import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.worker import Worker
from app.models.worker_queue_assignment import WorkerQueueAssignment
from app.repositories.base import BaseRepository


class WorkerRepository(BaseRepository[Worker]):
    def __init__(self, session: AsyncSession):
        super().__init__(Worker, session)

    async def register_worker(
        self, worker_id: str, hostname: str, concurrency: int, queue_ids: List[uuid.UUID]
    ) -> Worker:
        # Check if worker exists
        query = select(Worker).where(Worker.id == worker_id)
        result = await self.session.execute(query)
        worker = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if not worker:
            worker = Worker(
                id=worker_id,
                hostname=hostname,
                status="active",
                concurrency=concurrency,
                last_heartbeat=now,
                created_at=now,
            )
            self.session.add(worker)
        else:
            worker.hostname = hostname
            worker.status = "active"
            worker.concurrency = concurrency
            worker.last_heartbeat = now
            self.session.add(worker)

        # Clear old assignments and set new ones
        delete_assignment = delete(WorkerQueueAssignment).where(
            WorkerQueueAssignment.worker_id == worker_id
        )
        await self.session.execute(delete_assignment)

        for q_id in queue_ids:
            assignment = WorkerQueueAssignment(worker_id=worker_id, queue_id=q_id)
            self.session.add(assignment)

        await self.session.commit()
        await self.session.refresh(worker)
        return worker

    async def record_heartbeat(self, worker_id: str) -> Optional[Worker]:
        query = select(Worker).where(Worker.id == worker_id)
        result = await self.session.execute(query)
        worker = result.scalar_one_or_none()
        if worker:
            worker.last_heartbeat = datetime.now(timezone.utc)
            worker.status = "active"
            self.session.add(worker)
            await self.session.commit()
            await self.session.refresh(worker)
        return worker

    async def get_active_workers(self) -> List[Worker]:
        # Worker is active if it had a heartbeat in the last 30 seconds
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=30)
        query = select(Worker).where(
            and_(Worker.status == "active", Worker.last_heartbeat >= cutoff)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def reap_stale_workers(self) -> List[str]:
        # Worker is stale if no heartbeat in the last 30 seconds
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=30)
        query = select(Worker).where(
            and_(Worker.status == "active", Worker.last_heartbeat < cutoff)
        )
        result = await self.session.execute(query)
        stale_workers = result.scalars().all()
        
        reaped_ids = []
        for worker in stale_workers:
            worker.status = "offline"
            self.session.add(worker)
            reaped_ids.append(worker.id)
            
        if reaped_ids:
            await self.session.commit()
        return reaped_ids
