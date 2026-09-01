from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import redis.asyncio as redis
import json

from app.api.deps import get_db, get_current_active_user
from app.core.config import get_settings
from app.models.episode import Episode, EpisodeStatus
from app.models.attack import Attack
from app.models.detection import Detection
from app.models.response import Response
from app.models.posture_score import PostureScore
from app.models.project import Project
from app.models.target_app import TargetApp
from app.schemas.episode import EpisodeCreate, EpisodeResponse, EpisodeDetail, EpisodeListParams, EpisodeListResponse
from app.schemas.posture import PostureScoreResponse

router = APIRouter()
settings = get_settings()

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> Optional[redis.Redis]:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # quick ping check, but don't fail if unavailable in demo
            await _redis_client.ping()
        except Exception:
            # Fallback: no redis (HF/Railway demo without redis) -> use None, episode will run inline or stay pending
            import structlog
            structlog.get_logger(__name__).warning("Redis unavailable, episode queue disabled", redis_url=settings.REDIS_URL)
            return None
    # verify still alive
    try:
        await _redis_client.ping()
    except Exception:
        return None
    return _redis_client


async def push_episode_command(redis_client: Optional[redis.Redis], episode_id: UUID, command: str):
    if redis_client is None:
        import structlog
        structlog.get_logger(__name__).info("Skipping episode queue (no redis)", episode_id=str(episode_id))
        return
    try:
        await redis_client.xadd(
            "episode:commands",
            {"episode_id": str(episode_id), "command": command, "timestamp": str(datetime.utcnow())},
        )
    except Exception as e:
        import structlog
        structlog.get_logger(__name__).warning("Failed to push episode command", error=str(e), episode_id=str(episode_id))


from datetime import datetime, UTC


@router.post("", response_model=EpisodeResponse, status_code=status.HTTP_201_CREATED)
async def create_episode(
    episode_data: EpisodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    project_result = await db.execute(
        select(Project).where(Project.id == episode_data.project_id, Project.owner_id == current_user.id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    target_result = await db.execute(
        select(TargetApp).where(TargetApp.id == episode_data.target_app_id, TargetApp.project_id == project.id)
    )
    target = target_result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    if target.status != "ready":
        raise HTTPException(status_code=400, detail="Target is not ready")

    episode = Episode(
        project_id=episode_data.project_id,
        target_app_id=episode_data.target_app_id,
        scenario=episode_data.scenario,
        constraints=episode_data.constraints.model_dump(),
        status=EpisodeStatus.PENDING,
    )
    db.add(episode)
    await db.commit()
    await db.refresh(episode)

    redis_client = await get_redis()
    await push_episode_command(redis_client, episode.id, "start")
    # If no redis (demo mode), mark as running inline would require worker; keep pending but return

    return episode


@router.get("", response_model=EpisodeListResponse)
async def list_episodes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    project_id: Optional[UUID] = Query(None),
    target_app_id: Optional[UUID] = Query(None),
    scenario: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = select(Episode).join(Project).where(Project.owner_id == current_user.id)

    if project_id:
        query = query.where(Episode.project_id == project_id)
    if target_app_id:
        query = query.where(Episode.target_app_id == target_app_id)
    if scenario:
        query = query.where(Episode.scenario == scenario)
    if status:
        query = query.where(Episode.status == EpisodeStatus(status))

    total_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(total_query) or 0

    query = query.order_by(Episode.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    episodes = result.scalars().all()

    return EpisodeListResponse(
        items=episodes,
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit,
    )


@router.get("/{episode_id}", response_model=EpisodeDetail)
async def get_episode(
    episode_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Episode)
        .options(
            selectinload(Episode.attacks),
            selectinload(Episode.detections),
            selectinload(Episode.responses),
            selectinload(Episode.posture_score),
            selectinload(Episode.target_app)
        )
        .join(Project)
        .where(Episode.id == episode_id, Project.owner_id == current_user.id)
    )
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    attacks = [
        {
            "id": a.id,
            "technique_id": a.technique_id,
            "owasp_category": a.owasp_category,
            "success": a.success,
            "confidence": a.confidence,
            "timestamp": a.timestamp,
        }
        for a in episode.attacks
    ]
    detections = [
        {
            "id": d.id,
            "attack_id": d.attack_id,
            "detected": d.detected,
            "detection_type": d.detection_type,
            "confidence": d.confidence,
            "timestamp": d.timestamp,
        }
        for d in episode.detections
    ]
    responses = [
        {
            "id": r.id,
            "detection_id": r.detection_id,
            "action_type": r.action_type,
            "success": r.success,
            "timestamp": r.timestamp,
        }
        for r in episode.responses
    ]

    score = None
    if episode.posture_score:
        score = {
            "detection_rate": float(episode.posture_score.detection_rate),
            "mttr_seconds": episode.posture_score.mttr_seconds,
            "coverage": episode.posture_score.coverage,
            "overall_score": float(episode.posture_score.overall_score),
        }

    episode_data = {k: v for k, v in episode.__dict__.items() if not k.startswith('_') and k not in ('attacks', 'detections', 'responses', 'target_app', 'posture_score')}
    return EpisodeDetail(
        **episode_data,
        target_app={"id": episode.target_app.id, "name": episode.target_app.name, "type": episode.target_app.type.value} if episode.target_app else None,
        attacks=attacks,
        detections=detections,
        responses=responses,
        score=score,
    )


@router.get("/{episode_id}/score", response_model=PostureScoreResponse)
async def get_episode_score(
    episode_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(
        select(PostureScore)
        .join(Episode)
        .join(Project)
        .where(PostureScore.episode_id == episode_id, Project.owner_id == current_user.id)
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(status_code=404, detail="Score not found")
    return score