"""
Unit tests for Chat-to-Modify request/response schemas and LLMService modification contracts.
"""
import pytest
import asyncio
from unittest.mock import patch
from schemas import CADParameter, DualOutputPayload, ModifyRequest, ModifyResponse
from services.llm_service import LLMService
from main import allocate_modify_script_id


def test_modify_request_validation():
    """Test ModifyRequest schema enforcement."""
    req = ModifyRequest(
        script_id="part_test123",
        python_code="PARAMS = {'length': 50.0}\nfrom build123d import *",
        part_name="Test Bracket",
        modification_prompt="Make it 20mm wider and add mounting holes",
        parameters=[
            CADParameter(name="length", label="Length", type="number", default=50.0, min=10.0, max=100.0, step=1.0)
        ]
    )
    assert req.script_id == "part_test123"
    assert req.part_name == "Test Bracket"
    assert len(req.parameters) == 1
    assert req.modification_prompt == "Make it 20mm wider and add mounting holes"


def test_modify_request_short_prompt_rejected():
    """Test ModifyRequest rejects empty or too-short prompts (<3 chars)."""
    with pytest.raises(Exception):
        ModifyRequest(
            script_id="part_test123",
            python_code="PARAMS = {}",
            part_name="Test",
            modification_prompt="hi"  # < 3 chars
        )


def test_modify_response_schema():
    """Test ModifyResponse construction and fields."""
    resp = ModifyResponse(
        status="success",
        script_id="part_test123_v1",
        part_name="Modified Bracket",
        description="Modified with extra width",
        python_code="PARAMS = {'length': 50.0, 'width': 30.0}\nfrom build123d import *",
        parameters=[
            CADParameter(name="length", label="Length", type="number", default=50.0, min=10.0, max=100.0, step=1.0),
            CADParameter(name="width", label="Width", type="number", default=30.0, min=10.0, max=100.0, step=1.0)
        ],
        mesh_url="/static/models/part_test123_v1.stl",
        step_url="/static/models/part_test123_v1.step",
        mesh_info={"is_watertight": True, "body_count": 1, "volume_mm3": 1500.0},
        recomputation_time_ms=120,
        model_used="gemini-3.5-flash-lite",
        modification_summary="Make it 20mm wider"
    )
    assert resp.status == "success"
    assert resp.script_id == "part_test123_v1"
    assert len(resp.parameters) == 2
    assert resp.mesh_info["is_watertight"] is True


def test_llm_service_modify_script_contract():
    """Test LLMService.modify_script properly delegates to modify_code and preserves params."""
    mock_payload = DualOutputPayload(
        part_name="Modified Part",
        description="Test description",
        python_code="PARAMS = {'length': 50.0, 'width': 40.0}\nfrom build123d import *",
        parameters=[
            CADParameter(name="length", label="Length", type="number", default=50.0, min=10.0, max=100.0, step=1.0),
            CADParameter(name="width", label="Width", type="number", default=40.0, min=10.0, max=100.0, step=1.0)
        ]
    )

    with patch.object(LLMService, '_call_with_fallback', return_value=(mock_payload, "gemini-3.5-flash-lite")):
        payload, model = LLMService.modify_script(
            python_code="PARAMS = {'length': 50.0}\nfrom build123d import *",
            modification_prompt="Add 40mm width",
            part_name="Base Part",
            parameters=[
                CADParameter(name="length", label="Length", type="number", default=50.0, min=10.0, max=100.0, step=1.0)
            ]
        )
        assert payload.part_name == "Modified Part"
        assert model == "gemini-3.5-flash-lite"
        assert len(payload.parameters) == 2
        param_names = {p.name for p in payload.parameters}
        assert "length" in param_names
        assert "width" in param_names


def test_concurrent_modify_ids_are_unique(tmp_path):
    reserved = set()
    lock = asyncio.Lock()

    async def allocate():
        return await allocate_modify_script_id("part_test", tmp_path, reserved, lock)

    async def run_pair():
        return await asyncio.gather(allocate(), allocate())

    ids = asyncio.run(run_pair())
    assert len(set(ids)) == 2
    assert all(value.startswith("part_test_v") for value in ids)

