export type JobStatus = 
  | 'PENDING' 
  | 'QUEUED' 
  | 'RUNNING' 
  | 'SUCCESS' 
  | 'FAILED' 
  | 'RETRYING' 
  | 'CANCELLED' 
  | 'DEAD_LETTER';

export type JobType = 
  | 'GENERIC' 
  | 'PYTHON_TASK' 
  | 'ML_PREDICTION' 
  | 'DATA_PROCESSING';

export type WorkerStatus = 
  | 'STARTING' 
  | 'IDLE' 
  | 'BUSY' 
  | 'UNHEALTHY' 
  | 'STOPPED';

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'ADMIN' | 'USER';
  created_at: string;
}

export interface JobAttempt {
  id: string;
  worker_id?: string;
  attempt_number: number;
  started_at: string;
  completed_at?: string;
  status: JobStatus;
  error_message?: string;
  execution_time_ms?: number;
}

export interface JobCreate {
  job_type: JobType;
  priority?: number;
  payload?: Record<string, any>;
  max_retries?: number;
  timeout_seconds?: number;
  scheduled_at?: string;
  idempotency_key?: string;
}

export interface Job {
  id: string;
  user_id: string;
  job_type: JobType;
  payload: Record<string, any>;
  priority: number;
  status: JobStatus;
  scheduled_at?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  timeout_seconds: number;
  max_retries: number;
  retry_count: number;
  result_location?: string;
  error_message?: string;
  idempotency_key?: string;
  attempts?: JobAttempt[];
}

export interface WorkerNode {
  id: string;
  hostname: string;
  status: WorkerStatus;
  capabilities: string[];
  current_job_id?: string;
  last_heartbeat: string;
  jobs_completed: number;
  jobs_failed: number;
  started_at: string;
}

export interface ScheduleCreate {
  job_type: JobType;
  cron_expression: string;
  payload?: Record<string, any>;
  priority?: number;
  enabled?: boolean;
}

export interface Schedule {
  id: string;
  user_id: string;
  job_type: JobType;
  cron_expression: string;
  payload: Record<string, any>;
  priority: number;
  enabled: boolean;
  next_run_at?: string;
  last_run_at?: string;
  created_at: string;
}

export interface OverviewMetrics {
  total_jobs: number;
  pending_jobs: number;
  queued_jobs: number;
  running_jobs: number;
  success_jobs: number;
  failed_jobs: number;
  retrying_jobs: number;
  dead_letter_jobs: number;
  active_workers: number;
  unhealthy_workers: number;
  avg_execution_time_ms: number;
  success_rate_percent: number;
}

export interface SystemMetricsResponse {
  overview: OverviewMetrics;
  status_distribution: { status: string; count: number }[];
  job_type_distribution: { job_type: string; count: number }[];
  throughput_history: { timestamp: string; completed: number; failed: number }[];
}
