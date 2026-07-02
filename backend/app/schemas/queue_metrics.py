import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class QueueMetricsResponse(BaseModel):
    queue_id: uuid.UUID
    queued_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    avg_execution_time_ms: float
    throughput_1h: int
    success_rate: float
    last_updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
