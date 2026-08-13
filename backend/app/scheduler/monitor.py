import os
import sys
import time
import asyncio
import logging
try:
    from croniter import croniter
    HAS_CRONITER = True
except ImportError:
    HAS_CRONITER = False
    croniter = None

# Add root directory to python path if executing directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.redis import get_async_redis_client
from app.services.queue_service import QueueService
from app.models import Worker, Job, Schedule, WorkerStatus, JobStatus, JobType
from sqlalchemy import select, update, or_

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SchedulerMonitor] %(message)s"
)
logger = logging.getLogger("TaskFlowMonitor")

class SchedulerMonitor:
    def __init__(self):
        self.running = True

    async def check_scheduled_cron_jobs(self):
        """Identify due cron schedules and create job submissions."""
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            # Find active schedules due for execution
            stmt = select(Schedule).where(
                Schedule.enabled == True,
                or_(Schedule.next_run_at == None, Schedule.next_run_at <= now)
            )
            result = await db.execute(stmt)
            schedules = result.scalars().all()

            redis_client = get_async_redis_client()
            queue_service = QueueService(redis_client)

            for sched in schedules:
                try:
                    # Create new scheduled Job
                    new_job = Job(
                        user_id=sched.user_id,
                        job_type=sched.job_type,
                        priority=sched.priority,
                        payload=sched.payload,
                        status=JobStatus.PENDING,
                        scheduled_at=now
                    )
                    db.add(new_job)
                    await db.flush()

                    # Calculate next execution time using croniter
                    cron = croniter(sched.cron_expression, now)
                    next_run = cron.get_next(datetime)
                    sched.next_run_at = next_run
                    sched.last_run_at = now

                    # Enqueue in Redis
                    await queue_service.enqueue_job(
                        job_id=str(new_job.id),
                        priority=new_job.priority,
                        job_type=new_job.job_type.value
                    )
                    new_job.status = JobStatus.QUEUED

                    logger.info(f"Cron Schedule {sched.id} triggered job {new_job.id}. Next run at {next_run.isoformat()}")

                except Exception as e:
                    logger.error(f"Error executing schedule {sched.id}: {e}")

            await db.commit()
            await redis_client.aclose()

    async def process_delayed_queue(self):
        """Move ready delayed/retrying jobs into active Redis queues."""
        redis_client = get_async_redis_client()
        queue_service = QueueService(redis_client)
        try:
            count = await queue_service.process_delayed_jobs()
            if count > 0:
                logger.info(f"Moved {count} delayed/retrying jobs into active queues.")
        except Exception as e:
            logger.error(f"Error processing delayed queue: {e}")
        finally:
            await redis_client.aclose()

    async def detect_unhealthy_workers(self):
        """Identify worker heartbeat timeouts and recover orphan running jobs."""
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            stale_threshold = now - timedelta(seconds=settings.WORKER_UNHEALTHY_THRESHOLD_SECONDS)

            # 1. Find workers with heartbeat older than threshold
            stmt = select(Worker).where(
                Worker.status.in_([WorkerStatus.IDLE, WorkerStatus.BUSY]),
                Worker.last_heartbeat < stale_threshold
            )
            result = await db.execute(stmt)
            unhealthy_workers = result.scalars().all()

            if not unhealthy_workers:
                return

            redis_client = get_async_redis_client()
            queue_service = QueueService(redis_client)

            for w in unhealthy_workers:
                logger.warning(f"Worker {w.id} failed heartbeat check (Last seen: {w.last_heartbeat}). Marking UNHEALTHY.")
                w.status = WorkerStatus.UNHEALTHY

                # Check if worker was processing a job
                if w.current_job_id:
                    orphan_stmt = select(Job).where(Job.id == w.current_job_id)
                    job_res = await db.execute(orphan_stmt)
                    job = job_res.scalar_one_or_none()

                    if job and job.status == JobStatus.RUNNING:
                        logger.warning(f"Recovering orphan job {job.id} from failed worker {w.id}...")
                        job.error_message = f"Worker {w.id} failed heartbeat and became UNHEALTHY while processing."

                        if job.retry_count < job.max_retries:
                            job.status = JobStatus.QUEUED
                            job.retry_count += 1
                            # Re-enqueue in Redis
                            await queue_service.enqueue_job(
                                job_id=str(job.id),
                                priority=job.priority,
                                job_type=job.job_type.value
                            )
                            logger.info(f"Re-enqueued orphan job {job.id} for retry #{job.retry_count}.")
                        else:
                            job.status = JobStatus.DEAD_LETTER
                            logger.error(f"Orphan job {job.id} retries exhausted. Moved to DEAD_LETTER.")

                    w.current_job_id = None

            await db.commit()
            await redis_client.aclose()

    async def start(self):
        """Run monitor loop continuously."""
        logger.info("Scheduler & Worker Health Monitor started.")
        while self.running:
            try:
                await self.check_scheduled_cron_jobs()
                await self.process_delayed_queue()
                await self.detect_unhealthy_workers()
            except Exception as e:
                logger.error(f"Error in monitor main loop: {e}")
            
            await asyncio.sleep(3)

if __name__ == "__main__":
    monitor = SchedulerMonitor()
    try:
        asyncio.run(monitor.start())
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user.")
