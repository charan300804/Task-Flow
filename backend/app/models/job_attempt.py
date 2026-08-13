import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import JobStatus

class JobAttempt(Base):
    __tablename__ = "job_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    worker_id = Column(String(100), ForeignKey("workers.id", ondelete="SET NULL"), nullable=True, index=True)
    attempt_number = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(SQLEnum(JobStatus, name="job_attempt_status_enum"), nullable=False, default=JobStatus.RUNNING)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)

    # Relationships
    job = relationship("Job", back_populates="attempts")
    worker = relationship("Worker", back_populates="attempts")
