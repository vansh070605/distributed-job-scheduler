from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.queue import Queue
from app.repositories.base import BaseRepository


class QueueRepository(BaseRepository[Queue]):
    def __init__(self, session: AsyncSession):
        super().__init__(Queue, session)

    async def get_by_name(self, project_id: str, name: str) -> Optional[Queue]:
        query = select(Queue).where(Queue.project_id == project_id, Queue.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_project(self, project_id: str) -> List[Queue]:
        query = select(Queue).where(Queue.project_id == project_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
