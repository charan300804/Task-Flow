from typing import Dict, Any, List
from pydantic import BaseModel

class StatusCount(BaseModel):
    status: str
    count: int

class OverviewMetrics(BaseModel):
    total_jobs: int
    pending_jobs: int
    queued_jobs: int
    running_jobs: int
    success_jobs: int
    failed_jobs: int
    retrying_jobs: int
    dead_letter_jobs: int
    active_workers: int
    unhealthy_workers: int
    avg_execution_time_ms: float
    success_rate_percent: float

class JobTypeDistribution(BaseModel):
    job_type: str
    count: int

class MetricTimePoint(BaseModel):
    timestamp: str
    completed: int
    failed: int

class SystemMetricsResponse(BaseModel):
    overview: OverviewMetrics
    status_distribution: List[StatusCount]
    job_type_distribution: List[JobTypeDistribution]
    throughput_history: List[MetricTimePoint]
