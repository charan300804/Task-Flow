# TaskFlow Architecture Specification

## Overview

TaskFlow is a production-grade distributed job processing platform designed to handle asynchronous workloads, machine learning inference jobs, priority queuing, and distributed lock coordination.

```
                         ┌──────────────────────┐
                         │   React Dashboard    │
                         │ (TypeScript + Vite)  │
                         └──────────┬───────────┘
                                    │ HTTP / REST
                                    ▼
                         ┌──────────────────────┐
                         │   FastAPI Gateway    │
                         │ (Asynchronous REST)  │
                         └──────────┬───────────┘
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
┌──────────────┐             ┌──────────────┐             ┌──────────────┐
│ PostgreSQL 16│             │   Redis 7    │             │   MinIO S3   │
│ Metadata DB  │             │ Priority Q & │             │ Artifact Store│
│              │             │ Locks & State│             │ (ML Results) │
└──────▲───────┘             └──────▲───────┘             └──────▲───────┘
       │                            │                            │
       └────────────────────────────┼────────────────────────────┘
                                    │
                         ┌──────────┴───────────┐
                         │ Scheduler & Monitor  │
                         │ Daemon (Heartbeats)  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Distributed Workers  │
                         │ [Worker 1, 2, 3, ...]│
                         └──────────────────────┘
```

## System Components

### 1. API Gateway (FastAPI)
- Exposes authenticated REST endpoints for job submission, query, cancellation, schedule configuration, worker health, and system analytics.
- Validates request payloads and client idempotency keys.
- Enqueues valid jobs directly into Redis Priority Queues without blocking execution.

### 2. Distributed Queues (Redis)
- Structured into multiple logical queues:
  - `taskflow:queue:critical` (priority 9-10)
  - `taskflow:queue:high` (priority 7-8)
  - `taskflow:queue:default` (priority 4-6)
  - `taskflow:queue:low` (priority 1-3)
  - `taskflow:queue:ml` (job_type = ML_PREDICTION)
  - `taskflow:queue:delayed` (ZSET sorted set for retries and scheduled tasks)

### 3. Worker Daemon Service
- Autonomous background worker daemons.
- Registers capabilities and publishes heartbeats every 5 seconds.
- Dequeues tasks atomically using Redis `RPOPLPUSH` into worker processing set `taskflow:processing:{worker_id}`.
- Acquires Redis distributed lock (`SET key token NX PX ttl`).
- Executes tasks, stores large artifacts in MinIO object storage, updates PostgreSQL metadata, and acknowledges completion (`RREM`).

### 4. Scheduler & Health Monitor
- Evaluates due cron schedules using `croniter` and dispatches new jobs.
- Monitors worker heartbeats; marks nodes inactive if last heartbeat > 15 seconds.
- Automatically recovers orphan jobs running on crashed workers, incrementing retry count or routing to Dead Letter Queue (DLQ).
