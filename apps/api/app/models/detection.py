import enum
from datetime import datetime, UTC
from uuid import uuid4
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Enum, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.episode import Episode
    from app.models.attack import Attack
    from app.models.response import Response


class DetectionType(str, enum.Enum):
    LOG_ANALYSIS = "log_analysis"
    REQUEST_ANALYSIS = "request_analysis"
    PATTERN_MATCHING = "pattern_matching"
    ANOMALY_DETECTION = "anomaly_detection"
    SIGNATURE_BASED = "signature_based"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    ML_BASED = "ml_based"


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    episode_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False)
    attack_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("attacks.id", ondelete="SET NULL"), nullable=True)
    detected: Mapped[bool] = mapped_column(nullable=False, default=False)
    detection_type: Mapped[DetectionType] = mapped_column(Enum(DetectionType), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False, default=0.0)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    matched_patterns: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    false_positive: Mapped[bool] = mapped_column(nullable=False, default=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    episode: Mapped["Episode"] = relationship("Episode", back_populates="detections")
    attack: Mapped["Attack | None"] = relationship("Attack", back_populates="detections")
    responses: Mapped[list["Response"]] = relationship("Response", back_populates="detection")

    __table_args__ = (
        Index("ix_detections_episode_id", "episode_id"),
        Index("ix_detections_attack_id", "attack_id"),
        Index("ix_detections_detected", "detected"),
        Index("ix_detections_detection_type", "detection_type"),
        Index("ix_detections_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Detection(id={self.id}, detected={self.detected}, type={self.detection_type})>"