import enum
from datetime import datetime, UTC
from uuid import uuid4
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Enum, ForeignKey, JSON, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.episode import Episode
    from app.models.detection import Detection


class ResponseActionType(str, enum.Enum):
    BLOCK_IP = "block_ip"
    RATE_LIMIT = "rate_limit"
    ADD_HEADER = "add_header"
    MODIFY_HEADER = "modify_header"
    UPDATE_WAF_RULE = "update_waf_rule"
    REVOKE_SESSION = "revoke_session"
    FORCE_REAUTH = "force_reauth"
    DISABLE_ENDPOINT = "disable_endpoint"
    PATCH_VULNERABILITY = "patch_vulnerability"
    ADD_AUTH_CHECK = "add_auth_check"
    ENABLE_CSP = "enable_csp"
    ENABLE_HSTS = "enable_hsts"
    CUSTOM = "custom"


class Response(Base):
    __tablename__ = "responses"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    episode_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False)
    detection_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("detections.id", ondelete="SET NULL"), nullable=True)
    action_type: Mapped[ResponseActionType] = mapped_column(Enum(ResponseActionType), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    target: Mapped[str | None] = mapped_column(String(500), nullable=True)
    success: Mapped[bool] = mapped_column(nullable=False, default=False)
    result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reverted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    episode: Mapped["Episode"] = relationship("Episode", back_populates="responses")
    detection: Mapped["Detection | None"] = relationship("Detection", back_populates="responses")

    __table_args__ = (
        Index("ix_responses_episode_id", "episode_id"),
        Index("ix_responses_detection_id", "detection_id"),
        Index("ix_responses_action_type", "action_type"),
        Index("ix_responses_success", "success"),
        Index("ix_responses_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Response(id={self.id}, action={self.action_type}, success={self.success})>"