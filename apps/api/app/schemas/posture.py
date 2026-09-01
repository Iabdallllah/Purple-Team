from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginationParams, PaginatedResponse


class CoverageItem(BaseModel):
    total_techniques: int = 0
    covered_techniques: int = 0
    coverage: float = 0.0


class PostureScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    episode_id: UUID
    project_id: UUID
    detection_rate: float
    mttr_seconds: int
    coverage: dict[str, CoverageItem]
    overall_score: float
    trend: Optional[str] = None
    previous_score: Optional[float] = None
    calculated_at: datetime


class PostureScoreTrendItem(BaseModel):
    episode_id: UUID
    overall_score: float
    detection_rate: float
    mttr_seconds: int
    calculated_at: datetime


class PostureScoreTrend(BaseModel):
    project_id: UUID
    scores: list[PostureScoreTrendItem]
    trend: str
    improvement_rate: float


class PostureScoreListParams(PaginationParams):
    project_id: Optional[UUID] = None
    episode_id: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class PostureScoreListResponse(PaginatedResponse[PostureScoreResponse]):
    pass


class PostureSummary(BaseModel):
    project_id: UUID
    current_score: float
    previous_score: Optional[float] = None
    trend: str
    detection_rate: float
    mttr_seconds: int
    coverage_by_category: dict[str, float]
    total_episodes: int
    last_calculated_at: datetime