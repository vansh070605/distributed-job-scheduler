import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RetryPolicyBase(BaseModel):
    name: str
    strategy: str = "fixed"  # fixed, linear, exponential
    max_retries: int = Field(default=3, ge=0)
    base_delay: int = Field(default=5, ge=1)  # in seconds
    backoff_factor: int = Field(default=2, ge=1)


class RetryPolicyCreate(RetryPolicyBase):
    pass


class RetryPolicyUpdate(BaseModel):
    name: Optional[str] = None
    strategy: Optional[str] = None
    max_retries: Optional[int] = None
    base_delay: Optional[int] = None
    backoff_factor: Optional[int] = None


class RetryPolicyResponse(RetryPolicyBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
