import uuid
from datetime import datetime, timezone, timedelta
from croniter import croniter
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
from app.models.queue_metrics import QueueMetrics
from app.workers.tasks import execute_queue_job

logger = get_task_logger(__name__)


@celery_app.task(name="app.scheduler.tasks.poll_and_enqueue_due_jobs")
def poll_and_enqueue_due_jobs():
    """Polls database for due jobs and puts them in queued state."""
    session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        due_jobs = (
            session.query(Job)
            .filter(Job.status == "scheduled", Job.next_run_at <= now)
            .all()
        )

        for job in due_jobs:
            logger.info(f"Enqueuing due job {job.name} (ID: {job.id})")
            
            # If it's a cron job, calculate the next run time and spawn a copy or update this
            if job.cron_expression:
                try:
                    # Save history and trigger a clone of this job to execute
                    # For simplicity, we create a run copy or we run it and advance the cron next_run_at
                    # Let's advance this job's next_run_at to future, and spawn a cloned child job that is queued
                    iter_cron = croniter(job.cron_expression, now)
                    next_run = iter_cron.get_next(datetime)
                    
                    # Create execution copy
                    cloned_job = Job(
                        id=uuid.uuid4(),
                        queue_id=job.queue_id,
                        project_id=job.project_id,
                        name=f"{job.name} (Run)",
                        payload=job.payload,
                        status="queued",
                        priority_override=job.priority_override,
                        max_retries=job.max_retries,
                        idempotency_key=f"{job.idempotency_key}-{now.timestamp()}" if job.idempotency_key else None,
                        created_at=now,
                        updated_at=now
                    )
                    session.add(cloned_job)
                    
                    # Log cron scheduling
                    cron_log = JobLog(
                        id=uuid.uuid4(),
                        job_id=job.id,
                        execution_id=None,
                        level="info",
                        message=f"Cron trigger fired. Spawning job run {cloned_job.id}. Next run scheduled at {next_run}",
                        timestamp=now
                    )
                    session.add(cron_log)
                    
                    job.next_run_at = next_run
                    session.add(job)
                    
                    session.commit()
                    # Trigger worker for the queue
                    execute_queue_job.delay(str(cloned_job.queue_id), "scheduler")
                except Exception as cron_err:
                    logger.error(f"Failed to parse cron for job {job.id}: {str(cron_err)}")
            else:
                job.status = "queued"
                job.next_run_at = None
                session.add(job)
                session.commit()
                execute_queue_job.delay(str(job.queue_id), "scheduler")

    except Exception as e:
        logger.error(f"Error in poll_and_enqueue_due_jobs: {str(e)}")
        session.rollback()
    finally:
        session.close()


@celery_app.task(name="app.scheduler.tasks.reap_stale_workers")
def reap_stale_workers():
    """Identifies crashed workers and recovers/re-enqueues their running jobs."""
    session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=30)
        
        stale_workers = (
            session.query(Worker)
            .filter(Worker.status == "active", Worker.last_heartbeat < cutoff)
            .all()
        )

        for worker in stale_workers:
            logger.warning(f"Worker {worker.id} has missed heartbeats. Flagging offline.")
            worker.status = "offline"
            session.add(worker)

            # Find active jobs on this worker
            running_jobs = (
                session.query(Job)
                .filter(Job.status == "running", Job.last_worker_id == worker.id)
                .all()
            )

            for job in running_jobs:
                logger.warning(f"Recovering stale running job {job.id} from worker {worker.id}")
                
                # Fetch queue's retry policy
                queue = session.query(Queue).filter(Queue.id == job.queue_id).first()
                policy = None
                if queue and queue.retry_policy_id:
                    policy = session.query(RetryPolicy).filter(RetryPolicy.id == queue.retry_policy_id).first()

                max_retries = policy.max_retries if policy else job.max_retries

                # Create failed execution record
                execution = (
                    session.query(JobExecution)
                    .filter(JobExecution.job_id == job.id, JobExecution.status == "running")
                    .order_by(JobExecution.started_at.desc())
                    .first()
                )
                if execution:
                    execution.status = "failed"
                    execution.finished_at = now
                    execution.error_message = f"Worker heartbeat timeout. Worker {worker.id} died."
                    session.add(execution)

                if job.retry_count < max_retries:
                    job.retry_count += 1
                    job.status = "queued"  # immediate retry or could compute backoff
                    job.next_run_at = None
                    session.add(job)

                    rec_log = JobLog(
                        id=uuid.uuid4(),
                        job_id=job.id,
                        execution_id=execution.id if execution else None,
                        level="warning",
                        message=f"Job recovered from offline worker {worker.id}. Re-enqueuing (retry {job.retry_count}/{max_retries})",
                        timestamp=now
                    )
                    session.add(rec_log)
                else:
                    job.status = "dlq"
                    session.add(job)

                    dlq = DeadLetterQueue(
                        id=uuid.uuid4(),
                        job_id=job.id,
                        reason=f"Worker heartbeat timeout on worker {worker.id}. Retries exhausted.",
                        failed_at=now,
                        original_payload=job.payload
                    )
                    session.add(dlq)

                    dlq_log = JobLog(
                        id=uuid.uuid4(),
                        job_id=job.id,
                        execution_id=execution.id if execution else None,
                        level="error",
                        message="Worker heartbeat timeout. Retries exhausted. Job moved to DLQ.",
                        timestamp=now
                    )
                    session.add(dlq_log)

            session.commit()

    except Exception as e:
        logger.error(f"Error in reap_stale_workers: {str(e)}")
        session.rollback()
    finally:
        session.close()


