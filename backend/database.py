"""
database.py — Async SQLAlchemy Database Engine & Session Management
===================================================================
Uses SQLite (aiosqlite) for development, easily swappable to PostgreSQL
by changing DATABASE_URL in .env to:
  DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname
"""

import os
import logging
from pathlib import Path
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from config import BASE_DIR

logger = logging.getLogger("cad_workbench.database")

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

if "sqlite" in DATABASE_URL:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, _connection_record):
        """WAL mode + busy timeout so concurrent generate/gallery writes don't hit 'database is locked'."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

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

        # Automatic SQLite migration for newly added columns
        if "sqlite" in DATABASE_URL:
            def _migrate_sqlite_columns(sync_conn):
                cursor = sync_conn.connection.cursor()
                try:
                    cursor.execute("PRAGMA table_info(generations)")
                    existing = {row[1] for row in cursor.fetchall()}
                    if existing:  # Table exists
                        migrations = [
                            ("is_public", "INTEGER DEFAULT 0"),
                            ("like_count", "INTEGER DEFAULT 0"),
                            ("fork_count", "INTEGER DEFAULT 0"),
                            ("tags_json", "TEXT"),
                            ("forked_from", "VARCHAR(36)"),
                        ]
                        for col_name, col_def in migrations:
                            if col_name not in existing:
                                cursor.execute(f"ALTER TABLE generations ADD COLUMN {col_name} {col_def}")
                except Exception as e:
                    # Never swallow migration failures silently — a half-migrated
                    # schema causes confusing errors later. Production uses Alembic.
                    logger.error(f"[DB] SQLite auto-migration failed: {e}")
                    raise
            await conn.run_sync(_migrate_sqlite_columns)
