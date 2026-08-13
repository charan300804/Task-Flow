import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import JobType

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(SQLEnum(JobType, name="schedule_job_type_enum"), nullable=False, default=JobType.GENERIC)
    cron_expression = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    priority = Column(String(20), nullable=False, default="5")
    enabled = Column(Boolean, nullable=False, default=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="schedules")
