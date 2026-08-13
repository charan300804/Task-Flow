from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import JobStatus, JobType

class JobCreate(BaseModel):
    job_type: JobType = JobType.GENERIC
    priority: int = Field(default=5, ge=1, le=10, description="Priority from 1 (lowest) to 10 (highest)")
    payload: Dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=300, ge=5, le=3600)
    scheduled_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None

class JobAttemptResponse(BaseModel):
    id: Union[UUID, str]
    worker_id: Optional[str] = None
    attempt_number: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: JobStatus
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class JobResponse(BaseModel):
    id: Union[UUID, str]
    user_id: Union[UUID, str]
    job_type: JobType
    payload: Dict[str, Any]
    priority: int
    status: JobStatus
    scheduled_at: Optional[datetime] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: int
    max_retries: int
    retry_count: int
    result_location: Optional[str] = None
    error_message: Optional[str] = None
    idempotency_key: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class JobDetailResponse(JobResponse):
    attempts: List[JobAttemptResponse] = []

class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
    page: int
    size: int
    pages: int
