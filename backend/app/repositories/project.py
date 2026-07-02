from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: AsyncSession):
        super().__init__(Project, session)

    async def get_by_slug(self, org_id: str, slug: str) -> Optional[Project]:
        query = select(Project).where(Project.org_id == org_id, Project.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_org(self, org_id: str) -> List[Project]:
        query = select(Project).where(Project.org_id == org_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
