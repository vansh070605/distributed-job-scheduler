# Performance Tuning & Scaling Guidelines

This document details database index optimizations, connection pool tuning, and worker concurrency calibrations.

## 1. Database Index Optimizations

High-throughput queue execution creates heavy read-write loads on the database. The system utilizes specific composite indexes:

- **Fast Worker Polling**:
```sql
CREATE INDEX idx_jobs_claim ON jobs(status, queue_id, priority_override, created_at);
```
*Why*: The atomic claim query filters on `status` and `queue_id`, and then orders by `priority_override` and `created_at`. This index matches the scan path perfectly.

- **Fast Scheduler Polling**:
```sql
CREATE INDEX idx_jobs_next_run_at ON jobs(next_run_at) WHERE status = 'scheduled';
```
*Why*: The scheduler scans scheduled jobs due to execute. This partial index keeps index sizes small.

---

## 2. Connection Pool Tuning

When running 100+ Celery worker processes, database connection limits can be exceeded.
- **SQLAlchemy Configurations**:
  - `pool_size`: 20 connections per worker container.
  - `max_overflow`: 10 connections.
  - `pool_pre_ping`: True (discards dead connections immediately).
- **PgBouncer Integration**: In high-load clusters, route database queries through PgBouncer in transaction mode to pool hundreds of concurrent connections.

---

## 3. Worker Concurrency Calibrations

- **CPU-bound Tasks**: Configure celery worker concurrency to match total core count (`celery worker -c <CPU_COUNT>`).
- **I/O-bound Tasks (API calls, Web Scraping)**: Concurrency can be scaled up to 3x-4x core count. Ensure database connection pool sizing is adjusted accordingly.
