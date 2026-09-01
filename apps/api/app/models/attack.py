from datetime import datetime, UTC
from uuid import uuid4
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, JSON, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.episode import Episode
    from app.models.detection import Detection


class Attack(Base):
    __tablename__ = "attacks"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    episode_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False)
    technique_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    owasp_category: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    attack_type: Mapped[str] = mapped_column(String(100), nullable=False)
    success: Mapped[bool] = mapped_column(nullable=False, default=False)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False, default=0.0)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_endpoint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    http_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    request_headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    request_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_status: Mapped[int | None] = mapped_column(nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    episode: Mapped["Episode"] = relationship("Episode", back_populates="attacks")
    detections: Mapped[list["Detection"]] = relationship("Detection", back_populates="attack")

    __table_args__ = (
        Index("ix_attacks_episode_id", "episode_id"),
        Index("ix_attacks_technique_id", "technique_id"),
        Index("ix_attacks_owasp_category", "owasp_category"),
        Index("ix_attacks_success", "success"),
        Index("ix_attacks_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Attack(id={self.id}, technique={self.technique_id}, success={self.success})>"