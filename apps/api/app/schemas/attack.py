from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AttackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    episode_id: UUID
    technique_id: str
    owasp_category: str
    attack_type: str
    success: bool
    evidence: dict
    confidence: float
    payload: Optional[str] = None
    target_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    request_headers: Optional[dict] = None
    request_body: Optional[str] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    timestamp: datetime
    created_at: datetime


class AttackListParams(BaseModel):
    episode_id: UUID
    technique_id: Optional[str] = None
    owasp_category: Optional[str] = None
    success: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)


class AttackStats(BaseModel):
    total_attacks: int = 0
    successful_attacks: int = 0
    failed_attacks: int = 0
    by_technique: dict = Field(default_factory=dict)
    by_owasp_category: dict = Field(default_factory=dict)