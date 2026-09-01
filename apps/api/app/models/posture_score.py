from datetime import datetime, UTC
from uuid import uuid4
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.episode import Episode
    from app.models.project import Project


class PostureScore(Base):
    __tablename__ = "posture_scores"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    episode_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, unique=True)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    detection_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    mttr_seconds: Mapped[int] = mapped_column(nullable=False)
    coverage: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    overall_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    trend: Mapped[str | None] = mapped_column(String(20), nullable=True)
    previous_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    episode: Mapped["Episode"] = relationship("Episode", back_populates="posture_score")
    project: Mapped["Project"] = relationship("Project")

    __table_args__ = (
        Index("ix_posture_scores_project_id", "project_id"),
        Index("ix_posture_scores_episode_id", "episode_id"),
        Index("ix_posture_scores_calculated_at", "calculated_at"),
    )

    def __repr__(self) -> str:
        return f"<PostureScore(episode_id={self.episode_id}, overall={self.overall_score})>"