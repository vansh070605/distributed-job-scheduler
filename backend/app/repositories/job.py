import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job
from app.models.job_execution import JobExecution
from app.models.job_log import JobLog
from app.models.dead_letter_queue import DeadLetterQueue
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    def __init__(self, session: AsyncSession):
        super().__init__(Job, session)

    async def get_by_idempotency_key(self, project_id: uuid.UUID, key: str) -> Optional[Job]:
        query = select(Job).where(Job.project_id == project_id, Job.idempotency_key == key)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def claim_next_job(self, queue_id: uuid.UUID, worker_id: str) -> Optional[Job]:
        # Subquery to find the next job using SELECT ... FOR UPDATE SKIP LOCKED
        subquery = (
            select(Job.id)
            .where(and_(Job.status == "queued", Job.queue_id == queue_id))
            .order_by(
                Job.priority_override.desc().nullslast(),
                Job.created_at.asc(),
                Job.id.asc()
            )
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        
        result_sub = await self.session.execute(subquery)
        job_id = result_sub.scalar_one_or_none()

        if not job_id:
            return None

        # Atomically update the claimed job
        update_stmt = (
            update(Job)
            .where(Job.id == job_id)
            .values(
                status="running",
                last_worker_id=worker_id,
                updated_at=datetime.now(timezone.utc)
            )
            .returning(Job)
        )
        
        result = await self.session.execute(update_stmt)
        await self.session.commit()
        return result.scalar()

    async def create_execution(self, job_id: uuid.UUID, worker_id: str) -> JobExecution:
        execution = JobExecution(
            id=uuid.uuid4(),
            job_id=job_id,
            worker_id=worker_id,
            status="running",
            started_at=datetime.now(timezone.utc)
        )
        self.session.add(execution)
        await self.session.commit()
        await self.session.refresh(execution)
        return execution

    async def complete_execution(self, execution_id: uuid.UUID, duration: float) -> JobExecution:
        query = select(JobExecution).where(JobExecution.id == execution_id)
        res = await self.session.execute(query)
        execution = res.scalar_one()
        execution.status = "completed"
        execution.finished_at = datetime.now(timezone.utc)
        execution.duration = duration
        self.session.add(execution)
        await self.session.commit()
        await self.session.refresh(execution)
        return execution

    async def fail_execution(self, execution_id: uuid.UUID, error_msg: str, duration: float) -> JobExecution:
        query = select(JobExecution).where(JobExecution.id == execution_id)
        res = await self.session.execute(query)
        execution = res.scalar_one()
        execution.status = "failed"
        execution.error_message = error_msg
        execution.finished_at = datetime.now(timezone.utc)
        execution.duration = duration
        self.session.add(execution)
        await self.session.commit()
        await self.session.refresh(execution)
        return execution

    async def write_log(self, job_id: uuid.UUID, execution_id: Optional[uuid.UUID], level: str, message: str) -> JobLog:
        log = JobLog(
            id=uuid.uuid4(),
            job_id=job_id,
            execution_id=execution_id,
            level=level,
            message=message,
            timestamp=datetime.now(timezone.utc)
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def send_to_dlq(self, job_id: uuid.UUID, reason: str, original_payload: dict) -> DeadLetterQueue:
        dlq_entry = DeadLetterQueue(
            id=uuid.uuid4(),
            job_id=job_id,
            reason=reason,
            failed_at=datetime.now(timezone.utc),
            original_payload=original_payload
        )
        self.session.add(dlq_entry)
        
        # Update job status
        query = select(Job).where(Job.id == job_id)
        res = await self.session.execute(query)
        job = res.scalar_one()
        job.status = "dlq"
        self.session.add(job)
        
        await self.session.commit()
        return dlq_entry

    async def get_jobs_with_filters(
        self,
        project_id: uuid.UUID,
        queue_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Job]:
        conditions = [Job.project_id == project_id]
        if queue_id:
            conditions.append(Job.queue_id == queue_id)
        if status:
            conditions.append(Job.status == status)
        if search:
            conditions.append(Job.name.ilike(f"%{search}%"))

        query = (
            select(Job)
            .where(and_(*conditions))
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
