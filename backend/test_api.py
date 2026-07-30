import asyncio
import httpx
from main import app

async def test_fastapi_routes_async():
    # Use AsyncClient with ASGITransport for testing async FastAPI endpoints cleanly
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Healthcheck
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "online"
        print(f"[OK] GET /api/health -> {data['status']}")

        # 2. Execute Test Endpoint
        test_payload = {
            "script_id": "api_part_w2",
            "python_code": """import trimesh
PARAMS = {"bracket_length": 35.0, "width": 20.0, "height": 10.0}
mesh = trimesh.creation.box(extents=[PARAMS["bracket_length"], PARAMS["width"], PARAMS["height"]])
mesh.export(OUTPUT_STL)
""",
            "parameters": {"bracket_length": 35.0, "width": 20.0, "height": 10.0}
        }
        
        res = await client.post("/api/execute-test", json=test_payload)
        assert res.status_code == 200, f"Execute test failed: {res.text}"
        exec_data = res.json()
        assert exec_data["status"] == "success"
        print(f"[OK] POST /api/execute-test -> Executed in {exec_data['recomputation_time_ms']} ms")
        print(f"     Mesh URL: {exec_data['mesh_url']}")

        # 3. Recompute Endpoint
        recompute_payload = {
            "script_id": "api_part_w2",
            "python_code": test_payload["python_code"],
            "updated_parameters": {"bracket_length": 75.0, "width": 25.0, "height": 15.0}
        }
        
        res = await client.post("/api/recompute", json=recompute_payload)
        assert res.status_code == 200, f"Recompute failed: {res.text}"
        recomp_data = res.json()
        assert recomp_data["status"] == "success"
        print(f"[OK] POST /api/recompute -> Recomputed in {recomp_data['recomputation_time_ms']} ms")
        print(f"     Dimensions: {recomp_data['mesh_info']['dimensions_mm']}")

        # 4. Admin Cleanup Endpoint
        res = await client.post("/api/admin/cleanup")
        assert res.status_code == 200
        print(f"[OK] POST /api/admin/cleanup -> Removed files: {res.json()['removed_files']}")

    print("\n[SUCCESS] ALL FASTAPI ASYNC ENDPOINT TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(test_fastapi_routes_async())
