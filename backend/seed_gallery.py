"""
seed_gallery.py — Seed the Community CAD Gallery with Universal Archetype Models
================================================================================
Generates real 3D geometry (STL + STEP) and populates the database with public
sample models so the community gallery displays beautiful, interactive CAD parts.
"""

import ast
import json
import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_maker, create_tables
from models.user import User
from models.project import Project, Generation
from services.auth_service import hash_password
from services.cad_runner import CADRunner
from rag_corpus.examples_universal import EXAMPLES as UNIV_EXAMPLES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_gallery")

SAMPLE_ARCHETYPES = [
    {
        "id": "universal_stepped_shaft",
        "name": "Precision Stepped Drive Shaft",
        "likes": 42,
        "forks": 8,
        "tags": ["shaft", "stepped", "lathe", "rotational", "bearing", "keyway", "mechanical"],
    },
    {
        "id": "universal_electronics_enclosure",
        "name": "Parametric Electronics Enclosure Box",
        "likes": 58,
        "forks": 14,
        "tags": ["enclosure", "box", "case", "electronics", "standoffs", "thin-wall"],
    },
    {
        "id": "universal_v_belt_pulley",
        "name": "Industrial V-Belt Drive Pulley",
        "likes": 31,
        "forks": 6,
        "tags": ["pulley", "v-belt", "drive", "transmission", "keyway", "powertrain"],
    },
    {
        "id": "universal_spur_gear",
        "name": "Involute Spur Gear with Lightening Holes",
        "likes": 77,
        "forks": 23,
        "tags": ["gear", "spur", "transmission", "powertrain", "mechanical"],
    },
    {
        "id": "universal_flanged_pipe_elbow",
        "name": "90-Degree Flanged Pipe Elbow",
        "likes": 25,
        "forks": 4,
        "tags": ["flange", "pipe", "elbow", "swept", "fluid", "piping"],
    },
    {
        "id": "universal_gusseted_l_bracket",
        "name": "Heavy-Duty Gusseted L-Bracket",
        "likes": 64,
        "forks": 19,
        "tags": ["bracket", "gusset", "angle", "structural", "mounting", "hardware"],
    },
    {
        "id": "universal_ergonomic_phone_stand",
        "name": "Ergonomic Desktop Phone & Tablet Stand",
        "likes": 51,
        "forks": 12,
        "tags": ["phone stand", "stand", "holder", "cradle", "consumer", "tablet", "ergonomic"],
    },
    {
        "id": "universal_square_to_round_duct",
        "name": "Square-to-Round HVAC Transition Duct",
        "likes": 36,
        "forks": 7,
        "tags": ["loft", "duct", "transition", "square to round", "hvac", "ventilation", "adapter"],
    },
]


def extract_parameters(code: str) -> list:
    """Extract PARAMS dictionary into CADParameter-style objects."""
    tree = ast.parse(code)
    params_dict = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PARAMS":
                    params_dict = ast.literal_eval(node.value)
                    break

    params_list = []
    for k, v in params_dict.items():
        val = float(v)
        is_int = val.is_integer()
        min_val = round(val * 0.4, 1) if val > 0 else 1.0
        max_val = round(val * 2.5, 1) if val > 0 else 50.0
        step_val = 1.0 if is_int else 0.5

        params_list.append({
            "name": k,
            "label": k.replace("_", " ").title(),
            "type": "integer" if is_int else "number",
            "default": val,
            "min": min_val,
            "max": max_val,
            "step": step_val,
            "unit": "mm" if ("dia" in k or "len" in k or "width" in k or "thick" in k or "depth" in k or "radius" in k or "height" in k) else None,
        })
    return params_list


async def seed_gallery():
    await create_tables()

    async with async_session_maker() as db:
        # 1. Ensure seed author exists
        email = "atelier@parametric-cad.internal"
        res = await db.execute(select(User).where(User.email == email))
        author = res.scalar_one_or_none()
        if not author:
            author = User(
                email=email,
                password_hash=hash_password("atelier_foundry_secret"),
                display_name="Atelier Foundry",
                plan_tier="studio",
            )
            db.add(author)
            await db.flush()
            logger.info(f"Created author user: {author.display_name} ({author.id})")

        # 2. Ensure project exists
        res = await db.execute(select(Project).where(Project.user_id == author.id))
        project = res.scalars().first()
        if not project:
            project = Project(
                user_id=author.id,
                name="Community Showcase",
                description="Verified production-grade parametric designs",
            )
            db.add(project)
            await db.flush()

        # 3. Seed models
        seeded_count = 0
        for sample in SAMPLE_ARCHETYPES:
            ex = next((x for x in UNIV_EXAMPLES if x["id"] == sample["id"]), None)
            if not ex:
                continue

            script_id = f"seed_{sample['id']}"

            # Check if already seeded
            existing = await db.execute(
                select(Generation).where(Generation.script_id == script_id)
            )
            if existing.scalar_one_or_none():
                logger.info(f"Model {sample['name']} already exists in DB, skipping.")
                continue

            logger.info(f"Compiling CAD geometry for {sample['name']}...")
            exec_res = await CADRunner.execute_script_async(
                script_id=script_id,
                python_code=ex["code"],
                design_mode="single_solid",
            )

            if exec_res.get("status") != "success":
                logger.error(f"Failed to compile {sample['name']}: {exec_res.get('stderr')}")
                continue

            params = extract_parameters(ex["code"])

            gen = Generation(
                user_id=author.id,
                project_id=project.id,
                prompt=ex["description"],
                script_id=script_id,
                part_name=sample["name"],
                description=ex["description"],
                python_code=ex["code"],
                parameters_json=json.dumps(params),
                mesh_info_json=json.dumps(exec_res.get("mesh_info", {})),
                mesh_url=exec_res.get("mesh_url"),
                step_url=exec_res.get("step_url"),
                model_used="Gemini 2.5 Flash",
                generation_time_ms=exec_res.get("recomputation_time_ms", 120),
                self_corrections=0,
                design_mode="single_solid",
                is_public=True,
                like_count=sample["likes"],
                fork_count=sample["forks"],
                tags_json=json.dumps(sample["tags"]),
            )
            db.add(gen)
            seeded_count += 1
            logger.info(f"Successfully seeded: {sample['name']} (mesh: {exec_res.get('mesh_url')})")

        await db.commit()
        logger.info(f"Seeding completed. {seeded_count} models seeded to gallery.")


if __name__ == "__main__":
    asyncio.run(seed_gallery())
