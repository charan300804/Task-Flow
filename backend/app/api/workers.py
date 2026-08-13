from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.redis import get_redis
from app.models import Worker, WorkerStatus, User
from app.schemas.worker import WorkerResponse, WorkerHeartbeat
from app.api.deps import get_current_user_optional

router = APIRouter(prefix="/api/workers", tags=["Workers"])

@router.get("", response_model=List[WorkerResponse])
async def list_workers(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """List all registered worker nodes and their status."""
    try:
        stmt = select(Worker).order_by(Worker.started_at.desc())
        res = await db.execute(stmt)
        return res.scalars().all()
    except Exception:
        return []

@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker_detail(
    worker_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Get details for a specific worker node."""
    stmt = select(Worker).where(Worker.id == worker_id)
    res = await db.execute(stmt)
    worker = res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker

@router.post("/heartbeat", status_code=status.HTTP_200_OK)
async def worker_heartbeat(
    heartbeat_in: WorkerHeartbeat,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint for worker daemon heartbeats.
    Updates worker's last_heartbeat timestamp and status.
    """
    now = datetime.now(timezone.utc)
    stmt = select(Worker).where(Worker.id == heartbeat_in.worker_id)
    res = await db.execute(stmt)
    worker = res.scalar_one_or_none()

    if not worker:
        # Register new worker
        worker = Worker(
            id=heartbeat_in.worker_id,
            hostname=heartbeat_in.hostname,
            status=heartbeat_in.status,
            capabilities=heartbeat_in.capabilities,
            current_job_id=heartbeat_in.current_job_id,
            last_heartbeat=now,
            jobs_completed=heartbeat_in.jobs_completed,
            jobs_failed=heartbeat_in.jobs_failed,
            started_at=now
        )
        db.add(worker)
    else:
        # Update existing worker
        worker.hostname = heartbeat_in.hostname
        worker.status = heartbeat_in.status
        worker.capabilities = heartbeat_in.capabilities
        worker.current_job_id = heartbeat_in.current_job_id
        worker.last_heartbeat = now
        worker.jobs_completed = heartbeat_in.jobs_completed
        worker.jobs_failed = heartbeat_in.jobs_failed

    await db.commit()
    return {"status": "ok", "timestamp": now}
