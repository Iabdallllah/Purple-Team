from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    # Railway provides PORT env var dynamically; fall back to 8000
    APP_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # Database - defaults to sqlite for Railway demo if not set (Railway Postgres will override via env)
    DATABASE_URL: str = "sqlite+aiosqlite:///./purple.db"
    DATABASE_URL_SYNC: str = "sqlite:///./purple.db"
    # Also support Railway's DATABASE_URL env (postgres) - if set, it will be used
    # For backwards compat, also check for DATABASE_URL_SYNC being postgres when DATABASE_URL is postgres

    # Redis - defaults to localhost for dev, memory mock will be used if unavailable
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_STREAMS_MAXLEN: int = 10000

    # ChromaDB
    CHROMADB_URL: str = "http://localhost:8000"
    CHROMADB_COLLECTION: str = "purple-episodes"

    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    # JWT - default for demo, override in production via env
    JWT_SECRET: str = "dev-secret-key-32-chars-minimum-for-demo-only-please-change"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Sandbox
    DOCKER_HOST: str = "unix:///var/run/docker.sock"
    SANDBOX_NETWORK: str = "purple-network"
    SANDBOX_DEFAULT_TIMEOUT: int = 300
    SANDBOX_MAX_CONTAINERS: int = 10
    SANDBOX_CPU_LIMIT: str = "2"
    SANDBOX_MEMORY_LIMIT: str = "4g"

    # Target Apps
    JUICE_SHOP_URL: str = "http://localhost:3001"
    DVWA_URL: str = "http://localhost:3002"

    # Logging
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "json"

    def model_post_init(self, __context):
        # Handle Railway's DATABASE_URL (postgres) -> derive SYNC URL if not set
        # Railway provides DATABASE_URL as postgres://..., but we need async and sync variants
        # If DATABASE_URL is postgres and SYNC is still sqlite default, derive it
        if self.DATABASE_URL.startswith("postgres") and self.DATABASE_URL_SYNC.startswith("sqlite"):
            # Derive sync URL from async URL: postgresql+asyncpg -> postgresql
            sync_url = self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").replace("postgres://", "postgresql://")
            object.__setattr__(self, "DATABASE_URL_SYNC", sync_url)
        # Also handle PORT env var from Railway (dynamic port)
        port_env = os.getenv("PORT")
        if port_env and port_env.isdigit():
            object.__setattr__(self, "APP_PORT", int(port_env))


@lru_cache
def get_settings() -> Settings:
    return Settings()