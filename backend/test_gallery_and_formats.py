"""
Test suite for Gallery, Telemetry Metrics, and Extended Export Formats
"""
import pytest
import httpx
from main import app
from database import create_tables

@pytest.fixture(autouse=True)
async def init_db():
    await create_tables()

@pytest.mark.asyncio
async def test_gallery_and_metrics_endpoints():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Test /api/metrics
        res = await client.get("/api/metrics")
        assert res.status_code == 200
        metrics = res.json()
        assert "total_requests" in metrics
        assert "total_errors" in metrics
        assert "cad_generations" in metrics
        assert "latency_ms" in metrics

        # 2. Test /api/gallery listing
        res = await client.get("/api/gallery")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert isinstance(data["items"], list)

        # 3. Test /api/gallery search & sort
        res = await client.get("/api/gallery?search=bracket&sort_by=popular")
        assert res.status_code == 200
        assert "items" in res.json()

        # 4. Test /api/gallery tag filter
        res = await client.get("/api/gallery?tag=mechanical&sort_by=most_forked")
        assert res.status_code == 200
        assert "items" in res.json()

        # 5. Test /api/gallery like endpoint with invalid ID
        res = await client.post("/api/gallery/non-existent-id/like")
        assert res.status_code == 404

        # 6. Test /api/gallery fork endpoint with invalid ID
        res = await client.post("/api/gallery/non-existent-id/fork")
        assert res.status_code == 404
