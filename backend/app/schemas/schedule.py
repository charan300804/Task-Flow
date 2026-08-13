from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.enums import JobType

class ScheduleCreate(BaseModel):
    job_type: JobType = JobType.GENERIC
    cron_expression: str  # e.g., "0 */6 * * *"
    payload: Dict[str, Any] = {}
    priority: int = 5
    enabled: bool = True

class ScheduleUpdate(BaseModel):
    cron_expression: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None

class ScheduleResponse(BaseModel):
    id: UUID
    user_id: UUID
    job_type: JobType
    cron_expression: str
    payload: Dict[str, Any]
    priority: int
    enabled: bool
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
