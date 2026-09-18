"""
models/user.py — User Account Model
=====================================
Stores user credentials, profile info, and plan tier.
Passwords are hashed with bcrypt via passlib.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False, default="Engineer")
    plan_tier: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    api_key: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True, nullable=True, default=None
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    generations_today: Mapped[int] = mapped_column(default=0)
    last_generation_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email} ({self.plan_tier})>"
