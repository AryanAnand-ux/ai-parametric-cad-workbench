"""
routes/projects.py — Project & Design Management Endpoints
============================================================
POST   /api/projects                          — Create new project
GET    /api/projects                          — List user's projects
GET    /api/projects/{id}                     — Get project details
DELETE /api/projects/{id}                     — Delete project
GET    /api/projects/{id}/generations         — List generations in project
GET    /api/generations/{gen_id}              — Get generation details
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.user import User
from models.project import Project, Generation, Version
from services.auth_service import get_current_user

logger = logging.getLogger("cad_workbench.projects")

router = APIRouter(prefix="/api", tags=["Projects"])


# ─── Schemas ────────────────────────────────────────────────────────────────

class CreateProjectRequest(BaseModel):
    name: str = Field(default="Untitled Project", min_length=1, max_length=200)
    description: str | None = None


class ProjectSummary(BaseModel):
    id: str
    name: str
    description: str | None
    generation_count: int
    created_at: str
    updated_at: str


class GenerationSummary(BaseModel):
    id: str
    script_id: str
    prompt: str
    part_name: str | None
    model_used: str | None
    generation_time_ms: int | None
    self_corrections: int
    mesh_url: str | None
    step_url: str | None
    created_at: str


class GenerationDetail(BaseModel):
    id: str
    script_id: str
    prompt: str
    part_name: str | None
    description: str | None
    python_code: str
    parameters: list | None
    mesh_info: dict | None
    mesh_url: str | None
    step_url: str | None
    model_used: str | None
    generation_time_ms: int | None
    self_corrections: int
    design_mode: str
    components: list | None
    versions: list
    created_at: str


# ─── Project CRUD ───────────────────────────────────────────────────────────

@router.post("/projects", status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: CreateProjectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new design project workspace."""
    project = Project(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    logger.info(f"[PROJECT] Created '{project.name}' for user {current_user.email}")
    return {"status": "success", "project": {"id": project.id, "name": project.name}}


@router.get("/projects")
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects owned by the current user."""
    # Subquery to count generations per project
    gen_count_subq = (
        select(Generation.project_id, func.count(Generation.id).label("gen_count"))
        .group_by(Generation.project_id)
        .subquery()
    )

    result = await db.execute(
        select(Project, gen_count_subq.c.gen_count)
        .outerjoin(gen_count_subq, Project.id == gen_count_subq.c.project_id)
        .where(Project.user_id == current_user.id)
        .order_by(Project.updated_at.desc())
    )

    projects = []
    for row in result.all():
        proj = row[0]
        count = row[1] or 0
        projects.append(ProjectSummary(
            id=proj.id,
            name=proj.name,
            description=proj.description,
            generation_count=count,
            created_at=proj.created_at.isoformat() if proj.created_at else "",
            updated_at=proj.updated_at.isoformat() if proj.updated_at else "",
        ))

    return {"status": "success", "projects": [p.model_dump() for p in projects]}


@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project details including all generations."""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Get generations
    gen_result = await db.execute(
        select(Generation)
        .where(Generation.project_id == project_id)
        .order_by(Generation.created_at.desc())
    )
    generations = gen_result.scalars().all()

    return {
        "status": "success",
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at.isoformat() if project.created_at else "",
        },
        "generations": [
            GenerationSummary(
                id=g.id,
                script_id=g.script_id,
                prompt=g.prompt,
                part_name=g.part_name,
                model_used=g.model_used,
                generation_time_ms=g.generation_time_ms,
                self_corrections=g.self_corrections,
                mesh_url=g.mesh_url,
                step_url=g.step_url,
                created_at=g.created_at.isoformat() if g.created_at else "",
            ).model_dump()
            for g in generations
        ],
    }


