# TaskFlow Database Design & Index Rationale

TaskFlow relies on PostgreSQL 16 for durable metadata management.

## Database Schema

```
┌───────────────────┐       1:N       ┌───────────────────┐
│       users       ├─────────────────►       jobs        │
└───────────────────┘                 └─────────┬─────────┘
                                                │
                                                │ 1:N
                                                ▼
┌───────────────────┐       1:N       ┌───────────────────┐
│      workers      ├─────────────────►   job_attempts    │
└───────────────────┘                 └───────────────────┘
```

## Index Design & Rationale

1. `jobs.status`:
   - High cardinality query filtering for dashboard lists, dead-letter queries, and worker orphan recovery.
2. `jobs.created_at`:
   - Ordered pagination (`ORDER BY created_at DESC`).
3. `jobs.user_id`:
   - Fast lookup for user-specific job listings.
4. `jobs.priority`:
   - Priority-based job selection queries.
5. `jobs.scheduled_at`:
   - Efficient lookup for due scheduled jobs (`WHERE scheduled_at <= NOW()`).
6. `jobs.idempotency_key` (UNIQUE):
   - Fast $O(1)$ duplicate submission prevention.
7. `workers.last_heartbeat`:
   - Rapid identification of stale worker nodes (`WHERE last_heartbeat < NOW() - 15s`).
8. `job_attempts.job_id`:
   - Join indexing between jobs and attempt history logs.
