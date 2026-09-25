"""
routes/gallery.py — Public Design Gallery
==========================================
Endpoints for discovering, publishing, liking, and forking public CAD designs.

Routes:
  GET  /api/gallery              — Paginated public gallery with search + filter
  POST /api/designs/{id}/publish — Make a design publicly visible (owner only)
  POST /api/designs/{id}/unpublish — Remove from gallery (owner only)
  POST /api/designs/{id}/like    — Like a public design (authenticated)
  POST /api/designs/{id}/fork    — Clone a public design into the user's workspace
"""

import json
import uuid
import logging
from typing import Optional, List, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy import select, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.project import Generation, Project
from models.user import User
from services.auth_service import get_current_user, get_optional_user

logger = logging.getLogger("cad_workbench.gallery")

gallery_router = APIRouter(prefix="/api", tags=["gallery"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generation_to_gallery_card(g: Generation, author_name: str = "Anonymous") -> dict:
    """Serialize a Generation to a public gallery card."""
    tags = json.loads(g.tags_json) if g.tags_json else []
    mesh_info = json.loads(g.mesh_info_json) if g.mesh_info_json else {}
    params = json.loads(g.parameters_json) if g.parameters_json else []

    return {
        "id": g.id,
        "script_id": g.script_id,
        "part_name": g.part_name or "Untitled Part",
        "description": g.description or "",
        "prompt": g.prompt[:200] + ("…" if len(g.prompt) > 200 else ""),
        "tags": tags,
        "like_count": g.like_count,
        "fork_count": g.fork_count,
        "author": author_name,
        "created_at": g.created_at.isoformat(),
        "mesh_url": g.mesh_url,
        "step_url": g.step_url,
        "parameter_count": len(params),
        "design_mode": g.design_mode,
        "mesh_info": {
            "dimensions_mm": mesh_info.get("dimensions_mm", {}),
            "volume_mm3": mesh_info.get("volume_mm3"),
            "face_count": mesh_info.get("face_count"),
            "is_watertight": mesh_info.get("is_watertight"),
        },
        "forked_from": g.forked_from,
    }


# ---------------------------------------------------------------------------
# GET /api/gallery — Browse public designs
# ---------------------------------------------------------------------------

@gallery_router.get("/gallery")
async def browse_gallery(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=50, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by part name or description"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    sort_by: str = Query("recent", description="Sort by: recent | popular | most_forked"),
    db: AsyncSession = Depends(get_db),
):
    """Paginated public design gallery with optional search and tag filtering."""
    query = select(Generation).where(Generation.is_public == True)  # noqa: E712

    # Search filter
    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(Generation.part_name).like(search_term),
                func.lower(Generation.description).like(search_term),
                func.lower(Generation.prompt).like(search_term),
            )
        )

    # Tag filter
    if tag:
        query = query.where(Generation.tags_json.like(f'%"{tag}"%'))

    # Sorting
    if sort_by == "popular":
        query = query.order_by(desc(Generation.like_count), desc(Generation.created_at))
    elif sort_by == "most_forked":
        query = query.order_by(desc(Generation.fork_count), desc(Generation.created_at))
    else:  # recent
        query = query.order_by(desc(Generation.created_at))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    query = query.limit(per_page).offset(offset)
    result = await db.execute(query)
    generations = result.scalars().all()

    # Fetch author names (batch lookup by user_id)
    user_ids = list({g.user_id for g in generations})
    if user_ids:
        user_result = await db.execute(
            select(User.id, User.display_name, User.email).where(User.id.in_(user_ids))
        )
        user_map = {
            row.id: (row.display_name or row.email.split("@")[0])
            for row in user_result.all()
        }
    else:
        user_map = {}

    cards = [
        _generation_to_gallery_card(g, user_map.get(g.user_id, "Anonymous"))
        for g in generations
    ]

    return {
        "items": cards,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, (total + per_page - 1) // per_page),
    }


# ---------------------------------------------------------------------------
# POST /api/designs/{id}/publish — Publish a design
# ---------------------------------------------------------------------------

