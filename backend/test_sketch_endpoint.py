"""
Tests for POST /api/generate/sketch endpoint.
All vision, LLM, and CAD runner calls are patched — no network or file I/O required.
Run with: cd backend && .\\venv\\Scripts\\python.exe -m pytest test_sketch_endpoint.py -v --tb=short
"""
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from main import app

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

# Minimal 4-byte PNG header so the size check (>= 64) is satisfied
_VALID_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 60
_VALID_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 60
_VALID_WEBP = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 52

_FAKE_PARSED = MagicMock(
    visual_interpretation="Rectangular block 100x50x30mm with 5mm chamfer",
    identified_parameters={"length": 100.0, "width": 50.0, "height": 30.0},
    derived_prompt=(
        "Rectangular block 100mm × 50mm × 30mm with 5mm chamfer on all top "
        "edges, 4 corner through-holes M4 diameter"
    ),
)

_FAKE_DUAL_OUTPUT = MagicMock(
    part_name="Test Block",
    description="A test rectangular block",
    python_code=(
        "PARAMS = {'length': 100, 'width': 50, 'height': 30}\n"
        "from build123d import *\n"
        "with BuildPart() as p:\n"
        "    Box(PARAMS['length'], PARAMS['width'], PARAMS['height'])\n"
    ),
    parameters=[],
    design_mode="single_solid",
    components=None,
)

_FAKE_EXEC = {
    "status": "success",
    "mesh_url": "/static/models/sketch_abc123.stl",
    "step_url": "/static/models/sketch_abc123.step",
    "obj_url": None,
    "glb_url": None,
    "mesh_info": {"is_valid": True, "volume_mm3": 150000.0},
    "recomputation_time_ms": 1234,
    "error_type": None,
    "stderr": "",
}


# ---------------------------------------------------------------------------
# Validation / guard tests (no mocking needed)
# ---------------------------------------------------------------------------

async def test_sketch_missing_image_field_422():
    """Omitting the `image` field must return 422 Unprocessable Entity."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/generate/sketch")
    assert r.status_code == 422


async def test_sketch_unsupported_mime_415():
    """Uploading a GIF must be rejected with 415 Unsupported Media Type."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            "/api/generate/sketch",
            files={"image": ("drawing.gif", b"GIF89a" + b"\x00" * 60, "image/gif")},
        )
    assert r.status_code == 415
    assert "PNG" in r.json()["detail"] or "JPEG" in r.json()["detail"]


async def test_sketch_empty_file_400():
    """A near-empty file (< 64 bytes) must be rejected with 400."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            "/api/generate/sketch",
            files={"image": ("drawing.png", b"\x89PNG", "image/png")},
        )
    assert r.status_code == 400


async def test_sketch_no_api_key_503(monkeypatch):
    """Without GEMINI_API_KEY the endpoint must return 503."""
    monkeypatch.setattr("main.GEMINI_API_KEY", "")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            "/api/generate/sketch",
            files={"image": ("s.png", _VALID_PNG, "image/png")},
        )
    assert r.status_code == 503
    assert "GEMINI_API_KEY" in r.json()["detail"]


# ---------------------------------------------------------------------------
# Happy-path test
# ---------------------------------------------------------------------------

@patch("services.vision_service.VisionService.parse_sketch", return_value=_FAKE_PARSED)
@patch("services.llm_service.LLMService.generate_dual_output", return_value=(_FAKE_DUAL_OUTPUT, "gemini-2.5-flash"))
@patch("services.cad_runner.CADRunner.execute_script_async", new_callable=AsyncMock, return_value=_FAKE_EXEC)
async def test_sketch_happy_path_png(mock_cad, mock_llm, mock_vision, monkeypatch):
    """PNG upload flows through vision → LLM → CAD and returns GenerateResponse."""
    monkeypatch.setattr("main.GEMINI_API_KEY", "fake-key-for-testing")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            "/api/generate/sketch",
            files={"image": ("sketch.png", _VALID_PNG, "image/png")},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["script_id"].startswith("sketch_")
    assert body["part_name"] == "Test Block"
    assert body["mesh_url"] == "/static/models/sketch_abc123.stl"
    mock_vision.assert_called_once()
    mock_llm.assert_called_once()
    mock_cad.assert_called_once()


@patch("services.vision_service.VisionService.parse_sketch", return_value=_FAKE_PARSED)
@patch("services.llm_service.LLMService.generate_dual_output", return_value=(_FAKE_DUAL_OUTPUT, "gemini-2.5-flash"))
@patch("services.cad_runner.CADRunner.execute_script_async", new_callable=AsyncMock, return_value=_FAKE_EXEC)
async def test_sketch_happy_path_jpeg(mock_cad, mock_llm, mock_vision, monkeypatch):
    """JPEG upload is accepted identically to PNG."""
    monkeypatch.setattr("main.GEMINI_API_KEY", "fake-key-for-testing")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            "/api/generate/sketch",
            files={"image": ("sketch.jpg", _VALID_JPEG, "image/jpeg")},
        )
    assert r.status_code == 200
    assert r.json()["status"] == "success"


# ---------------------------------------------------------------------------
# Vision failure test
# ---------------------------------------------------------------------------

@patch(
    "services.vision_service.VisionService.parse_sketch",
    side_effect=ValueError("Vision model returned non-JSON"),
)
async def test_sketch_vision_failure_502(mock_vision, monkeypatch):
    """A Vision parse failure must surface as 502 Bad Gateway."""
    monkeypatch.setattr("main.GEMINI_API_KEY", "fake-key-for-testing")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            "/api/generate/sketch",
            files={"image": ("sketch.png", _VALID_PNG, "image/png")},
        )
    assert r.status_code == 502
    assert "vision" in r.json()["detail"].lower() or "parsing" in r.json()["detail"].lower()


@patch("services.vision_service.VisionService.parse_sketch", return_value=_FAKE_PARSED)
@patch("services.llm_service.LLMService.generate_dual_output", return_value=(_FAKE_DUAL_OUTPUT, "gemini-2.5-flash"))
@patch("services.cad_runner.CADRunner.execute_script_async", new_callable=AsyncMock, return_value=_FAKE_EXEC)
async def test_sketch_with_optional_prompt(mock_cad, mock_llm, mock_vision, monkeypatch):
    """Optional prompt text from user is forwarded to VisionService.parse_sketch."""
    monkeypatch.setattr("main.GEMINI_API_KEY", "fake-key-for-testing")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            "/api/generate/sketch",
            files={"image": ("sketch.png", _VALID_PNG, "image/png")},
            data={"prompt": "Focus on model 2: make base 50mm wider"},
        )
    assert r.status_code == 200
    assert r.json()["status"] == "success"
    # Verify mock_vision was called with the user prompt
    mock_vision.assert_called_once()
    call_args = mock_vision.call_args[0]
    assert call_args[2] == "Focus on model 2: make base 50mm wider"

