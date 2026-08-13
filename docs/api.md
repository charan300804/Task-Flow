# TaskFlow API Documentation

## Authentication Endpoints

### `POST /auth/register`
Register a new user.
```json
{
  "email": "user@taskflow.io",
  "name": "User Name",
  "password": "Password123!",
  "role": "USER"
}
```

### `POST /auth/login`
Authenticate user and obtain JWT access token. Form-encoded body with `username` and `password`.

### `GET /auth/me`
Returns current user profile. Requires Bearer Token.

---

## Job Management Endpoints

### `POST /api/jobs`
Asynchronously submit a job to TaskFlow.

**Headers:**
- `Authorization: Bearer <token>`
- `Idempotency-Key: <unique-string>` (Optional)

**Payload:**
```json
{
  "job_type": "ML_PREDICTION",
  "priority": 8,
  "payload": {
    "dataset_size": 1200,
    "num_trees": 50
  },
  "max_retries": 3,
  "timeout_seconds": 120
}
```

### `GET /api/jobs`
List submitted jobs with pagination and status filters.
`GET /api/jobs?page=1&size=20&status=SUCCESS&job_type=ML_PREDICTION`

### `GET /api/jobs/{id}`
Get detailed metadata and execution attempt history for a specific job.

### `POST /api/jobs/{id}/cancel`
Cancel a pending or queued job.

### `POST /api/jobs/{id}/retry`
Re-enqueue a failed or cancelled job.

### `GET /api/jobs/{id}/result`
Retrieve job execution result JSON or presigned MinIO S3 download URL.

---

## Worker Endpoints

### `GET /api/workers`
List all registered worker nodes, heartbeats, status, capabilities, and job counts.

---

## Schedule Endpoints

### `POST /api/schedules`
Create a recurring cron schedule.
```json
{
  "job_type": "ML_PREDICTION",
  "cron_expression": "0 */6 * * *",
  "payload": { "batch": true },
  "priority": 7
}
```

---

## Admin Endpoints

### `GET /api/admin/dead-letter`
List quarantined dead-lettered jobs.

### `POST /api/admin/dead-letter/{id}/retry`
Admin re-enqueue of dead-letter job.

### `DELETE /api/admin/dead-letter/{id}`
Permanently purge dead-letter job.
