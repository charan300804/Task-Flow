from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.enums import WorkerStatus

class WorkerResponse(BaseModel):
    id: str
    hostname: str
    status: WorkerStatus
    capabilities: List[str]
    current_job_id: Optional[UUID] = None
    last_heartbeat: datetime
    jobs_completed: int
    jobs_failed: int
    started_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WorkerHeartbeat(BaseModel):
    worker_id: str
    status: WorkerStatus
    current_job_id: Optional[UUID] = None
