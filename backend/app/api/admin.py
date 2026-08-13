from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.redis import get_redis
from app.services.queue_service import QueueService
from app.models import Job, JobStatus, User
from app.schemas.job import JobResponse, JobListResponse
from app.api.deps import get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["Admin & Dead-Letter Queue"])

@router.get("/dead-letter", response_model=JobListResponse)
async def list_dead_letter_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all jobs in DEAD_LETTER state for administrative inspection."""
    query = select(Job).where(Job.status == JobStatus.DEAD_LETTER).order_by(desc(Job.created_at))
    
    offset = (page - 1) * size
    res = await db.execute(query.offset(offset).limit(size))
    items = res.scalars().all()

    total_stmt = select(Job).where(Job.status == JobStatus.DEAD_LETTER)
    total_res = await db.execute(total_stmt)
    total = len(total_res.scalars().all())

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 1
    }

@router.post("/dead-letter/{job_id}/retry", response_model=JobResponse)
async def retry_dead_letter_job(
    job_id: UUID,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """Admin endpoint to requeue a dead-lettered job for execution."""
    stmt = select(Job).where(Job.id == job_id, Job.status == JobStatus.DEAD_LETTER)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Dead-letter job not found.")

    job.status = JobStatus.QUEUED
    job.error_message = None
    job.retry_count = 0  # Reset counter

    queue_service = QueueService(redis)
    await queue_service.enqueue_job(
        job_id=str(job.id),
        priority=job.priority,
        job_type=job.job_type.value
    )

    await db.commit()
    await db.refresh(job)
    return job

@router.delete("/dead-letter/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dead_letter_job(
    job_id: UUID,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Permanently delete a dead-letter job."""
    stmt = select(Job).where(Job.id == job_id, Job.status == JobStatus.DEAD_LETTER)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Dead-letter job not found.")

    await db.delete(job)
    await db.commit()
