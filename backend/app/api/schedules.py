from typing import List
from uuid import UUID
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

try:
    from croniter import croniter
    HAS_CRONITER = True
except ImportError:
    HAS_CRONITER = False
    croniter = None

from app.core.database import get_db
from app.models import Schedule, User
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])

@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    sched_in: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    if HAS_CRONITER and croniter:
        if not croniter.is_valid(sched_in.cron_expression):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid cron expression '{sched_in.cron_expression}'."
            )
        cron = croniter(sched_in.cron_expression, now)
        next_run = cron.get_next(datetime)
    else:
        next_run = now + timedelta(hours=6)

    schedule = Schedule(
        user_id=current_user.id,
        job_type=sched_in.job_type,
        cron_expression=sched_in.cron_expression,
        payload=sched_in.payload,
        priority=sched_in.priority,
        enabled=sched_in.enabled,
        next_run_at=next_run
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule

@router.get("", response_model=List[ScheduleResponse])
async def list_schedules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all recurring job schedules."""
    stmt = select(Schedule).order_by(desc(Schedule.created_at))
    res = await db.execute(stmt)
    return res.scalars().all()

@router.patch("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: UUID,
    sched_update: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update schedule properties (cron, payload, enabled status)."""
    stmt = select(Schedule).where(Schedule.id == schedule_id)
    res = await db.execute(stmt)
    sched = res.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if sched_update.cron_expression is not None:
        if not croniter.is_valid(sched_update.cron_expression):
            raise HTTPException(status_code=400, detail="Invalid cron expression.")
        sched.cron_expression = sched_update.cron_expression
        cron = croniter(sched.cron_expression, datetime.now(timezone.utc))
        sched.next_run_at = cron.get_next(datetime)

    if sched_update.payload is not None:
        sched.payload = sched_update.payload
    if sched_update.priority is not None:
        sched.priority = sched_update.priority
    if sched_update.enabled is not None:
        sched.enabled = sched_update.enabled

    await db.commit()
    await db.refresh(sched)
    return sched

@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete schedule."""
    stmt = select(Schedule).where(Schedule.id == schedule_id)
    res = await db.execute(stmt)
    sched = res.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await db.delete(sched)
    await db.commit()
