import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.repositories import QueueRepository
from app.repositories.base import BaseRepository
from app.models.queue import Queue
from app.models.retry_policy import RetryPolicy
from app.models.user import User
from app.schemas.queue import QueueCreate, QueueResponse, QueueUpdate
from app.schemas.retry_policy import RetryPolicyCreate, RetryPolicyResponse

router = APIRouter()


@router.post("/projects/{project_id}/queues", response_model=QueueResponse)
async def create_queue(
    project_id: uuid.UUID,
    queue_in: QueueCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["admin", "manager"]))
):
    queue_repo = QueueRepository(db)
    existing_queue = await queue_repo.get_by_name(str(project_id), queue_in.name)
    if existing_queue:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Queue with this name already exists in this project",
        )
    
    queue = Queue(
        project_id=project_id,
        name=queue_in.name,
        priority=queue_in.priority,
        concurrency=queue_in.concurrency,
        is_paused=queue_in.is_paused,
        rate_limit=queue_in.rate_limit,
        retry_policy_id=queue_in.retry_policy_id
    )
    return await queue_repo.create(queue)


@router.get("/projects/{project_id}/queues", response_model=List[QueueResponse])
async def list_queues(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    queue_repo = QueueRepository(db)
    return await queue_repo.get_by_project(str(project_id))


@router.put("/projects/{project_id}/queues/{queue_id}", response_model=QueueResponse)
async def update_queue(
    project_id: uuid.UUID,
    queue_id: uuid.UUID,
    queue_in: QueueUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["admin", "manager"]))
):
    queue_repo = QueueRepository(db)
    db_queue = await queue_repo.get(queue_id)
    if not db_queue or db_queue.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found",
        )
    
    update_dict = queue_in.model_dump(exclude_unset=True)
    return await queue_repo.update(db_queue, update_dict)


# Retry Policies Endpoints
@router.post("/projects/{project_id}/retry-policies", response_model=RetryPolicyResponse)
async def create_retry_policy(
    project_id: uuid.UUID,
    policy_in: RetryPolicyCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["admin", "manager"]))
):
    policy_repo = BaseRepository(RetryPolicy, db)
    policy = RetryPolicy(
        project_id=project_id,
        name=policy_in.name,
        strategy=policy_in.strategy,
        max_retries=policy_in.max_retries,
        base_delay=policy_in.base_delay,
        backoff_factor=policy_in.backoff_factor
    )
    return await policy_repo.create(policy)


@router.get("/projects/{project_id}/retry-policies", response_model=List[RetryPolicyResponse])
async def list_retry_policies(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # Select from DB using standard select query
    from sqlalchemy import select
    query = select(RetryPolicy).where(RetryPolicy.project_id == project_id)
    result = await db.execute(query)
    return list(result.scalars().all())
