from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api import deps
from app.repositories import WorkerRepository
from app.schemas.worker import WorkerResponse
from app.models.worker import Worker
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[WorkerResponse])
async def list_workers(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # Retrieve workers including assignments using selectinload
    query = select(Worker).options(selectinload(Worker.queue_assignments)).order_by(Worker.last_heartbeat.desc())
    result = await db.execute(query)
    return list(result.scalars().all())
