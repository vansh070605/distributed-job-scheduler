# System Architecture Guide

This document describes the high-level architecture, event flows, and database interactions of the Distributed Job Scheduler.

## System Topology

```mermaid
graph TD
    Client[React SPA Dashboard] -->|REST APIs| FastAPI[FastAPI REST Server]
    FastAPI -->|Write/Read| Postgres[(PostgreSQL DB)]
    FastAPI -->|Enqueue Event| Redis[(Redis Broker & Lock Manager)]
    
    subgraph Scheduler Engine
        CeleryBeat[Celery Beat Scheduler] -->|Poll Due Jobs| Postgres
        CeleryBeat -->|Trigger Event| Redis
    end
    
    subgraph Execution Pool
        Worker1[Celery Worker 1] -->|SELECT FOR UPDATE SKIP LOCKED| Postgres
        Worker2[Celery Worker 2] -->|SELECT FOR UPDATE SKIP LOCKED| Postgres
        Worker1 -->|Register Heartbeat| Redis
        Worker2 -->|Register Heartbeat| Redis
    end
```

## Core Components

### 1. Stateless API Layer (FastAPI)
- Handles authentication and security enforcement.
- Performs REST API inputs validation via Pydantic schemas.
- Coordinates database operations via the Repository pattern.
- Issues trigger signals to Redis to kick off execution runs on the worker pool.

### 2. Scheduler Engine (Celery Beat)
- Orchestrates cron scheduling, delays, and recurring trigger loops.
- Scans Postgres database table records periodically to find jobs whose `next_run_at <= NOW()`.
- Transitions jobs from `scheduled` to `queued` state and enqueues event payloads in Redis.
- Monitors active nodes and reaps dead/offline worker processes.

### 3. Worker Execution Pool (Celery Workers)
- Thread-safe pool of worker processes.
- Atomically selects next available job from assigned queues using row-level locks.
- Validates job execution rules (e.g. idempotency keys).
- Logs execution logs and updates status columns in PostgreSQL.

---

## Event Sequences

```mermaid
sequenceDiagram
    participant User
    participant API as FastAPI Server
    participant DB as PostgreSQL DB
    participant Redis as Redis Broker
    participant Beat as Celery Beat
    participant Worker as Celery Worker

    User->>API: POST /api/v1/projects/{id}/jobs
    API->>DB: Check Idempotency Key
    alt If not already executed
        API->>DB: Insert Job (status='queued')
        API->>Redis: Trigger Queue Event
    end
    API-->>User: Return Job ID

    loop Every 5 Seconds
        Beat->>DB: Poll due jobs (next_run_at <= NOW)
        DB-->>Beat: Due Jobs list
        Beat->>DB: Update Jobs status='queued'
        Beat->>Redis: Enqueue Trigger Event
    end

    Worker->>Redis: Pop Trigger Event
    Worker->>DB: Claim Job (SELECT FOR UPDATE SKIP LOCKED)
    DB-->>Worker: Lock job & return details
    Worker->>DB: Create JobExecution (status='running')
    Worker->>Worker: Process payload execution
    Worker->>DB: Update Job status='completed'
    Worker->>DB: Update JobExecution status='completed' & write logs
```
