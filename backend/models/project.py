"""
models/project.py — Project, Generation & Version Models
==========================================================
Stores CAD design projects, individual generations (prompt → 3D model),
and version history for Chat-to-Modify modifications.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Project(Base):
    """A workspace containing multiple CAD design generations."""
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="Untitled Project")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    owner = relationship("User", back_populates="projects")
    generations = relationship("Generation", back_populates="project", cascade="all, delete-orphan",
                               order_by="Generation.created_at.desc()")

    def __repr__(self):
        return f"<Project '{self.name}' ({self.id[:8]})>"


class Generation(Base):
    """A single CAD part generation from a prompt (or fork)."""
    __tablename__ = "generations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    script_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    part_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    python_code: Mapped[str] = mapped_column(Text, nullable=False)
    parameters_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    mesh_info_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    mesh_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    step_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generation_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    self_corrections: Mapped[int] = mapped_column(Integer, default=0)
    design_mode: Mapped[str] = mapped_column(String(20), default="single_solid")
    components_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    project = relationship("Project", back_populates="generations")
    versions = relationship("Version", back_populates="generation", cascade="all, delete-orphan",
                            order_by="Version.version_number")

    def __repr__(self):
        return f"<Generation '{self.part_name}' ({self.script_id})>"


class Version(Base):
    """A Chat-to-Modify version of a generation."""
    __tablename__ = "versions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    generation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generations.id"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    modification_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    script_id: Mapped[str] = mapped_column(String(100), nullable=False)
    python_code: Mapped[str] = mapped_column(Text, nullable=False)
    parameters_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    mesh_info_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    mesh_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    step_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    generation = relationship("Generation", back_populates="versions")

    def __repr__(self):
        return f"<Version v{self.version_number} of {self.generation_id[:8]}>"
