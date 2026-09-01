import enum
from datetime import datetime, UTC
from uuid import uuid4

from sqlalchemy import String, DateTime, Enum, Boolean, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID

from app.core.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


# Association table for user-organization membership
user_organization = Table(
    "user_organizations",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
    Column("role", Enum(UserRole), default=UserRole.VIEWER, nullable=False),
    Column("joined_at", DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    global_role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    owned_organizations: Mapped[list["Organization"]] = relationship("Organization", back_populates="owner")
    organizations: Mapped[list["Organization"]] = relationship(
        "Organization",
        secondary=user_organization,
        back_populates="members"
    )
    owned_projects: Mapped[list["Project"]] = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id")
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="user")

    @property
    def role(self):
        # backward compat for old code using user.role
        return self.global_role
    @role.setter
    def role(self, value):
        if isinstance(value, str):
            mapping = {"admin": UserRole.ORG_ADMIN, "ADMIN": UserRole.ORG_ADMIN, "super_admin": UserRole.SUPER_ADMIN, "org_admin": UserRole.ORG_ADMIN, "analyst": UserRole.ANALYST, "viewer": UserRole.VIEWER}
            self.global_role = mapping.get(value.lower(), UserRole.VIEWER) if value else UserRole.VIEWER
        elif isinstance(value, UserRole):
            self.global_role = value
        else:
            self.global_role = UserRole.VIEWER

    @property
    def projects(self):
        return self.owned_projects
    @projects.setter
    def projects(self, value):
        self.owned_projects = value

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.global_role})>"

    def has_permission(self, permission: str, organization_id: UUID = None) -> bool:
        """Check if user has a specific permission"""
        if self.is_superuser:
            return True
        if self.global_role == UserRole.SUPER_ADMIN:
            return True
        
        # Check organization-specific role
        if organization_id:
            for org in self.organizations:
                if org.id == organization_id:
                    org_role = next((m.role for m in org.members if m.id == self.id), None)
                    if org_role:
                        return self._role_has_permission(org_role, permission)
        return False

    def _role_has_permission(self, role: UserRole, permission: str) -> bool:
        """Check if role has permission"""
        role_permissions = {
            UserRole.ORG_ADMIN: ["*"],
            UserRole.ANALYST: [
                "projects:read", "projects:write",
                "targets:read", "targets:write",
                "episodes:read", "episodes:write",
                "reports:read", "reports:write",
            ],
            UserRole.VIEWER: [
                "projects:read",
                "targets:read",
                "episodes:read",
                "reports:read",
            ],
        }
        perms = role_permissions.get(role, [])
        return "*" in perms or permission in perms