import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api import deps
from app.schemas.queue_metrics import QueueMetricsResponse
from app.models.queue_metrics import QueueMetrics
from app.models.queue import Queue
from app.models.user import User

router = APIRouter()


@router.get("/projects/{project_id}", response_model=List[QueueMetricsResponse])
async def get_project_metrics(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # Query queue metrics joining Queue to filter by project
    query = (
        select(QueueMetrics)
        .join(Queue, Queue.id == QueueMetrics.queue_id)
        .where(Queue.project_id == project_id)
    )
    result = await db.execute(query)
    return list(result.scalars().all())
