from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginationParams, PaginatedResponse


class EpisodeConstraints(BaseModel):
    max_duration_minutes: int = Field(default=30, ge=1, le=120)
    allowed_techniques: list[str] = Field(default_factory=list)
    safety_level: str = Field(default="active", pattern="^(passive|active|aggressive)$")
    max_concurrent_attacks: int = Field(default=3, ge=1, le=10)
    stop_on_first_detection: bool = False
    stop_on_successful_attack: bool = False


class EpisodeBase(BaseModel):
    scenario: str
    constraints: EpisodeConstraints = Field(default_factory=EpisodeConstraints)


class EpisodeCreate(EpisodeBase):
    project_id: UUID
    target_app_id: UUID


class EpisodeUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(pending|initializing|running|completed|failed|cancelled)$")
    error: Optional[str] = None


class EpisodeResponse(EpisodeBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    target_app_id: UUID
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EpisodeDetail(EpisodeResponse):
    target_app: Optional[dict] = None
    attacks: list[dict] = Field(default_factory=list)
    detections: list[dict] = Field(default_factory=list)
    responses: list[dict] = Field(default_factory=list)
    score: Optional[dict] = None


class EpisodeListParams(PaginationParams):
    project_id: Optional[UUID] = None
    target_app_id: Optional[UUID] = None
    scenario: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(pending|initializing|running|completed|failed|cancelled)$")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class EpisodeListResponse(PaginatedResponse[EpisodeResponse]):
    pass