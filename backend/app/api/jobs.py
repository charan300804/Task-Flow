import math
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.redis import get_redis
from app.services.queue_service import QueueService
from app.models import Job, JobAttempt, User, JobStatus, JobType
from app.schemas.job import JobCreate, JobResponse, JobDetailResponse, JobListResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def submit_job(
    job_in: JobCreate,
    idempotency_key_header: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    Asynchronously submit a job to TaskFlow.
    1. Validates authentication & payload.
    2. Enforces Idempotency (if key provided).
    3. Persists metadata in PostgreSQL.
    4. Pushes job to Redis Priority Queue.
    5. Immediately returns job object without blocking execution.
    """
    effective_idempotency_key = job_in.idempotency_key or idempotency_key_header

    # Check Idempotency Key
    if effective_idempotency_key:
        stmt = select(Job).where(Job.idempotency_key == effective_idempotency_key)
        res = await db.execute(stmt)
        existing_job = res.scalar_one_or_none()
        if existing_job:
            return existing_job

    now = datetime.now(timezone.utc)
    job = Job(
        user_id=current_user.id,
        job_type=job_in.job_type,
        payload=job_in.payload,
        priority=job_in.priority,
        status=JobStatus.PENDING,
        scheduled_at=job_in.scheduled_at,
        created_at=now,
        max_retries=job_in.max_retries,
        timeout_seconds=job_in.timeout_seconds,
        idempotency_key=effective_idempotency_key
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Push to Redis Queue if immediate
    queue_service = QueueService(redis)
    if job_in.scheduled_at and job_in.scheduled_at > now:
        # Schedule in delayed zset
        await queue_service.enqueue_delayed_job(
            job_id=str(job.id),
            priority=job.priority,
            job_type=job.job_type.value,
            execute_at_timestamp=job_in.scheduled_at.timestamp()
        )
    else:
        # Enqueue in priority queue
        await queue_service.enqueue_job(
            job_id=str(job.id),
            priority=job.priority,
            job_type=job.job_type.value
        )
        job.status = JobStatus.QUEUED
        await db.commit()
        await db.refresh(job)

    return job

@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: Optional[JobStatus] = Query(None),
    job_type: Optional[JobType] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve paginated list of submitted jobs with optional status/type filter."""
    query = select(Job)
    if status:
        query = query.where(Job.status == status)
    if job_type:
        query = query.where(Job.job_type == job_type)

    # Count total
    count_stmt = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()

    # Paginate results
    offset = (page - 1) * size
    query = query.order_by(desc(Job.created_at)).offset(offset).limit(size)
    res = await db.execute(query)
    items = res.scalars().all()

    pages = math.ceil(total / size) if total > 0 else 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job_detail(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get full job detail including all attempt history."""
    stmt = select(Job).options(selectinload(Job.attempts)).where(Job.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """Cancel a pending or queued job."""
    stmt = select(Job).where(Job.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in [JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job in '{job.status.value}' state.")

    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(job)
    return job

@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """Manually retry a failed or dead-lettered job."""
    stmt = select(Job).where(Job.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus.QUEUED
    job.error_message = None
    job.retry_count = 0  # Reset retry counter for manual retry

    queue_service = QueueService(redis)
    await queue_service.enqueue_job(
        job_id=str(job.id),
        priority=job.priority,
        job_type=job.job_type.value
    )

    await db.commit()
    await db.refresh(job)
    return job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete job and associated attempt records."""
    stmt = select(Job).where(Job.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await db.delete(job)
    await db.commit()
