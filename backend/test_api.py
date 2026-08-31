"""
FastAPI Endpoint Tests - Week 2, 3 & 7
Tests all registered routes: /api/health, /api/generate, /api/recompute,
/api/admin/cleanup, /api/admin/models, /api/modify
"""
import asyncio
import os
import httpx
import pytest
from dotenv import load_dotenv

load_dotenv()

from main import app

HAVE_API_KEY = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY"))

SAMPLE_CODE = """PARAMS = {
    "bracket_length": 35.0,
    "width": 20.0,
    "height": 10.0
}

from build123d import *
with BuildPart() as part:
    Box(PARAMS["bracket_length"], PARAMS["width"], PARAMS["height"])

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""

SAMPLE_PARAMS = [
    {"name": "bracket_length", "label": "Length (mm)", "type": "number", "default": 35.0, "min": 10.0, "max": 200.0, "step": 1.0},
    {"name": "width", "label": "Width (mm)", "type": "number", "default": 20.0, "min": 5.0, "max": 100.0, "step": 1.0},
    {"name": "height", "label": "Height (mm)", "type": "number", "default": 10.0, "min": 2.0, "max": 100.0, "step": 0.5},
]

@pytest.mark.asyncio
async def test_fastapi_routes_async():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:

        # 1. Health Check
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "online"
        assert "gemini_configured" in data
        print(f"[OK] GET /api/health -> status={data['status']}, gemini={data['gemini_configured']}")

        # 2. POST /api/generate
        gen_script_id = None
        gen_python_code = None
        gen_part_name = None
        gen_parameters = None
        if HAVE_API_KEY:
            gen_payload = {"prompt": "Generate a simple 40mm x 20mm x 10mm rectangular box"}
            res = await client.post("/api/generate", json=gen_payload, timeout=60.0)
            assert res.status_code == 200, f"/api/generate failed: {res.text[:300]}"
            gen_data = res.json()
            assert gen_data["status"] == "success"
            assert "script_id" in gen_data
            assert "parameters" in gen_data
            assert "mesh_url" in gen_data
            assert "model_used" in gen_data
            assert len(gen_data["parameters"]) >= 1
            gen_script_id = gen_data["script_id"]
            gen_python_code = gen_data["python_code"]
            gen_part_name = gen_data["part_name"]
            gen_parameters = gen_data["parameters"]
            print(f"[OK] POST /api/generate -> part='{gen_data['part_name']}' | model={gen_data['model_used']} | {gen_data['recomputation_time_ms']}ms | corrections={gen_data['self_correction_attempts']}")
        else:
            print("[SKIP] POST /api/generate (no API key configured)")

        # 3. POST /api/recompute
        recompute_payload = {
            "script_id": "api_test_recompute",
            "python_code": SAMPLE_CODE,
            "updated_parameters": {"bracket_length": 75.0, "width": 25.0, "height": 15.0}
        }
        res = await client.post("/api/recompute", json=recompute_payload, timeout=30.0)
        assert res.status_code == 200, f"/api/recompute failed: {res.text}"
        recomp_data = res.json()
        assert recomp_data["status"] == "success"
        dims = recomp_data.get("mesh_info", {}).get("dimensions_mm", {})
        print(f"[OK] POST /api/recompute -> {recomp_data['recomputation_time_ms']}ms | dims={dims}")

        # 4. GET /api/admin/models
        res = await client.get("/api/admin/models")
        assert res.status_code == 200
        models_data = res.json()
        assert "models" in models_data
        print(f"[OK] GET /api/admin/models -> {models_data['count']} models stored")

        # 5. POST /api/admin/cleanup
        res = await client.post("/api/admin/cleanup")
        assert res.status_code == 200
        print(f"[OK] POST /api/admin/cleanup -> removed={res.json()['removed_files']} files")

        # 6. Error handling: short prompt
        res = await client.post("/api/generate", json={"prompt": "hi"}, timeout=10.0)
        assert res.status_code == 422
        print(f"[OK] POST /api/generate (too short prompt) -> 422 Unprocessable Entity")

        # 7. POST /api/modify (Chat-to-Modify)
        if HAVE_API_KEY and gen_script_id:
            modify_payload = {
                "script_id": gen_script_id,
                "python_code": gen_python_code,
                "part_name": gen_part_name,
                "modification_prompt": "Make the box twice as tall",
                "parameters": gen_parameters,
            }
            res = await client.post("/api/modify", json=modify_payload, timeout=90.0)
            assert res.status_code == 200, f"/api/modify failed: {res.text[:400]}"
            mod_data = res.json()
            assert mod_data["status"] == "success"
            assert "script_id" in mod_data
            assert "_v1" in mod_data["script_id"]
            assert "mesh_url" in mod_data
            assert len(mod_data["parameters"]) >= 1
            print(f"[OK] POST /api/modify -> part='{mod_data['part_name']}' | script={mod_data['script_id']} | model={mod_data['model_used']} | {mod_data['recomputation_time_ms']}ms")
            # 8. GET /api/download/{script_id}/{fmt}
            res_dl = await client.get(f"/api/download/{gen_script_id}/stl")
            assert res_dl.status_code == 200
            assert len(res_dl.content) > 0
            assert "attachment" in res_dl.headers.get("content-disposition", "")
            print(f"[OK] GET /api/download/{gen_script_id}/stl -> 200 OK ({len(res_dl.content)} bytes)")
        else:
            print("[SKIP] POST /api/modify & GET /api/download (no API key or generate skipped)")

    print("\n[SUCCESS] ALL FASTAPI ASYNC ENDPOINT TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(test_fastapi_routes_async())
