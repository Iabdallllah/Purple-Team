from typing import Optional
from uuid import UUID
from datetime import datetime, UTC
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_token, verify_password
from app.models.user import User, UserRole
from app.models.api_key import APIKey, APIKeyStatus

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    from app.core.security import verify_token
    payload = verify_token(token)
    if not payload:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if not user_id:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user


async def get_current_user_from_api_key(
    api_key: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Authenticate using API key"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Hash the provided API key to compare with stored hash
    from app.core.security import get_password_hash, verify_password
    
    # We need to find the API key by prefix first, then verify
    prefix = api_key[:20]  # Assuming prefix is first 20 chars
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_prefix == prefix,
            APIKey.status == APIKeyStatus.ACTIVE
        )
    )
    api_key_obj = result.scalar_one_or_none()
    
    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    # Verify the full key against the hash
    if not verify_password(api_key, api_key_obj.key_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    # Check expiration
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key expired"
        )

    # Update last used timestamp
    from datetime import datetime, UTC
    api_key_obj.last_used_at = datetime.now(UTC)

    # Get the user
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == api_key_obj.user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="User inactive or not found")

    return user


async def get_current_user_flexible(
    token_user: User = Depends(get_current_user),
    api_key_user: User = Depends(get_current_user_from_api_key)
) -> User:
    """Get current user from either JWT token or API key"""
    return token_user or api_key_user


def require_permission(permission: str, organization_id: Optional[UUID] = None):
    """Dependency to check if user has a specific permission"""
    def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.is_superuser:
            return current_user
        if current_user.global_role == UserRole.SUPER_ADMIN:
            return current_user
        
        if not current_user.has_permission(permission, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}"
            )
        return current_user
    return permission_checker


def require_organization_role(organization_id: UUID, *roles: UserRole):
    """Dependency to check if user has a specific role in an organization"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.is_superuser:
            return current_user
        
        # Check organization membership
        user_org_role = None
        for org in current_user.organizations:
            if org.id == organization_id:
                # Find the user's role in this organization
                from sqlalchemy import select
                from app.models.user import user_organization
                from app.core.database import async_session_maker
                
                # This would need a proper query - for now check global role
                if current_user.global_role in roles:
                    return current_user
                break
        
        if current_user.global_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role in organization: {', '.join([r.value for r in roles])}"
            )
        return current_user
    return role_checker


# Backward compatibility
def require_role(*roles: str):
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_roles = [UserRole(r) for r in roles]
        if current_user.global_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker


require_super_admin = require_role("super_admin")
require_org_admin = require_role("org_admin")
require_analyst = require_role("admin", "analyst")
require_viewer = require_role("admin", "analyst", "viewer")