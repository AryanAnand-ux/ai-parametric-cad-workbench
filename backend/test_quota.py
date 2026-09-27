"""Tests for daily generation quota, per-user rate keys, and batch export-all."""
import asyncio
import io
import uuid
import zipfile
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import main
from config import MODELS_DIR
from database import async_session_maker, create_tables
from services.auth_service import DAILY_GENERATION_QUOTA, check_and_bump_quota


@pytest.fixture(autouse=True, scope="module")
def init_db():
    asyncio.run(create_tables())


@pytest.fixture(autouse=True)
def clear_limiters():
    main.generate_limiter.history.clear()
    main.modify_limiter.history.clear()
    main.recompute_limiter.history.clear()
    yield
    main.generate_limiter.history.clear()
    main.modify_limiter.history.clear()
    main.recompute_limiter.history.clear()


class _FakeDB:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        pass


def _today():
    return datetime.now(timezone.utc).date().isoformat()


def _user(generations_today=0, last_generation_date=None):
    return SimpleNamespace(
        id=f"user_{uuid.uuid4().hex[:8]}",
        generations_today=generations_today,
        last_generation_date=last_generation_date,
    )


@pytest.mark.asyncio
async def test_quota_resets_on_new_day():
    assert DAILY_GENERATION_QUOTA == 50
    db = _FakeDB()
    user = _user(generations_today=50, last_generation_date="2000-01-01")
    await check_and_bump_quota(user, db)
    assert user.last_generation_date == _today()
    assert user.generations_today == 1
    assert db.commits == 1


@pytest.mark.asyncio
async def test_quota_raises_429_at_limit():
    db = _FakeDB()
    user = _user(generations_today=50, last_generation_date=_today())
    with pytest.raises(HTTPException) as exc:
        await check_and_bump_quota(user, db)
    assert exc.value.status_code == 429
    detail = exc.value.detail
    assert detail["error"] == "Daily generation quota exceeded (50/day on free tier)"
    assert detail["error_code"] == "quota_exceeded"
    assert detail["reset"] == "midnight UTC"
    # No increment / commit on rejection
    assert user.generations_today == 50
    assert db.commits == 0


@pytest.mark.asyncio
async def test_quota_increments_under_limit():
    db = _FakeDB()
    user = _user(generations_today=49, last_generation_date=_today())
    await check_and_bump_quota(user, db)
    assert user.generations_today == 50
    assert user.last_generation_date == _today()
    assert db.commits == 1


@pytest.mark.asyncio
async def test_quota_first_use_no_history():
    db = _FakeDB()
    user = _user(generations_today=0, last_generation_date=None)
    await check_and_bump_quota(user, db)
    assert user.generations_today == 1
    assert user.last_generation_date == _today()
    assert db.commits == 1


def _mock_success_pipeline(monkeypatch):
    from schemas import CADParameter, DualOutputPayload

    payload = DualOutputPayload(
        part_name="Quota Box",
        description="test",
        python_code="PARAMS = {}",
        parameters=[
            CADParameter(name="length", label="Length", type="number",
                         default=10.0, min=1.0, max=100.0, step=1.0)
        ],
    )

    def fake_llm(prompt):
        return payload, "test-model"

    async def fake_exec(**kwargs):
        return {
            "status": "success",
            "mesh_url": "/static/models/x.stl",
            "step_url": "/static/models/x.step",
            "mesh_info": {"is_valid": True, "volume_mm3": 1000.0},
            "recomputation_time_ms": 5,
        }

    monkeypatch.setattr(main.LLMService, "generate_dual_output", fake_llm)
    monkeypatch.setattr(main.CADRunner, "execute_script_async", fake_exec)


def test_guest_generate_bypasses_quota(monkeypatch):
    _mock_success_pipeline(monkeypatch)
    calls = []

    async def spy(user, db=None, cost=1):
        calls.append(getattr(user, "id", None))
        return user

    monkeypatch.setattr(main, "check_and_bump_quota", spy)
    client = TestClient(main.app)
    res = client.post("/api/generate",
                      json={"prompt": "Generate a simple 40mm guest quota test box"})
    assert res.status_code == 200, res.text
    assert calls == []


