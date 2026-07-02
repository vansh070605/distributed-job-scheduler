import uuid
from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict


class JobCreate(BaseModel):
    queue_id: uuid.UUID
    name: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority_override: Optional[int] = None
    max_retries: int = 3
    cron_expression: Optional[str] = None
    delay_seconds: Optional[int] = None  # to schedule a delayed job
    idempotency_key: Optional[str] = None


class JobResponse(BaseModel):
    id: uuid.UUID
    queue_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    payload: Dict[str, Any]
    status: str
    priority_override: Optional[int]
    retry_count: int
    max_retries: int
    cron_expression: Optional[str]
    next_run_at: Optional[datetime]
    idempotency_key: Optional[str]
    last_worker_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobExecutionResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    worker_id: Optional[str]
    status: str
    error_message: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]
    duration: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class JobLogResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    execution_id: Optional[uuid.UUID]
    level: str
    message: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class DeadLetterQueueResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    reason: str
    failed_at: datetime
    original_payload: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
