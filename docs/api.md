# REST API Documentation (v1)

All API routes are versioned and prefixes start with `/api/v1`.

## Authentication

### 1. User Registration
`POST /api/v1/auth/register`
- **Request Body**:
```json
{
  "email": "user@scheduler.io",
  "password": "securepassword",
  "full_name": "Developer User",
  "role": "admin"
}
```
- **Response**: `200 OK`
```json
{
  "id": "uuid-string",
  "email": "user@scheduler.io",
  "full_name": "Developer User",
  "role": "admin",
  "is_active": true
}
```

### 2. User Login
`POST /api/v1/auth/login`
- **Request Body**: Form-encoded `username` and `password`
- **Response**: `200 OK`
```json
{
  "access_token": "jwt-token-string",
  "token_type": "bearer"
}
```

---

## Queues

### 1. Create Queue
`POST /api/v1/projects/{project_id}/queues`
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
```json
{
  "name": "data-sync",
  "priority": 2,
  "concurrency": 10,
  "is_paused": false,
  "rate_limit": null,
  "retry_policy_id": null
}
```

### 2. List Project Queues
`GET /api/v1/projects/{project_id}/queues`

---

## Jobs

### 1. Submit Job
`POST /api/v1/projects/{project_id}/jobs`
- **Request Body**:
```json
{
  "queue_id": "queue-uuid",
  "name": "sync-profile-task",
  "payload": {
    "duration": 5,
    "should_fail": false
  },
  "priority_override": 5,
  "max_retries": 3,
  "cron_expression": null,
  "delay_seconds": null,
  "idempotency_key": "unique-transaction-key-uuid"
}
```

### 2. List Jobs
`GET /api/v1/projects/{project_id}/jobs`
- **Query Parameters**:
  - `queue_id` (optional)
  - `status` (optional)
  - `search` (optional)
  - `skip` (default 0)
  - `limit` (default 100)

### 3. Read Job Logs
`GET /api/v1/projects/{project_id}/jobs/{job_id}/logs`

---

## Workers

### 1. Active Worker Diagnostics
`GET /api/v1/workers/`
- **Response**:
```json
[
  {
    "id": "worker-uuid",
    "hostname": "worker-host",
    "status": "active",
    "concurrency": 10,
    "last_heartbeat": "timestamp",
    "queue_assignments": [
      {
        "queue_id": "queue-uuid"
      }
    ]
  }
]
```
