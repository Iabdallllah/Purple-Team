from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


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
    APP_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Redis
    REDIS_URL: str
    REDIS_STREAMS_MAXLEN: int = 10000

    # ChromaDB
    CHROMADB_URL: str = "http://localhost:8000"
    CHROMADB_COLLECTION: str = "purple-episodes"

    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    # JWT
    JWT_SECRET: str
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


@lru_cache
def get_settings() -> Settings:
    return Settings()