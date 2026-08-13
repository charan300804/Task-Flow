import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Index, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import JobStatus, JobType

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(SQLEnum(JobType, name="job_type_enum"), nullable=False, default=JobType.GENERIC)
    payload = Column(JSON, nullable=False, default=dict)
    priority = Column(Integer, nullable=False, default=5, index=True)
    status = Column(SQLEnum(JobStatus, name="job_status_enum"), nullable=False, default=JobStatus.PENDING, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    timeout_seconds = Column(Integer, nullable=False, default=300)
    max_retries = Column(Integer, nullable=False, default=3)
    retry_count = Column(Integer, nullable=False, default=0)
    result_location = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)
    idempotency_key = Column(String(255), unique=True, nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="jobs")
    attempts = relationship("JobAttempt", back_populates="job", cascade="all, delete-orphan", order_by="JobAttempt.attempt_number")

    __table_args__ = (
        Index("idx_jobs_status_priority", "status", "priority"),
        Index("idx_jobs_status_scheduled", "status", "scheduled_at"),
    )
