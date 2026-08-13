import json
import logging
import time
from typing import Optional, Dict, Any, List, Tuple
from redis.asyncio import Redis
import redis as sync_redis

logger = logging.getLogger(__name__)

# Redis Queue Keys
QUEUE_CRITICAL = "taskflow:queue:critical"   # priority 9-10
QUEUE_HIGH = "taskflow:queue:high"           # priority 7-8
QUEUE_DEFAULT = "taskflow:queue:default"     # priority 4-6
QUEUE_LOW = "taskflow:queue:low"             # priority 1-3
QUEUE_ML = "taskflow:queue:ml"               # ML Prediction tasks
QUEUE_DELAYED = "taskflow:queue:delayed"     # Sorted set score = timestamp

ALL_QUEUES = [QUEUE_CRITICAL, QUEUE_HIGH, QUEUE_DEFAULT, QUEUE_LOW, QUEUE_ML]

class QueueService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def _get_queue_key(self, priority: int, job_type: str) -> str:
        if job_type == "ML_PREDICTION":
            return QUEUE_ML
        if priority >= 9:
            return QUEUE_CRITICAL
        elif priority >= 7:
            return QUEUE_HIGH
        elif priority >= 4:
            return QUEUE_DEFAULT
        else:
            return QUEUE_LOW

    async def enqueue_job(self, job_id: str, priority: int, job_type: str, payload: Dict[str, Any] = None) -> bool:
        """Push a job into the appropriate Redis queue."""
        queue_key = self._get_queue_key(priority, job_type)
        job_data = {
            "id": str(job_id),
            "priority": priority,
            "job_type": job_type,
            "enqueued_at": time.time()
        }
        await self.redis.lpush(queue_key, json.dumps(job_data))
        logger.info(f"Enqueued job {job_id} into {queue_key} with priority {priority}")
        return True

    async def enqueue_delayed_job(self, job_id: str, priority: int, job_type: str, execute_at_timestamp: float) -> bool:
        """Add job to delayed sorted set for retry or scheduled execution."""
        job_data = {
            "id": str(job_id),
            "priority": priority,
            "job_type": job_type,
        }
        await self.redis.zadd(QUEUE_DELAYED, {json.dumps(job_data): execute_at_timestamp})
        logger.info(f"Enqueued delayed job {job_id} for execution at {execute_at_timestamp}")
        return True

    async def process_delayed_jobs(self) -> int:
        """Move ready delayed jobs into their respective active queues."""
        now = time.time()
        # Retrieve jobs with score <= now
        ready_jobs = await self.redis.zrangebyscore(QUEUE_DELAYED, min=0, max=now)
        processed_count = 0
        for raw_job in ready_jobs:
            # Remove from delayed set atomically
            removed = await self.redis.zrem(QUEUE_DELAYED, raw_job)
            if removed:
                job_data = json.loads(raw_job)
                await self.enqueue_job(
                    job_id=job_data["id"],
                    priority=job_data["priority"],
                    job_type=job_data["job_type"]
                )
                processed_count += 1
        return processed_count

    async def get_queue_lengths(self) -> Dict[str, int]:
        """Return the count of jobs in each queue."""
        lengths = {}
        for q in ALL_QUEUES:
            lengths[q.split(":")[-1]] = await self.redis.llen(q)
        lengths["delayed"] = await self.redis.zcard(QUEUE_DELAYED)
        return lengths


class SyncQueueService:
    """Sync version for Worker process daemon."""
    def __init__(self, redis_client: sync_redis.Redis):
        self.redis = redis_client

    def _get_queues_for_worker(self, capabilities: List[str]) -> List[str]:
        """Order queues based on worker capabilities and priority."""
        queues = []
        if "ML_PREDICTION" in capabilities or "ALL" in capabilities:
            queues.append(QUEUE_ML)
        queues.extend([QUEUE_CRITICAL, QUEUE_HIGH, QUEUE_DEFAULT, QUEUE_LOW])
        return queues

    def dequeue_job(self, worker_id: str, capabilities: List[str], timeout: int = 2) -> Optional[Dict[str, Any]]:
        """
        Poll queues in order of priority.
        Uses RPOPLPUSH to atomically move job to worker's processing set.
        """
        target_queues = self._get_queues_for_worker(capabilities)
        processing_key = f"taskflow:processing:{worker_id}"

        for queue_key in target_queues:
            raw_job = self.redis.rpoplpush(queue_key, processing_key)
            if raw_job:
                try:
                    job_data = json.loads(raw_job)
                    job_data["_raw"] = raw_job
                    job_data["_source_queue"] = queue_key
                    return job_data
                except Exception as e:
                    logger.error(f"Failed to parse job data from {queue_key}: {e}")
                    self.redis.lrem(processing_key, 1, raw_job)
                    return None
        return None

    def ack_job(self, worker_id: str, raw_job: str) -> None:
        """Remove job from worker processing set upon successful execution."""
        processing_key = f"taskflow:processing:{worker_id}"
        self.redis.lrem(processing_key, 1, raw_job)

    def nack_job(self, worker_id: str, raw_job: str) -> None:
        """Remove job from worker processing set on failure/cancellation."""
        processing_key = f"taskflow:processing:{worker_id}"
        self.redis.lrem(processing_key, 1, raw_job)
