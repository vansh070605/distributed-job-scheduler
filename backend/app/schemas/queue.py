import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class QueueBase(BaseModel):
    name: str
    priority: int = Field(default=1, ge=0)
    concurrency: int = Field(default=10, ge=1)
    is_paused: bool = False
    rate_limit: Optional[int] = Field(default=None, ge=1)
    retry_policy_id: Optional[uuid.UUID] = None


class QueueCreate(QueueBase):
    pass


class QueueUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[int] = None
    concurrency: Optional[int] = None
    is_paused: Optional[bool] = None
    rate_limit: Optional[int] = None
    retry_policy_id: Optional[uuid.UUID] = None


class QueueResponse(QueueBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
