from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.common import PaginationParams


class TargetAppConfig(BaseModel):
    base_url: Optional[HttpUrl] = None
    docker_image: Optional[str] = None
    docker_tag: str = "latest"
    environment: dict = Field(default_factory=dict)
    health_check_path: str = "/"
    health_check_interval: int = Field(default=30, ge=1)
    reset_script: Optional[str] = None
    exposed_ports: list[int] = Field(default_factory=lambda: [80, 443])
    resources: Optional[dict] = None


class TargetAppBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: str = Field(pattern="^(juice_shop|dvwa|custom)$")
    config: TargetAppConfig


class TargetAppCreate(TargetAppBase):
    project_id: UUID


class TargetAppUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    config: Optional[TargetAppConfig] = None
    status: Optional[str] = Field(default=None, pattern="^(pending|ready|error|deprecated)$")


class TargetAppResponse(TargetAppBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    status: str
    last_validated_at: Optional[datetime] = None
    validation_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TargetAppListParams(PaginationParams):
    project_id: Optional[UUID] = None
    type: Optional[str] = Field(default=None, pattern="^(juice_shop|dvwa|custom)$")
    status: Optional[str] = Field(default=None, pattern="^(pending|ready|error|deprecated)$")


class ValidateTargetAppRequest(BaseModel):
    target_app_id: UUID


class ValidateTargetAppResponse(BaseModel):
    success: bool
    status: str
    error: Optional[str] = None
    details: Optional[dict] = None


class TargetAppListResponse(BaseModel):
    items: list[TargetAppResponse]
    total: int
    page: int
    limit: int
    total_pages: int