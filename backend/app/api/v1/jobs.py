import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from croniter import croniter
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api import deps
from app.repositories import JobRepository, QueueRepository
from app.repositories.base import BaseRepository
from app.models.job import Job
from app.models.job_execution import JobExecution
from app.models.job_log import JobLog
from app.models.dead_letter_queue import DeadLetterQueue
from app.models.user import User
from app.schemas.job import JobCreate, JobResponse, JobExecutionResponse, JobLogResponse, DeadLetterQueueResponse
from app.workers.tasks import execute_queue_job

router = APIRouter()


@router.post("/projects/{project_id}/jobs", response_model=JobResponse)
async def create_job(
    project_id: uuid.UUID,
    job_in: JobCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    queue_repo = QueueRepository(db)
    queue = await queue_repo.get(job_in.queue_id)
    if not queue or queue.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target queue not found or belongs to another project",
        )
    
    job_repo = JobRepository(db)
    
    # Idempotency Check
    if job_in.idempotency_key:
        existing_job = await job_repo.get_by_idempotency_key(project_id, job_in.idempotency_key)
        if existing_job:
            # If the job is already complete or running, return it directly
            return existing_job

    now = datetime.now(timezone.utc)
    status_str = "queued"
    next_run_at = None

    if job_in.delay_seconds is not None:
        status_str = "scheduled"
        next_run_at = now + timedelta(seconds=job_in.delay_seconds)
    elif job_in.cron_expression is not None:
        if not croniter.is_valid(job_in.cron_expression):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cron expression format",
            )
        status_str = "scheduled"
        iter_cron = croniter(job_in.cron_expression, now)
        next_run_at = iter_cron.get_next(datetime)

    job = Job(
        queue_id=job_in.queue_id,
        project_id=project_id,
        name=job_in.name,
        payload=job_in.payload,
        status=status_str,
        priority_override=job_in.priority_override,
        max_retries=job_in.max_retries,
        cron_expression=job_in.cron_expression,
        next_run_at=next_run_at,
        idempotency_key=job_in.idempotency_key,
        created_at=now,
        updated_at=now
    )
    
    created_job = await job_repo.create(job)

    # Log initial submission
    await job_repo.write_log(
        job_id=created_job.id,
        execution_id=None,
        level="info",
        message=f"Job submitted via REST API. Initial status: {status_str}"
    )

    # If it is immediate execution (queued), trigger worker execution event
    if status_str == "queued":
        execute_queue_job.delay(str(created_job.queue_id), "api-trigger")

    return created_job


@router.get("/projects/{project_id}/jobs", response_model=List[JobResponse])
async def list_jobs(
    project_id: uuid.UUID,
    queue_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    job_repo = JobRepository(db)
    return await job_repo.get_jobs_with_filters(
        project_id=project_id,
        queue_id=queue_id,
        status=status,
        search=search,
        skip=skip,
        limit=limit
    )


@router.get("/projects/{project_id}/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    job_repo = JobRepository(db)
    job = await job_repo.get(job_id)
    if not job or job.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


@router.get("/projects/{project_id}/jobs/{job_id}/executions", response_model=List[JobExecutionResponse])
async def list_job_executions(
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    query = select(JobExecution).where(JobExecution.job_id == job_id).order_by(JobExecution.started_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/projects/{project_id}/jobs/{job_id}/logs", response_model=List[JobLogResponse])
async def list_job_logs(
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    query = select(JobLog).where(JobLog.job_id == job_id).order_by(JobLog.timestamp.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


# DLQ API Endpoints
@router.get("/projects/{project_id}/dlq", response_model=List[DeadLetterQueueResponse])
async def list_dlq_jobs(
    project_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    query = (
        select(DeadLetterQueue)
        .join(Job, Job.id == DeadLetterQueue.job_id)
        .where(Job.project_id == project_id)
        .order_by(DeadLetterQueue.failed_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/projects/{project_id}/dlq/{dlq_id}/retry")
async def retry_dlq_job(
    project_id: uuid.UUID,
    dlq_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["admin", "manager"]))
):
    # Fetch from DLQ
    dlq_repo = BaseRepository(DeadLetterQueue, db)
    dlq = await dlq_repo.get(dlq_id)
    if not dlq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DLQ entry not found",
        )
    
    # Reset job to queued
    job_repo = JobRepository(db)
    job = await job_repo.get(dlq.job_id)
    if job:
        job.status = "queued"
        job.retry_count = 0
        db.add(job)
        await dlq_repo.delete(dlq_id)
        await db.commit()

        # Trigger execution
        execute_queue_job.delay(str(job.queue_id), "dlq-retry")
        return {"status": "success", "message": f"Job {job.id} re-enqueued successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Job associated with this DLQ entry does not exist",
    )
