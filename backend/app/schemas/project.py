import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    name: str
    slug: str
    org_id: uuid.UUID


class ProjectCreate(BaseModel):
    name: str
    slug: str


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