@router.delete("/projects/{project_id}", status_code=status.HTTP_200_OK)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and all its generations."""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    await db.delete(project)
    await db.commit()
    logger.info(f"[PROJECT] Deleted '{project.name}' (user={current_user.email})")
    return {"status": "success", "message": f"Project '{project.name}' deleted."}


# ─── Generation Detail ─────────────────────────────────────────────────────

@router.get("/generations/{generation_id}")
async def get_generation(
    generation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full details of a generation including version history."""
    result = await db.execute(
        select(Generation)
        .options(selectinload(Generation.versions))
        .where(Generation.id == generation_id, Generation.user_id == current_user.id)
    )
    gen = result.scalar_one_or_none()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found.")

    def _safe_json(text):
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            return None

    return {
        "status": "success",
        "generation": GenerationDetail(
            id=gen.id,
            script_id=gen.script_id,
            prompt=gen.prompt,
            part_name=gen.part_name,
            description=gen.description,
            python_code=gen.python_code,
            parameters=_safe_json(gen.parameters_json),
            mesh_info=_safe_json(gen.mesh_info_json),
            mesh_url=gen.mesh_url,
            step_url=gen.step_url,
            model_used=gen.model_used,
            generation_time_ms=gen.generation_time_ms,
            self_corrections=gen.self_corrections,
            design_mode=gen.design_mode,
            components=_safe_json(gen.components_json),
            versions=[
                {
                    "version_number": v.version_number,
                    "modification_prompt": v.modification_prompt,
                    "script_id": v.script_id,
                    "python_code": v.python_code,
                    "parameters": _safe_json(v.parameters_json),
                    "mesh_url": v.mesh_url,
                    "step_url": v.step_url,
                    "created_at": v.created_at.isoformat() if v.created_at else "",
                }
                for v in gen.versions
            ],
            created_at=gen.created_at.isoformat() if gen.created_at else "",
        ).model_dump(),
    }


# ─── Persistence Helpers (used by main.py) ──────────────────────────────────

async def save_generation_record(
    db: AsyncSession,
    user_id: str,
    prompt: str,
    script_id: str,
    part_name: str | None,
    description: str | None,
    python_code: str,
    parameters: list | None,
    mesh_info: dict | None,
    mesh_url: str | None,
    step_url: str | None,
    model_used: str | None,
    generation_time_ms: int | None,
    self_corrections: int,
    design_mode: str = "single",
    components: list | None = None,
    project_id: str | None = None,
) -> Optional[Generation]:
    """Persist a completed generation into the database."""
    try:
        # Find or create target project
        if not project_id:
            result = await db.execute(
                select(Project).where(Project.user_id == user_id).order_by(Project.created_at.asc())
            )
            project = result.scalars().first()
            if not project:
                project = Project(user_id=user_id, name="My Workspace", description="Default workspace")
                db.add(project)
                await db.flush()
            project_id = project.id

        generation = Generation(
            user_id=user_id,
            project_id=project_id,
            prompt=prompt,
            script_id=script_id,
            part_name=part_name,
            description=description,
            python_code=python_code,
            parameters_json=json.dumps(parameters) if parameters else None,
            mesh_info_json=json.dumps(mesh_info) if mesh_info else None,
            mesh_url=mesh_url,
            step_url=step_url,
            model_used=model_used,
            generation_time_ms=generation_time_ms,
            self_corrections=self_corrections,
            design_mode=design_mode,
            components_json=json.dumps(components) if components else None,
        )
        db.add(generation)
        await db.commit()
        await db.refresh(generation)
        return generation
    except Exception as e:
        logger.error(f"[DB] Failed to persist generation: {e}")
        await db.rollback()
        return None


async def save_version_record(
    db: AsyncSession,
    user_id: str,
    base_script_id: str,
    new_script_id: str,
    modification_prompt: str,
    python_code: str,
    parameters: list | None = None,
    mesh_url: str | None = None,
    step_url: str | None = None,
    mesh_info: dict | None = None,
) -> Optional[Version]:
    """Persist a modified version linked to base generation."""
    try:
        # Find parent generation by base_script_id (or root part ID)
        root_id = base_script_id.split("_v")[0]
        result = await db.execute(
            select(Generation).where(
                (Generation.script_id == base_script_id) | (Generation.script_id == root_id),
                Generation.user_id == user_id
            ).order_by(Generation.created_at.desc())
        )
        gen = result.scalars().first()
        if not gen:
            return None

        # Determine version number
        v_count_res = await db.execute(
            select(func.count(Version.id)).where(Version.generation_id == gen.id)
        )
        v_num = (v_count_res.scalar() or 0) + 1

        version = Version(
            generation_id=gen.id,
            version_number=v_num,
            modification_prompt=modification_prompt,
            script_id=new_script_id,
            python_code=python_code,
            parameters_json=json.dumps(parameters) if parameters else None,
            mesh_url=mesh_url,
            step_url=step_url,
        )
        db.add(version)
        await db.commit()
        return version
    except Exception as e:
        logger.error(f"[DB] Failed to persist version: {e}")
        await db.rollback()
        return None
