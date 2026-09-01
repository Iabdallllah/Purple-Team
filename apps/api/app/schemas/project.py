from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginationParams, PaginatedResponse


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[str] = Field(default=None, pattern="^(active|archived|paused)$")


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


class ProjectWithStats(ProjectResponse):
    target_count: int = 0
    episode_count: int = 0
    latest_episode_at: Optional[datetime] = None


class ProjectListParams(PaginationParams):
    status: Optional[str] = Field(default=None, pattern="^(active|archived|paused)$")
    search: Optional[str] = None


class ProjectListResponse(PaginatedResponse[ProjectResponse]):
    pass