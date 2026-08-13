# TaskFlow Scalability & Benchmarking Architecture

## 1. Horizontal Worker Scaling

TaskFlow is designed to be completely stateless at the API and worker layers.

```bash
docker compose up --scale worker-1=5 --scale worker-2=5
```

- **Stateless API Gateway**: FastAPI instances do not hold state. Request routing can be balanced via Nginx or AWS ALB.
- **Worker Auto-Scaling**: Worker daemons consume jobs directly from Redis queue primitives. Adding 50 workers requires no code changes or master-worker cluster re-configuration.

## 2. Bottlenecks & Optimization Strategies

1. **Redis Queue Operations**:
   - Uses native Redis $O(1)$ operations (`LPUSH`, `RPOPLPUSH`, `ZADD`, `ZRANGEBYSCORE`).
   - Handles tens of thousands of ops/sec per single Redis core.
2. **Database Pooling**:
   - Connection pools managed via AsyncPG and SQLAlchemy session factories.
3. **Large Result Decoupling**:
   - Large ML prediction arrays and outputs are stored directly in MinIO / S3 object storage rather than PostgreSQL text/JSON columns.
