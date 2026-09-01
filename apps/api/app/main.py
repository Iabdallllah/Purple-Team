from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.core.logging import setup_logging, get_logger
from app.api.v1.router import api_router
from app.workers.socket_server import socket_app
from app.monitoring.metrics import (
    setup_instrumentator,
    metrics_endpoint,
    update_system_metrics,
    record_episode_start,
)

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting Purple Platform API", env=settings.APP_ENV)
    await init_db()
    
    # Start background task for system metrics
    import asyncio
    from app.monitoring.metrics import update_system_metrics
    metrics_task = asyncio.create_task(update_system_metrics())
    
    yield
    
    metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        pass
    
    await close_db()
    logger.info("Shutting down Purple Platform API")


app = FastAPI(
    title="Purple Platform API",
    description="Autonomous Purple Team Platform API",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_PREFIX)

# Mount Socket.IO app
app.mount("/socket.io", socket_app)

# Setup Prometheus instrumentation
setup_instrumentator(app)

# Custom metrics endpoint with all custom metrics
app.add_route("/metrics", metrics_endpoint, methods=["GET"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "purple-api"}

@app.get("/")
async def root():
    return {
        "service": "purple-api",
        "status": "healthy",
        "docs": "/docs",
        "health": "/health",
        "api_prefix": settings.API_PREFIX,
    }
