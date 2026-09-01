import enum
from datetime import datetime, UTC
from uuid import uuid4
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.episode import Episode


class TargetAppType(str, enum.Enum):
    JUICE_SHOP = "juice_shop"
    DVWA = "dvwa"
    CUSTOM = "custom"


class TargetAppStatus(str, enum.Enum):
    PENDING = "pending"
    READY = "ready"
    ERROR = "error"
    DEPRECATED = "deprecated"


class TargetApp(Base):
    __tablename__ = "target_apps"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[TargetAppType] = mapped_column(Enum(TargetAppType), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[TargetAppStatus] = mapped_column(Enum(TargetAppStatus), default=TargetAppStatus.PENDING, nullable=False)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validation_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="target_apps")
    episodes: Mapped[list["Episode"]] = relationship("Episode", back_populates="target_app", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_target_apps_project_id", "project_id"),
        Index("ix_target_apps_status", "status"),
        Index("ix_target_apps_type", "type"),
    )

    def __repr__(self) -> str:
        return f"<TargetApp(id={self.id}, name={self.name}, type={self.type}, status={self.status})>"