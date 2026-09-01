from datetime import datetime, UTC, timedelta
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_active_user
from app.models.project import Project
from app.services.compliance import generate_compliance_report, ComplianceFramework

router = APIRouter()


@router.get("/projects/{project_id}/compliance/reports")
async def list_compliance_reports(
    project_id: UUID,
    framework: Optional[str] = Query(None, regex="^(soc2|iso27001|nist_csf)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """List generated compliance reports for a project"""
    # Verify project ownership
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # TODO: Implement report storage and listing
    return {"items": [], "total": 0, "page": page, "limit": limit}


@router.post("/projects/{project_id}/compliance/reports")
async def generate_compliance_report_endpoint(
    project_id: UUID,
    framework: str = Query(..., regex="^(soc2|iso27001|nist_csf)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Generate a compliance report for a project"""
    # Verify project ownership
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Default to last 90 days
    end = end_date or datetime.now(UTC)
    start = start_date or (end - timedelta(days=90))

    try:
        report = await generate_compliance_report(
            db=db,
            project_id=project_id,
            framework=framework,
            start_date=start,
            end_date=end,
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/projects/{project_id}/compliance/reports/{report_id}")
async def get_compliance_report(
    project_id: UUID,
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get a specific compliance report"""
    # TODO: Implement report storage and retrieval
    raise HTTPException(status_code=501, detail="Report retrieval not implemented")


@router.get("/projects/{project_id}/compliance/dashboard")
async def get_compliance_dashboard(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get compliance dashboard data for a project"""
    # Verify project ownership
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get latest posture scores
    from app.models.posture_score import PostureScore
    from app.models.episode import Episode
    
    result = await db.execute(
        select(PostureScore)
        .join(Episode)
        .where(Episode.project_id == project_id)
        .order_by(PostureScore.calculated_at.desc())
        .limit(10)
    )
    scores = result.scalars().all()

    return {
        "project": project.name,
        "latest_score": float(scores[0].overall_score) if scores else 0,
        "trend": scores[0].trend if scores else "stable",
        "frameworks": {
            "soc2": {"ready": True, "last_generated": None},
            "iso27001": {"ready": True, "last_generated": None},
            "nist_csf": {"ready": True, "last_generated": None},
        },
        "recent_scores": [
            {
                "score": float(s.overall_score),
                "date": s.calculated_at.isoformat(),
                "trend": s.trend,
            }
            for s in scores
        ],
    }