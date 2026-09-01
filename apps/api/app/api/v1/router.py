from fastapi import APIRouter

api_router = APIRouter()

from app.api.v1 import auth, projects, targets, episodes, compliance

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(targets.router, prefix="/targets", tags=["targets"])
api_router.include_router(episodes.router, prefix="/episodes", tags=["episodes"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])