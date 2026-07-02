import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class WorkerQueueAssignmentResponse(BaseModel):
    queue_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class WorkerResponse(BaseModel):
    id: str
    hostname: Optional[str]
    status: str
    concurrency: int
    last_heartbeat: datetime
    created_at: datetime
    queue_assignments: List[WorkerQueueAssignmentResponse] = []

    model_config = ConfigDict(from_attributes=True)
