from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_active_user, require_analyst
from app.models.target_app import TargetApp, TargetAppType, TargetAppStatus
from app.models.project import Project
from app.schemas.target_app import (
    TargetAppCreate, TargetAppUpdate, TargetAppResponse,
    TargetAppListParams, TargetAppListResponse,
    ValidateTargetAppRequest, ValidateTargetAppResponse
)

router = APIRouter()


@router.post("", response_model=TargetAppResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    target_data: TargetAppCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    project_result = await db.execute(
        select(Project).where(Project.id == target_data.project_id, Project.owner_id == current_user.id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    target = TargetApp(
        project_id=target_data.project_id,
        name=target_data.name,
        type=TargetAppType(target_data.type),
        config=target_data.config.model_dump(),
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return target


@router.get("", response_model=TargetAppListResponse)
async def list_targets(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    project_id: Optional[UUID] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = select(TargetApp).join(Project).where(Project.owner_id == current_user.id)

    if project_id:
        query = query.where(TargetApp.project_id == project_id)
    if type:
        query = query.where(TargetApp.type == TargetAppType(type))
    if status:
        query = query.where(TargetApp.status == TargetAppStatus(status))

    total_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(total_query) or 0

    query = query.order_by(TargetApp.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    targets = result.scalars().all()

    return TargetAppListResponse(
        items=targets,
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit,
    )


@router.get("/{target_id}", response_model=TargetAppResponse)
async def get_target(
    target_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(
        select(TargetApp)
        .join(Project)
        .where(TargetApp.id == target_id, Project.owner_id == current_user.id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target


@router.patch("/{target_id}", response_model=TargetAppResponse)
async def update_target(
    target_id: UUID,
    target_data: TargetAppUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(
        select(TargetApp)
        .join(Project)
        .where(TargetApp.id == target_id, Project.owner_id == current_user.id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    for field, value in target_data.model_dump(exclude_unset=True).items():
        if field == "config" and value:
            value = value.model_dump()
        setattr(target, field, value)

    await db.commit()
    await db.refresh(target)
    return target


@router.post("/{target_id}/validate", response_model=ValidateTargetAppResponse)
async def validate_target(
    target_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(
        select(TargetApp)
        .join(Project)
        .where(TargetApp.id == target_id, Project.owner_id == current_user.id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    # TODO: Implement actual validation logic
    # For now, just update status
    from datetime import datetime, UTC
    target.status = TargetAppStatus.READY
    target.last_validated_at = datetime.now(UTC)
    target.validation_error = None
    await db.commit()

    return ValidateTargetAppResponse(success=True, status=target.status.value)