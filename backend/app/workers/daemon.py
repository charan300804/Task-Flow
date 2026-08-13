import os
import sys
import time
import json
import socket
import signal
import uuid
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Add root directory to python path if executing directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.config import settings
from app.core.database import SyncSessionLocal
from app.core.redis import get_sync_redis_client
from app.core.storage import storage_client
from app.services.queue_service import SyncQueueService
from app.services.lock_service import DistributedLock
from app.models import Worker, Job, JobAttempt, WorkerStatus, JobStatus, JobType
from app.tasks.ml_prediction import execute_ml_prediction_task
from app.tasks.generic import (
    execute_sleep_task,
    execute_cpu_prime_task,
    execute_matrix_computation_task,
    execute_data_processing_task,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("TaskFlowWorker")

class WorkerDaemon:
    def __init__(self, worker_id: Optional[str] = None, capabilities: Optional[List[str]] = None):
        self.hostname = socket.gethostname()
        self.worker_id = worker_id or os.getenv("WORKER_ID", f"worker-{self.hostname}-{uuid.uuid4().hex[:6]}")
        
        # Capabilities matching
        cap_env = os.getenv("WORKER_CAPABILITIES", "GENERIC,PYTHON_TASK,ML_PREDICTION,DATA_PROCESSING")
        self.capabilities = capabilities or [c.strip() for c in cap_env.split(",")]
        
        self.redis_client = get_sync_redis_client()
        self.queue_service = SyncQueueService(self.redis_client)
        
        self.running = True
        self.current_job_id = None
        self.heartbeat_thread = None
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        logger.info(f"Worker {self.worker_id} received shutdown signal ({signum}). Cleaning up...")
        self.running = False

    def register(self):
        """Register worker in PostgreSQL database."""
        db = SyncSessionLocal()
        try:
            worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
            now = datetime.now(timezone.utc)
            if not worker:
                worker = Worker(
                    id=self.worker_id,
                    hostname=self.hostname,
                    status=WorkerStatus.IDLE,
                    capabilities=self.capabilities,
                    last_heartbeat=now,
                    started_at=now,
                    jobs_completed=0,
                    jobs_failed=0
                )
                db.add(worker)
            else:
                worker.hostname = self.hostname
                worker.status = WorkerStatus.IDLE
                worker.capabilities = self.capabilities
                worker.last_heartbeat = now
                worker.current_job_id = None
            db.commit()
            logger.info(f"Worker {self.worker_id} registered successfully with capabilities: {self.capabilities}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to register worker in DB: {e}")
        finally:
            db.close()

    def _start_heartbeat_loop(self):
        """Periodically update worker heartbeat in Redis & Postgres."""
        while self.running:
            try:
                now = datetime.now(timezone.utc)
                # 1. Update Redis state
                redis_data = {
                    "id": self.worker_id,
                    "hostname": self.hostname,
                    "status": WorkerStatus.BUSY.value if self.current_job_id else WorkerStatus.IDLE.value,
                    "last_heartbeat": now.isoformat(),
                    "current_job_id": str(self.current_job_id) if self.current_job_id else ""
                }
                self.redis_client.hset(f"taskflow:worker:{self.worker_id}", mapping=redis_data)
                
                # 2. Update Postgres database
                db = SyncSessionLocal()
                try:
                    worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
                    if worker:
                        worker.last_heartbeat = now
                        worker.status = WorkerStatus.BUSY if self.current_job_id else WorkerStatus.IDLE
                        worker.current_job_id = self.current_job_id
                        db.commit()
                except Exception as ex:
                    db.rollback()
                    logger.warning(f"Heartbeat DB update warning: {ex}")
                finally:
                    db.close()

            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")

            time.sleep(settings.WORKER_HEARTBEAT_INTERVAL_SECONDS)

    def execute_job_task(self, job_type: str, payload: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        """Dispatch task based on job_type."""
        if job_type == JobType.ML_PREDICTION.value or job_type == "ML_PREDICTION":
            return execute_ml_prediction_task(job_id, payload)
        elif job_type == JobType.DATA_PROCESSING.value or job_type == "DATA_PROCESSING":
            return execute_data_processing_task(payload)
        elif job_type == "CPU_PRIME":
            return execute_cpu_prime_task(payload)
        elif job_type == "MATRIX":
            return execute_matrix_computation_task(payload)
        else:
            # Generic / Sleep fallback
            return execute_sleep_task(payload)

    def process_job(self, job_data: Dict[str, Any]):
        job_id_str = job_data.get("id")
        raw_job = job_data.get("_raw")
        if not job_id_str:
            return

        db = SyncSessionLocal()
        lock = DistributedLock(self.redis_client, name=job_id_str, timeout_seconds=settings.DEFAULT_JOB_TIMEOUT_SECONDS)

        try:
            # 1. Acquire distributed lock
            if not lock.acquire():
                logger.warning(f"Could not acquire lock for job {job_id_str}. Another worker may be processing it.")
                self.queue_service.nack_job(self.worker_id, raw_job)
                return

            # 2. Load job from DB
            job = db.query(Job).filter(Job.id == uuid.UUID(job_id_str)).first()
            if not job or job.status in [JobStatus.SUCCESS.value, JobStatus.CANCELLED.value]:
                logger.info(f"Job {job_id_str} is invalid or already finished/cancelled. Skipping.")
                self.queue_service.ack_job(self.worker_id, raw_job)
                lock.release()
                return

            # 3. Update job state to RUNNING
            now = datetime.now(timezone.utc)
            job.status = JobStatus.RUNNING
            job.started_at = now
            job.retry_count += 1
            current_attempt_number = job.retry_count

            # Create attempt record
            attempt = JobAttempt(
                job_id=job.id,
                worker_id=self.worker_id,
                attempt_number=current_attempt_number,
                started_at=now,
                status=JobStatus.RUNNING
            )
            db.add(attempt)

            # Update worker status
            self.current_job_id = job.id
            worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
            if worker:
                worker.status = WorkerStatus.BUSY
                worker.current_job_id = job.id
            db.commit()

            logger.info(f"Worker {self.worker_id} started job {job.id} (Type: {job.job_type.value}, Attempt {current_attempt_number}/{job.max_retries})")

            # 4. Execute actual task payload
            task_start_time = time.time()
            task_result = self.execute_job_task(job.job_type.value, job.payload or {}, str(job.id))
            execution_time_ms = int((time.time() - task_start_time) * 1000)

            # 5. Handle Successful Execution
            finished_now = datetime.now(timezone.utc)
            job.status = JobStatus.SUCCESS
            job.completed_at = finished_now

            # Result storage URL
            result_loc = task_result.get("result_location")
            if not result_loc:
                object_key = f"results/job_{job.id}.json"
                result_loc = storage_client.upload_json(object_key, task_result)
            job.result_location = result_loc

            attempt.status = JobStatus.SUCCESS
            attempt.completed_at = finished_now
            attempt.execution_time_ms = execution_time_ms

            if worker:
                worker.jobs_completed += 1

            db.commit()
            self.queue_service.ack_job(self.worker_id, raw_job)
            logger.info(f"Job {job.id} COMPLETED SUCCESSFULLY in {execution_time_ms} ms. Result: {result_loc}")

        except Exception as e:
            db.rollback()
            execution_time_ms = int((time.time() - task_start_time) * 1000) if 'task_start_time' in locals() else 0
            err_msg = str(e)
            logger.error(f"Job {job_id_str} FAILED: {err_msg}")

            try:
                job = db.query(Job).filter(Job.id == uuid.UUID(job_id_str)).first()
                worker = db.query(Worker).filter(Worker.id == self.worker_id).first()

                if job:
                    job.error_message = err_msg
                    if worker:
                        worker.jobs_failed += 1

                    # Check retry eligibility
                    if job.retry_count < job.max_retries:
                        # Exponential backoff: delay = base * 2^(attempt - 1)
                        delay = settings.RETRY_BASE_DELAY_SECONDS * (2 ** (job.retry_count - 1))
                        execute_at = time.time() + delay
                        job.status = JobStatus.RETRYING

                        # Schedule delayed retry in Redis sorted set
                        sync_qs = SyncQueueService(self.redis_client)
                        sync_qs.redis.zadd(
                            "taskflow:queue:delayed",
                            {json.dumps({"id": str(job.id), "priority": job.priority, "job_type": job.job_type.value}): execute_at}
                        )
                        logger.info(f"Job {job.id} scheduled for retry #{job.retry_count + 1} in {delay} seconds.")
                    else:
                        job.status = JobStatus.DEAD_LETTER
                        logger.warning(f"Job {job.id} exhausted max retries ({job.max_retries}). Moved to DEAD_LETTER queue.")

                    # Update attempt record
                    if 'attempt' in locals() and attempt:
                        attempt.status = JobStatus.FAILED
                        attempt.error_message = err_msg
                        attempt.completed_at = datetime.now(timezone.utc)
                        attempt.execution_time_ms = execution_time_ms

                    db.commit()

            except Exception as rollback_err:
                db.rollback()
                logger.error(f"Failed to record job failure in DB: {rollback_err}")

            self.queue_service.nack_job(self.worker_id, raw_job)

        finally:
            lock.release()
            self.current_job_id = None
            try:
                worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
                if worker:
                    worker.status = WorkerStatus.IDLE
                    worker.current_job_id = None
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()

    def start(self):
        """Start worker main loop."""
        self.register()
        
        # Start heartbeat background thread
        self.heartbeat_thread = threading.Thread(target=self._start_heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()

        logger.info(f"Worker {self.worker_id} daemon started. Waiting for jobs...")

        while self.running:
            try:
                job_data = self.queue_service.dequeue_job(
                    worker_id=self.worker_id,
                    capabilities=self.capabilities,
                    timeout=2
                )
                if job_data:
                    self.process_job(job_data)
                else:
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error in worker main loop: {e}")
                time.sleep(1)

        # Shutdown cleanup
        logger.info(f"Worker {self.worker_id} stopping...")
        db = SyncSessionLocal()
        try:
            worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
            if worker:
                worker.status = WorkerStatus.STOPPED
                worker.current_job_id = None
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
        logger.info(f"Worker {self.worker_id} stopped gracefully.")

if __name__ == "__main__":
    worker_id_arg = sys.argv[1] if len(sys.argv) > 1 else None
    daemon = WorkerDaemon(worker_id=worker_id_arg)
    daemon.start()
