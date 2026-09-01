import enum
from datetime import datetime, UTC
from uuid import uuid4
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Enum, ForeignKey, JSON, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.target_app import TargetApp
    from app.models.attack import Attack
    from app.models.detection import Detection
    from app.models.response import Response
    from app.models.posture_score import PostureScore


class EpisodeStatus(str, enum.Enum):
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SafetyLevel(str, enum.Enum):
    PASSIVE = "passive"
    ACTIVE = "active"
    AGGRESSIVE = "aggressive"


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    target_app_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("target_apps.id", ondelete="CASCADE"), nullable=False)
    scenario: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[EpisodeStatus] = mapped_column(Enum(EpisodeStatus), default=EpisodeStatus.PENDING, nullable=False)
    constraints: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="episodes")
    target_app: Mapped["TargetApp"] = relationship("TargetApp", back_populates="episodes")
    attacks: Mapped[list["Attack"]] = relationship("Attack", back_populates="episode", cascade="all, delete-orphan")
    detections: Mapped[list["Detection"]] = relationship("Detection", back_populates="episode", cascade="all, delete-orphan")
    responses: Mapped[list["Response"]] = relationship("Response", back_populates="episode", cascade="all, delete-orphan")
    posture_score: Mapped["PostureScore | None"] = relationship("PostureScore", back_populates="episode", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_episodes_project_id", "project_id"),
        Index("ix_episodes_target_app_id", "target_app_id"),
        Index("ix_episodes_status", "status"),
        Index("ix_episodes_scenario", "scenario"),
        Index("ix_episodes_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Episode(id={self.id}, scenario={self.scenario}, status={self.status})>"