@gallery_router.post("/designs/{generation_id}/publish")
async def publish_design(
    generation_id: str,
    payload: Optional[Any] = Body(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Make a design publicly visible in the gallery (owner only)."""
    result = await db.execute(
        select(Generation).where(
            Generation.id == generation_id,
            Generation.user_id == current_user.id,
        )
    )
    gen = result.scalar_one_or_none()
    if not gen:
        raise HTTPException(status_code=404, detail="Design not found or access denied")

    gen.is_public = True

    # Support tags passed as list ["a", "b"] or dict {"tags": ["a", "b"]}
    tags = None
    if isinstance(payload, list):
        tags = [str(t).strip().lower() for t in payload if t]
    elif isinstance(payload, dict):
        raw_tags = payload.get("tags")
        if isinstance(raw_tags, list):
            tags = [str(t).strip().lower() for t in raw_tags if t]

    if tags is not None:
        gen.tags_json = json.dumps(tags[:10])
    await db.commit()

    logger.info(f"[Gallery] Published design {generation_id} by user {current_user.id}")
    return {"message": "Design published to gallery", "id": generation_id, "is_public": True}


# ---------------------------------------------------------------------------
# POST /api/designs/{id}/unpublish — Unpublish a design
# ---------------------------------------------------------------------------

@gallery_router.post("/designs/{generation_id}/unpublish")
async def unpublish_design(
    generation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a design from the public gallery (owner only)."""
    result = await db.execute(
        select(Generation).where(
            Generation.id == generation_id,
            Generation.user_id == current_user.id,
        )
    )
    gen = result.scalar_one_or_none()
    if not gen:
        raise HTTPException(status_code=404, detail="Design not found or access denied")

    gen.is_public = False
    await db.commit()
    return {"message": "Design removed from gallery", "id": generation_id}


# ---------------------------------------------------------------------------
# POST /api/designs/{id}/like — Like a public design
# ---------------------------------------------------------------------------

@gallery_router.post("/designs/{generation_id}/like")
async def like_design(
    generation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Increment like count on a public design."""
    result = await db.execute(
        select(Generation).where(
            Generation.id == generation_id,
            Generation.is_public == True,  # noqa: E712
        )
    )
    gen = result.scalar_one_or_none()
    if not gen:
        raise HTTPException(status_code=404, detail="Public design not found")

    gen.like_count = (gen.like_count or 0) + 1
    await db.commit()
    return {"like_count": gen.like_count}


# ---------------------------------------------------------------------------
# POST /api/designs/{id}/fork — Fork a public design into your workspace
# ---------------------------------------------------------------------------

@gallery_router.post("/designs/{generation_id}/fork")
async def fork_design(
    generation_id: str,
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Clone a public design into the authenticated user's workspace.
    If project_id is not provided, creates a new workspace for the fork.
    """
    # Fetch original
    result = await db.execute(
        select(Generation).where(
            Generation.id == generation_id,
            Generation.is_public == True,  # noqa: E712
        )
    )
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404, detail="Public design not found")

    # Resolve or create target project
    if project_id:
        proj_result = await db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.user_id == current_user.id,
            )
        )
        project = proj_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Target project not found")
    else:
        # Auto-create a workspace named after the forked design
        project = Project(
            user_id=current_user.id,
            name=f"Fork of {original.part_name or 'Untitled'}",
            description=f"Forked from community design #{generation_id[:8]}",
        )
        db.add(project)
        await db.flush()

    # Create forked generation record (new id, new script_id suffix)
    forked_script_id = f"{original.script_id}_fork_{str(uuid.uuid4())[:6]}"
    fork = Generation(
        project_id=project.id,
        user_id=current_user.id,
        prompt=original.prompt,
        script_id=forked_script_id,
        part_name=f"{original.part_name or 'Untitled'} (fork)",
        description=original.description,
        python_code=original.python_code,
        parameters_json=original.parameters_json,
        mesh_info_json=original.mesh_info_json,
        mesh_url=original.mesh_url,
        step_url=original.step_url,
        model_used=original.model_used,
        design_mode=original.design_mode,
        components_json=original.components_json,
        tags_json=original.tags_json,
        is_public=False,  # forks start private
        forked_from=generation_id,
    )
    db.add(fork)

    # Increment fork count on original
    original.fork_count = (original.fork_count or 0) + 1
    await db.commit()
    await db.refresh(fork)

    logger.info(
        f"[Gallery] User {current_user.id} forked design {generation_id} "
        f"→ {fork.id} into project {project.id}"
    )
    return {
        "message": "Design forked into your workspace",
        "fork_id": fork.id,
        "project_id": project.id,
        "script_id": forked_script_id,
        "part_name": fork.part_name,
    }
