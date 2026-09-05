"""Regression tests for recompute result validation."""

import pytest
from fastapi import HTTPException

import main
from schemas import RecomputeRequest


@pytest.mark.asyncio
async def test_recompute_rejects_invalid_mesh(monkeypatch):
    async def fake_execute_script_async(**kwargs):
        return {
            "status": "success",
            "mesh_url": "/static/models/example.stl",
            "step_url": "/static/models/example.step",
            "mesh_info": {
                "is_valid": False,
                "geometry_warnings": ["Mesh is not watertight"],
            },
        }

    monkeypatch.setattr(main.CADRunner, "execute_script_async", fake_execute_script_async)

    with pytest.raises(HTTPException) as raised:
        await main.recompute_part(RecomputeRequest(
            script_id="part_example",
            python_code="PARAMS = {}",
            updated_parameters={},
        ))

    assert raised.value.status_code == 400
    assert "invalid" in str(raised.value.detail).lower()


@pytest.mark.asyncio
async def test_recompute_uses_unique_execution_artifact_id(monkeypatch):
    execution_ids = []

    async def fake_execute_script_async(**kwargs):
        execution_ids.append(kwargs["script_id"])
        return {
            "status": "success",
            "mesh_url": f"/static/models/{kwargs['script_id']}.stl",
            "step_url": f"/static/models/{kwargs['script_id']}.step",
            "mesh_info": {"is_valid": True, "dimensions_mm": {}},
        }

    monkeypatch.setattr(main.CADRunner, "execute_script_async", fake_execute_script_async)
    payload = RecomputeRequest(
        script_id="part_example",
        python_code="PARAMS = {}",
        updated_parameters={},
    )

    await main.recompute_part(payload)
    await main.recompute_part(payload)

    assert len(execution_ids) == 2
    assert execution_ids[0] != execution_ids[1]
    assert all(value.startswith("part_example_recomputed_") for value in execution_ids)