@celery_app.task(name="app.scheduler.tasks.aggregate_queue_metrics")
def aggregate_queue_metrics():
    """Aggregates and cache stats inside queuemetrics tables."""
    session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        queues = session.query(Queue).all()

        for queue in queues:
            # Gather metrics
            queued = session.query(Job).filter(Job.queue_id == queue.id, Job.status == "queued").count()
            running = session.query(Job).filter(Job.queue_id == queue.id, Job.status == "running").count()
            completed = session.query(Job).filter(Job.queue_id == queue.id, Job.status == "completed").count()
            failed = session.query(Job).filter(Job.queue_id == queue.id, Job.status == "failed").count()
            dlq = session.query(Job).filter(Job.queue_id == queue.id, Job.status == "dlq").count()

            # Executions for avg time
            executions = (
                session.query(JobExecution)
                .join(Job, Job.id == JobExecution.job_id)
                .filter(Job.queue_id == queue.id, JobExecution.status == "completed")
                .all()
            )
            durations = [e.duration for e in executions if e.duration is not None]
            avg_duration_ms = (sum(durations) / len(durations) * 1000.0) if durations else 0.0

            total_runs = completed + failed + dlq
            success_rate = (completed / total_runs * 100.0) if total_runs > 0 else 100.0

            # Pre-aggregated throughput (completed in last 1 hour)
            one_hour_ago = now - timedelta(hours=1)
            throughput = (
                session.query(JobExecution)
                .join(Job, Job.id == JobExecution.job_id)
                .filter(
                    Job.queue_id == queue.id,
                    JobExecution.status == "completed",
                    JobExecution.finished_at >= one_hour_ago
                )
                .count()
            )

            metrics = session.query(QueueMetrics).filter(QueueMetrics.queue_id == queue.id).first()
            if not metrics:
                metrics = QueueMetrics(
                    queue_id=queue.id,
                    queued_jobs=queued,
                    running_jobs=running,
                    completed_jobs=completed,
                    failed_jobs=failed + dlq,
                    avg_execution_time_ms=avg_duration_ms,
                    throughput_1h=throughput,
                    success_rate=success_rate,
                    last_updated_at=now
                )
                session.add(metrics)
            else:
                metrics.queued_jobs = queued
                metrics.running_jobs = running
                metrics.completed_jobs = completed
                metrics.failed_jobs = failed + dlq
                metrics.avg_execution_time_ms = avg_duration_ms
                metrics.throughput_1h = throughput
                metrics.success_rate = success_rate
                metrics.last_updated_at = now
                session.add(metrics)

        session.commit()
    except Exception as e:
        logger.error(f"Error in aggregate_queue_metrics: {str(e)}")
        session.rollback()
    finally:
        session.close()
