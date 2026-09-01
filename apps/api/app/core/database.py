from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
import os

from app.core.config import get_settings

settings = get_settings()

# Support both postgres (asyncpg) and sqlite (aiosqlite) for Railway/HF demo fallback
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
if db_url.startswith("postgresql://") and "+asyncpg" not in db_url and "+psycopg" not in db_url:
    # keep sync URL as is, but async needs driver
    if "postgresql+asyncpg" not in db_url:
        pass  # already handled via config

engine_kwargs = dict(
    echo=settings.APP_ENV == "development",
    poolclass=NullPool if settings.APP_ENV == "test" else None,
    pool_pre_ping=True,
)
# SQLite needs check_same_thread=False via connect_args
if "sqlite" in db_url:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(db_url, **engine_kwargs)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    # Alembic handles migrations, no need to create tables on startup
    pass


async def close_db() -> None:
    await engine.dispose()