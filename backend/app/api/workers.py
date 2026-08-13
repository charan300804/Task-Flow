from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models import Worker, User
from app.schemas.worker import WorkerResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/workers", tags=["Workers"])

@router.get("", response_model=List[WorkerResponse])
async def list_workers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all registered worker nodes and their real-time health metrics."""
    stmt = select(Worker).order_by(desc(Worker.last_heartbeat))
    res = await db.execute(stmt)
    workers = res.scalars().all()
    return workers

@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker(
    worker_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get single worker node detail."""
    stmt = select(Worker).where(Worker.id == worker_id)
    res = await db.execute(stmt)
    worker = res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker node not found")
    return worker
