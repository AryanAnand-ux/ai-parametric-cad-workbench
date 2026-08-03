"""
FastAPI Endpoint Tests — Week 2 & 3
Tests all registered routes: /api/health, /api/generate, /api/recompute,
/api/admin/cleanup, /api/admin/models
"""
import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

from main import app

HAVE_API_KEY = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY"))

SAMPLE_CODE = """PARAMS = {
    "bracket_length": 35.0,
    "width": 20.0,
    "height": 10.0
}

import trimesh
mesh = trimesh.creation.box(extents=[PARAMS["bracket_length"], PARAMS["width"], PARAMS["height"]])
mesh.export(OUTPUT_STL)
"""

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

        # 2. POST /api/generate (requires API key)
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
            print(f"[OK] POST /api/generate -> part='{gen_data['part_name']}' | "
                  f"model={gen_data['model_used']} | "
                  f"{gen_data['recomputation_time_ms']}ms | "
                  f"corrections={gen_data['self_correction_attempts']}")
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
        assert res.status_code == 422   # Pydantic min_length=5 validation
        print(f"[OK] POST /api/generate (too short prompt) -> 422 Unprocessable Entity")

    print("\n[SUCCESS] ALL FASTAPI ASYNC ENDPOINT TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(test_fastapi_routes_async())
