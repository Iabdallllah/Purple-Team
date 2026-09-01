from typing import Optional
from uuid import UUID
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.api.deps import get_db, get_current_active_user
from app.models.posture_score import PostureScore
from app.models.episode import Episode
from app.models.project import Project

router = APIRouter()

@router.get("/summary")
async def get_posture_summary(
    project_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    # Base query filter by owner
    base = select(PostureScore).join(Episode, PostureScore.episode_id == Episode.id).join(Project, Episode.project_id == Project.id).where(Project.owner_id == current_user.id)
    if project_id:
        # verify ownership
        proj = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id))
        if not proj.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Project not found")
        base = base.where(Episode.project_id == project_id)

    result = await db.execute(base.order_by(desc(PostureScore.calculated_at)))
    scores = result.scalars().all()

    if not scores:
        # No scores yet: return empty but meaningful
        # also get total episodes count
        ep_q = select(func.count(Episode.id)).join(Project, Episode.project_id == Project.id).where(Project.owner_id == current_user.id)
        if project_id:
            ep_q = ep_q.where(Episode.project_id == project_id)
        total_episodes = await db.scalar(ep_q) or 0
        return {
            "currentScore": 0,
            "previousScore": 0,
            "trend": "stable",
            "detectionRate": 0,
            "mttrSeconds": 0,
            "coverageByCategory": {f"A0{i}": 0 for i in range(1, 11) if i != 0} | {"A10": 0},
            "totalEpisodes": total_episodes,
            "lastCalculatedAt": None,
            "history": [],
        }

    latest = scores[0]
    previous = scores[1] if len(scores) > 1 else latest
    # aggregate coverage by OWASP category: average coverage per category across all scores
    # coverage is dict per score: {A01: {coverage:0.5,...}, ...}
    cats = [f"A0{i}" for i in range(1, 10)] + ["A10"]
    coverage_sum = {c: 0.0 for c in cats}
    count = len(scores)
    for s in scores:
        cov = s.coverage or {}
        for c in cats:
            val = cov.get(c)
            if isinstance(val, dict):
                coverage_sum[c] += float(val.get("coverage", 0))
            elif isinstance(val, (int, float)):
                coverage_sum[c] += float(val)
    coverage_avg = {c: round(coverage_sum[c]/count, 3) for c in cats}

    # detectionRate and mttr: average across recent, but current is latest
    avg_detection = sum(float(s.detection_rate) for s in scores) / count
    avg_mttr = sum(int(s.mttr_seconds) for s in scores) / count if count else 0

    # history for chart: last 10 sorted asc
    hist_scores = list(reversed(scores[:10]))
    history = [
        {"episode": i+1, "detectionRate": float(s.detection_rate), "mttr": int(s.mttr_seconds), "overall": float(s.overall_score), "calculatedAt": s.calculated_at.isoformat()}
        for i, s in enumerate(hist_scores)
    ]

    # total episodes for user
    ep_q = select(func.count(Episode.id)).join(Project, Episode.project_id == Project.id).where(Project.owner_id == current_user.id)
    if project_id:
        ep_q = ep_q.where(Episode.project_id == project_id)
    total_episodes = await db.scalar(ep_q) or 0

    return {
        "currentScore": float(latest.overall_score),
        "previousScore": float(previous.overall_score) if previous else float(latest.overall_score),
        "trend": latest.trend or "stable",
        "detectionRate": float(latest.detection_rate),
        "mttrSeconds": int(latest.mttr_seconds),
        "avgDetectionRate": round(avg_detection, 3),
        "avgMttr": round(avg_mttr, 1),
        "coverageByCategory": coverage_avg,
        "totalEpisodes": total_episodes,
        "lastCalculatedAt": latest.calculated_at.isoformat(),
        "history": history,
    }

@router.get("/trend")
async def get_posture_trend(
    project_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    base = select(PostureScore).join(Episode, PostureScore.episode_id == Episode.id).join(Project, Episode.project_id == Project.id).where(Project.owner_id == current_user.id)
    if project_id:
        base = base.where(Episode.project_id == project_id)
    result = await db.execute(base.order_by(desc(PostureScore.calculated_at)).limit(limit))
    scores = result.scalars().all()
    scores = list(reversed(scores))
    return {
        "items": [
            {
                "episode_id": str(s.episode_id),
                "overall_score": float(s.overall_score),
                "detection_rate": float(s.detection_rate),
                "mttr_seconds": int(s.mttr_seconds),
                "coverage": s.coverage,
                "calculated_at": s.calculated_at.isoformat(),
                "trend": s.trend,
            } for s in scores
        ],
        "total": len(scores),
    }
