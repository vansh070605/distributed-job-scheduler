import uuid
import time
from datetime import datetime, timezone, timedelta
from celery.utils.log import get_task_logger
from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.job import Job
from app.models.queue import Queue
from app.models.retry_policy import RetryPolicy
from app.models.job_execution import JobExecution
from app.models.job_log import JobLog
from app.models.dead_letter_queue import DeadLetterQueue
from app.models.worker import Worker
from app.models.worker_queue_assignment import WorkerQueueAssignment
from app.models.queue_metrics import QueueMetrics

logger = get_task_logger(__name__)


def calculate_retry_delay(retry_count: int, policy: RetryPolicy) -> int:
    """Calculates backoff delay based on retry strategy."""
    if not policy:
        return 5  # default 5 seconds
    
    strategy = policy.strategy.lower()
    base_delay = policy.base_delay
    factor = policy.backoff_factor

    if strategy == "linear":
        return base_delay * retry_count
    elif strategy == "exponential":
        return base_delay * (factor ** (retry_count - 1))
    else:  # fixed
        return base_delay


@celery_app.task(name="app.workers.tasks.execute_queue_job")
def execute_queue_job(queue_id_str: str, worker_id: str):
    """Celery task executing job claiming and processing inside a queue."""
    queue_id = uuid.UUID(queue_id_str)
    session = SessionLocal()
    try:
        # Atomic Claim (FOR UPDATE SKIP LOCKED)
        # Find next queued job in the queue
        job = (
            session.query(Job)
            .filter(Job.status == "queued", Job.queue_id == queue_id)
            .order_by(
                Job.priority_override.desc().nullslast(),
                Job.created_at.asc(),
                Job.id.asc()
            )
            .limit(1)
            .with_for_update(skip_locked=True)
            .first()
        )

        if not job:
            logger.info(f"No queued jobs found in queue {queue_id}")
            return False

        # Mark job as claimed/running
        job.status = "running"
        job.last_worker_id = worker_id
        job.updated_at = datetime.now(timezone.utc)
        session.add(job)
        session.commit()

        # Create JobExecution record
        execution = JobExecution(
            id=uuid.uuid4(),
            job_id=job.id,
            worker_id=worker_id,
            status="running",
            started_at=datetime.now(timezone.utc)
        )
        session.add(execution)
        session.commit()

        # Write execution start log
        start_log = JobLog(
            id=uuid.uuid4(),
            job_id=job.id,
            execution_id=execution.id,
            level="info",
            message=f"Job claimed by worker {worker_id} and execution started.",
            timestamp=datetime.now(timezone.utc)
        )
        session.add(start_log)
        session.commit()

        # Idempotency Check
        if job.idempotency_key:
            completed_job = (
                session.query(Job)
                .filter(
                    Job.project_id == job.project_id,
                    Job.idempotency_key == job.idempotency_key,
                    Job.status == "completed",
                    Job.id != job.id
                )
                .first()
            )
            if completed_job:
                # Job has already been completed, short circuit
                job.status = "completed"
                session.add(job)
                
                execution.status = "completed"
                execution.finished_at = datetime.now(timezone.utc)
                execution.duration = 0.0
                session.add(execution)

                dup_log = JobLog(
                    id=uuid.uuid4(),
                    job_id=job.id,
                    execution_id=execution.id,
                    level="info",
                    message=f"Idempotency match found. Skipping execution. Copied result from job {completed_job.id}",
                    timestamp=datetime.now(timezone.utc)
                )
                session.add(dup_log)
                session.commit()
                return True

        # Process Job Payload (simulate execution)
        start_time = time.time()
        success = True
        error_msg = None

        try:
            payload = job.payload or {}
            # Allow configurable execution duration or simulate a crash
            duration_sim = payload.get("duration", 1)
            should_fail = payload.get("should_fail", False)
            
            logger.info(f"Executing job {job.name} (ID: {job.id}) - Simulating {duration_sim}s run")
            time.sleep(duration_sim)

            if should_fail:
                raise Exception(payload.get("error_message", "Simulated execution failure"))

        except Exception as e:
            success = False
            error_msg = str(e)

        duration = time.time() - start_time

        # Update Execution Status & Log Results
        if success:
            job.status = "completed"
            job.updated_at = datetime.now(timezone.utc)
            session.add(job)

            execution.status = "completed"
            execution.finished_at = datetime.now(timezone.utc)
            execution.duration = duration
            session.add(execution)

            end_log = JobLog(
                id=uuid.uuid4(),
                job_id=job.id,
                execution_id=execution.id,
                level="info",
                message=f"Job completed successfully in {duration:.2f} seconds.",
                timestamp=datetime.now(timezone.utc)
            )
            session.add(end_log)
            session.commit()
        else:
            # Handle Failure & Retry Policy
            execution.status = "failed"
            execution.finished_at = datetime.now(timezone.utc)
            execution.duration = duration
            execution.error_message = error_msg
            session.add(execution)

            fail_log = JobLog(
                id=uuid.uuid4(),
                job_id=job.id,
                execution_id=execution.id,
                level="error",
                message=f"Job failed: {error_msg}",
                timestamp=datetime.now(timezone.utc)
            )
            session.add(fail_log)
            session.commit()

            # Retrieve Queue and Retry Policy
            queue = session.query(Queue).filter(Queue.id == job.queue_id).first()
            policy = None
            if queue and queue.retry_policy_id:
                policy = session.query(RetryPolicy).filter(RetryPolicy.id == queue.retry_policy_id).first()

            max_retries = policy.max_retries if policy else job.max_retries

            if job.retry_count < max_retries:
                job.retry_count += 1
                delay_sec = calculate_retry_delay(job.retry_count, policy)
                
                job.status = "scheduled"
                job.next_run_at = datetime.now(timezone.utc) + timedelta(seconds=delay_sec)
                job.updated_at = datetime.now(timezone.utc)
                session.add(job)

                retry_log = JobLog(
                    id=uuid.uuid4(),
                    job_id=job.id,
                    execution_id=execution.id,
                    level="warning",
                    message=f"Job scheduled for retry {job.retry_count}/{max_retries} in {delay_sec} seconds.",
                    timestamp=datetime.now(timezone.utc)
                )
                session.add(retry_log)
                session.commit()
            else:
                # Move to Dead Letter Queue
                job.status = "dlq"
                job.updated_at = datetime.now(timezone.utc)
                session.add(job)

                dlq = DeadLetterQueue(
                    id=uuid.uuid4(),
                    job_id=job.id,
                    reason=error_msg or "Retries exhausted",
                    failed_at=datetime.now(timezone.utc),
                    original_payload=job.payload
                )
                session.add(dlq)

                dlq_log = JobLog(
                    id=uuid.uuid4(),
                    job_id=job.id,
                    execution_id=execution.id,
                    level="error",
                    message="Retries exhausted. Job moved to Dead Letter Queue (DLQ).",
                    timestamp=datetime.now(timezone.utc)
                )
                session.add(dlq_log)
                session.commit()

        # Trigger check for next job in the queue
        execute_queue_job.delay(queue_id_str, worker_id)
        return True

    except Exception as e:
        logger.exception(f"Unexpected error in execute_queue_job: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()


@celery_app.task(name="app.workers.tasks.worker_heartbeat")
def worker_heartbeat(worker_id: str, hostname: str, concurrency: int, queue_ids: list):
    """Sends heartbeat updating worker status and queue assignments."""
    session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        worker = session.query(Worker).filter(Worker.id == worker_id).first()
        if not worker:
            worker = Worker(
                id=worker_id,
                hostname=hostname,
                status="active",
                concurrency=concurrency,
                last_heartbeat=now,
                created_at=now
            )
            session.add(worker)
        else:
            worker.status = "active"
            worker.last_heartbeat = now
            session.add(worker)

        # Sync Queue Assignments
        session.query(WorkerQueueAssignment).filter(WorkerQueueAssignment.worker_id == worker_id).delete()
        for q_id_str in queue_ids:
            q_id = uuid.UUID(q_id_str)
            assignment = WorkerQueueAssignment(worker_id=worker_id, queue_id=q_id)
            session.add(assignment)

        session.commit()
    except Exception as e:
        logger.error(f"Failed to record worker heartbeat: {str(e)}")
        session.rollback()
    finally:
        session.close()
