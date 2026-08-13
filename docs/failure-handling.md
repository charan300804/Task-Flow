# TaskFlow Fault Tolerance & Failure Recovery Specification

TaskFlow is engineered with zero-data-loss design principles for distributed background processing.

## 1. Worker Crash Recovery

When a worker node crashes mid-execution:
1. The heartbeat loop terminates, causing `last_heartbeat` in Redis and PostgreSQL to stop updating.
2. The Scheduler Monitor background daemon evaluates worker heartbeats every 3 seconds.
3. If `last_heartbeat` is older than 15 seconds:
   - Worker state is updated to `UNHEALTHY`.
   - The monitor inspects `current_job_id` and any jobs stranded in `RUNNING` status on that worker.
   - If `retry_count < max_retries`:
     - Job status is set to `QUEUED`, `retry_count` is incremented, and job is pushed back into Redis active queues.
   - If retries exhausted:
     - Job status is set to `DEAD_LETTER`.

## 2. Exponential Backoff Retries

When a job task throws an unhandled exception:
1. Worker catches exception, records error message in `job_attempts` table.
2. If `retry_count < max_retries`:
   - Calculates backoff delay:
     $$\text{delay} = \text{base\_delay} \times 2^{(\text{attempt} - 1)}$$
   - Adds job payload to Redis Sorted Set `taskflow:queue:delayed` with score equal to execution timestamp.
   - Scheduler monitor checks `taskflow:queue:delayed` every second and pushes ready tasks back to priority queues.
3. If retries exhausted:
   - Job transitions to `DEAD_LETTER`.

## 3. Idempotent Processing

Clients supply an optional `Idempotency-Key` HTTP header:
- If a client retries a request due to network timeout, the API checks PostgreSQL/Redis for existing key.
- If existing job is found, original job metadata is returned without creating duplicate tasks or queuing duplicate side-effects.
