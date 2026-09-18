"""
database.py — Async SQLAlchemy Database Engine & Session Management
===================================================================
Uses SQLite (aiosqlite) for development, easily swappable to PostgreSQL
by changing DATABASE_URL in .env to:
  DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname
"""

import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from config import BASE_DIR

# Default: SQLite in the backend directory (zero-config dev setup)
# Production: set DATABASE_URL env var to PostgreSQL
_default_db_path = BASE_DIR / "cad_workbench.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{_default_db_path}")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    # SQLite needs connect_args for concurrent access
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


async def get_db():
    """FastAPI dependency: yields an async database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Create all tables (used on startup). Safe to call multiple times."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
