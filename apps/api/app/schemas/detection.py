from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DetectionType(str):
    LOG_ANALYSIS = "log_analysis"
    REQUEST_ANALYSIS = "request_analysis"
    PATTERN_MATCHING = "pattern_matching"
    ANOMALY_DETECTION = "anomaly_detection"
    SIGNATURE_BASED = "signature_based"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    ML_BASED = "ml_based"


class DetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    episode_id: UUID
    attack_id: Optional[UUID] = None
    detected: bool
    detection_type: str
    confidence: float
    details: dict
    matched_patterns: list[str]
    false_positive: bool
    timestamp: datetime
    created_at: datetime


class DetectionListParams(BaseModel):
    episode_id: UUID
    attack_id: Optional[UUID] = None
    detected: Optional[bool] = None
    detection_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)


class DetectionStats(BaseModel):
    total_detections: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    detection_rate: float = 0.0
    by_type: dict = Field(default_factory=dict)