def test_authenticated_generate_enforces_quota_before_llm(monkeypatch):
    _mock_success_pipeline(monkeypatch)
    llm_calls = []
    orig_llm = main.LLMService.generate_dual_output

    def counting_llm(prompt):
        llm_calls.append(prompt)
        return orig_llm(prompt)

    monkeypatch.setattr(main.LLMService, "generate_dual_output", counting_llm)
    client = TestClient(main.app)
    email = f"quota_{uuid.uuid4().hex[:8]}@cad.ai"
    reg = client.post("/api/auth/register", json={
        "email": email, "password": "Password123!", "display_name": "Quota User"})
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]

    async def _max_out():
        await create_tables()
        from sqlalchemy import select
        from models.user import User
        async with async_session_maker() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            assert user is not None
            user.generations_today = 50
            user.last_generation_date = _today()
            await session.commit()

    asyncio.run(_max_out())
    res = client.post("/api/generate",
                      json={"prompt": "Generate a simple 40mm over-quota test box"},
                      headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 429, res.text
    body = res.json()
    detail = body.get("detail", body)
    assert detail["error_code"] == "quota_exceeded"
    assert llm_calls == []


def test_per_user_rate_keys():
    assert main._rate_limit_key(SimpleNamespace(id="abc"), "1.2.3.4") == "user:abc"
    assert main._rate_limit_key(None, "1.2.3.4") == "ip:1.2.3.4"


def test_download_all_zip_contains_members():
    client = TestClient(main.app)
    script_id = f"batch{uuid.uuid4().hex[:10]}"
    created = []
    try:
        for ext, content in (("stl", b"STL-DATA"), ("step", b"STEP-DATA"),
                             ("obj", b"OBJ-DATA"), ("glb", b"GLB-DATA")):
            path = MODELS_DIR / f"{script_id}.{ext}"
            path.write_bytes(content)
            created.append(path)
        res = client.get(f"/api/download/{script_id}/all")
        assert res.status_code == 200, res.text
        assert "attachment" in res.headers.get("content-disposition", "")
        assert f"{script_id}_all.zip" in res.headers.get("content-disposition", "")
        with zipfile.ZipFile(io.BytesIO(res.content)) as archive:
            names = set(archive.namelist())
        assert names == {f"{script_id}.stl", f"{script_id}.step",
                         f"{script_id}.obj", f"{script_id}.glb"}
    finally:
        for path in created:
            try:
                path.unlink()
            except OSError:
                pass


def test_download_all_404_when_nothing_exists():
    client = TestClient(main.app)
    script_id = f"missing{uuid.uuid4().hex[:10]}"
    res = client.get(f"/api/download/{script_id}/all")
    assert res.status_code == 404


def test_download_all_private_gated():
    client = TestClient(main.app)
    owner_email = f"owner_{uuid.uuid4().hex[:8]}@cad.ai"
    reg = client.post("/api/auth/register", json={
        "email": owner_email, "password": "Password123!", "display_name": "Owner"})
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]

    script_id = f"priv{uuid.uuid4().hex[:10]}"
    stl_path = MODELS_DIR / f"{script_id}.stl"
    stl_path.write_bytes(b"STL-PRIVATE")
    try:
        async def _seed():
            await create_tables()
            from sqlalchemy import select
            from models.user import User
            from models.project import Project, Generation
            async with async_session_maker() as session:
                result = await session.execute(
                    select(User).where(User.email == owner_email))
                owner = result.scalar_one_or_none()
                assert owner is not None
                project = Project(user_id=owner.id, name="Private WS")
                session.add(project)
                await session.flush()
                session.add(Generation(
                    user_id=owner.id, project_id=project.id,
                    prompt="private box", script_id=script_id,
                    part_name="Private", python_code="PARAMS = {}",
                    is_public=False,
                ))
                await session.commit()

        asyncio.run(_seed())

        guest_res = client.get(f"/api/download/{script_id}/all")
        assert guest_res.status_code == 403

        owner_res = client.get(
            f"/api/download/{script_id}/all",
            headers={"Authorization": f"Bearer {token}"})
        assert owner_res.status_code == 200, owner_res.text
        with zipfile.ZipFile(io.BytesIO(owner_res.content)) as archive:
            assert f"{script_id}.stl" in archive.namelist()
    finally:
        try:
            stl_path.unlink()
        except OSError:
            pass
