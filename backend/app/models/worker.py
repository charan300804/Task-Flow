from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import WorkerStatus

class Worker(Base):
    __tablename__ = "workers"

    id = Column(String(100), primary_key=True)
    hostname = Column(String(255), nullable=False)
    status = Column(SQLEnum(WorkerStatus, name="worker_status_enum"), nullable=False, default=WorkerStatus.STARTING)
    capabilities = Column(JSON, nullable=False, default=list)
    current_job_id = Column(String(36), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    jobs_completed = Column(Integer, nullable=False, default=0)
    jobs_failed = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    attempts = relationship("JobAttempt", back_populates="worker")
