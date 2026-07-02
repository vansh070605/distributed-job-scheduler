# System Design Decisions & Trade-offs

This document details the choices made during the development of the Distributed Job Scheduler and outlines the engineering rationale behind them.

## 1. Storage Choice: PostgreSQL vs NoSQL (MongoDB)

**Decision**: PostgreSQL
- **ACID Guarantees**: Job scheduling requires strong consistency to ensure that job status transitions are atomic and durable. A job must never be lost or executed twice because of loose transactional boundaries.
- **Row-level Locking (`FOR UPDATE SKIP LOCKED`)**: PostgreSQL provides native locking capabilities to claim jobs atomically without executing concurrent updates on identical records.
- **JSONB Column Serialization**: Jobs payloads and metadata are unstructured or dynamic. PostgreSQL `JSONB` columns allow schemas to evolve while maintaining SQL index capabilities.

---

## 2. Distributed Locking & Broker: Redis vs Kafka/ZooKeeper

**Decision**: Redis + Celery
- **Celery Broker Integration**: Redis serves as a high-speed, lightweight message broker that integrates seamlessly with Celery's task queue environment.
- **Low Operational Overhead**: Using Redis for brokers, lock managers, and rate-limiting eliminates the complexity of coordinating etcd, ZooKeeper, or Kafka clusters for internship scope.
- **Transient Heartbeats**: Worker status and heartbeat keys are stored with TTLs directly in Redis memory, preventing database writes for frequent 5-second checkins.

---

## 3. Worker Claim Strategy: Row-Level Database Locking

**Decision**: Pessimistic Locking with `FOR UPDATE SKIP LOCKED`
- **Race Condition Prevention**: When 100 workers poll the same queue, we must guarantee that only one worker successfully claims a job.
- **Performance**: Standard `FOR UPDATE` blocks other transactions until the lock is released, creating a bottleneck. Adding `SKIP LOCKED` causes other workers to skip the locked row and process subsequent rows immediately, enabling high-concurrency claims.

---

## 4. Observability and Performance: CQRS-lite

**Decision**: Cached Pre-Aggregated Metrics
- **Problem**: Querying total execution rates, success rate percentages, and averages over millions of log rows for dashboard rendering is slow and locks tables.
- **Solution**: We implement CQRS-lite by storing pre-aggregated statistics inside a `queuemetrics` table. Celery Beat aggregates data asynchronously every 10 seconds, decoupling write-heavy task execution logs from fast read-heavy dashboard metric requests.
