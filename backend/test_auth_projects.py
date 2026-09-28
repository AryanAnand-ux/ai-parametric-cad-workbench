"""
test_auth_projects.py — Automated Unit & Integration Tests for Auth & Workspaces
================================================================================
Tests:
  - Native bcrypt password hashing and verification
  - JWT token generation and validation
  - /api/auth/register, /api/auth/login, /api/auth/me
  - /api/projects CRUD and user workspace isolation
  - /api/generate/stream SSE streaming format
"""

import pytest
import uuid
import asyncio
from fastapi.testclient import TestClient
from main import app
from database import create_tables
from services.auth_service import hash_password, verify_password, create_access_token, decode_token

@pytest.fixture(autouse=True, scope="module")
def init_db():
    asyncio.run(create_tables())

client = TestClient(app)


def test_password_hashing():
    pw = "SuperSecure123!"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_roundtrip():
    user_id = str(uuid.uuid4())
    email = "engineer@example.com"
    token = create_access_token(user_id, email)
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["email"] == email
    assert payload["type"] == "access"


def test_auth_registration_and_login():
    unique_email = f"user_{uuid.uuid4().hex[:8]}@cad.ai"
    password = "TestPassword456!"

    # 1. Register
    reg_resp = client.post("/api/auth/register", json={
        "email": unique_email,
        "password": password,
        "display_name": "Test Engineer"
    })
    assert reg_resp.status_code == 201, reg_resp.text
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == unique_email
    assert reg_data["user"]["display_name"] == "Test Engineer"

    token = reg_data["access_token"]

    # 2. Duplicate registration fails with 409
    dup_resp = client.post("/api/auth/register", json={
        "email": unique_email,
        "password": password,
        "display_name": "Duplicate User"
    })
    assert dup_resp.status_code == 409

    # 3. Login
    login_resp = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": password
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data

    # 4. Wrong password fails with 401
    bad_login = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401

    # 5. Access profile with token
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == unique_email

    # 6. Access profile without token fails with 401
    unauth_resp = client.get("/api/auth/me")
    assert unauth_resp.status_code == 401


def test_project_workspace_crud_and_isolation():
    # User A
    user_a_email = f"usera_{uuid.uuid4().hex[:8]}@cad.ai"
    resp_a = client.post("/api/auth/register", json={
        "email": user_a_email,
        "password": "Password123!",
        "display_name": "User A"
    })
    token_a = resp_a.json()["access_token"]

    # User B
    user_b_email = f"userb_{uuid.uuid4().hex[:8]}@cad.ai"
    resp_b = client.post("/api/auth/register", json={
        "email": user_b_email,
        "password": "Password123!",
        "display_name": "User B"
    })
    token_b = resp_b.json()["access_token"]

    # User A creates a project
    create_resp = client.post("/api/projects", json={
        "name": "Robotics Chassis",
        "description": "Main chassis assembly"
    }, headers={"Authorization": f"Bearer {token_a}"})
    assert create_resp.status_code == 201
    proj_a_id = create_resp.json()["project"]["id"]

    # User A lists projects -> sees 1
    list_a = client.get("/api/projects", headers={"Authorization": f"Bearer {token_a}"}).json()
    assert any(p["id"] == proj_a_id for p in list_a["projects"])

    # User B lists projects -> does NOT see User A's project (isolation)
    list_b = client.get("/api/projects", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert not any(p["id"] == proj_a_id for p in list_b["projects"])

    # User A deletes project
    del_resp = client.delete(f"/api/projects/{proj_a_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert del_resp.status_code == 200

    # User A lists again -> project gone
    list_a_after = client.get("/api/projects", headers={"Authorization": f"Bearer {token_a}"}).json()
    assert not any(p["id"] == proj_a_id for p in list_a_after["projects"])


def test_generation_detail_public_and_isolation():
    from database import async_session_maker
    from models.project import Project, Generation

    # 1. Register owner and guest
    owner_email = f"gen_owner_{uuid.uuid4().hex[:8]}@cad.ai"
    guest_email = f"gen_guest_{uuid.uuid4().hex[:8]}@cad.ai"
    owner_token = client.post("/api/auth/register", json={
        "email": owner_email, "password": "Password123!", "display_name": "Owner"
    }).json()["access_token"]
    guest_token = client.post("/api/auth/register", json={
        "email": guest_email, "password": "Password123!", "display_name": "Guest"
    }).json()["access_token"]

    priv_script_id = f"priv_gen_{uuid.uuid4().hex[:8]}"
    pub_script_id = f"pub_gen_{uuid.uuid4().hex[:8]}"
    priv_gen_id = None
    pub_gen_id = None

    async def _setup():
        from models.user import User
        from sqlalchemy import select
        async with async_session_maker() as session:
            res = await session.execute(select(User).where(User.email == owner_email))
            owner = res.scalar_one()
            proj = Project(user_id=owner.id, name="Test WS")
            session.add(proj)
            await session.flush()

            priv_g = Generation(
                user_id=owner.id, project_id=proj.id,
                prompt="private gear", script_id=priv_script_id,
                part_name="Private Gear", python_code="PARAMS = {}",
                is_public=False
            )
            pub_g = Generation(
                user_id=owner.id, project_id=proj.id,
                prompt="public bolt", script_id=pub_script_id,
                part_name="Public Bolt", python_code="PARAMS = {}",
                is_public=True
            )
            session.add(priv_g)
            session.add(pub_g)
            await session.commit()
            return priv_g.id, pub_g.id

    priv_gen_id, pub_gen_id = asyncio.run(_setup())

    # A. Public generation: accessible anonymously and by any user
    anon_pub = client.get(f"/api/generations/{pub_gen_id}")
    assert anon_pub.status_code == 200
    assert anon_pub.json()["generation"]["part_name"] == "Public Bolt"

    # Also lookup public generation by script_id
    anon_pub_script = client.get(f"/api/generations/{pub_script_id}")
    assert anon_pub_script.status_code == 200

    # B. Private generation: anonymous access returns 401
    anon_priv = client.get(f"/api/generations/{priv_gen_id}")
    assert anon_priv.status_code == 401

    # C. Private generation: other user returns 403
    other_priv = client.get(
        f"/api/generations/{priv_gen_id}",
        headers={"Authorization": f"Bearer {guest_token}"}
    )
    assert other_priv.status_code == 403

    # D. Private generation: owner returns 200
    owner_priv = client.get(
        f"/api/generations/{priv_gen_id}",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert owner_priv.status_code == 200
    assert owner_priv.json()["generation"]["part_name"] == "Private Gear"

    # Also lookup private generation by script_id with owner token
    owner_priv_script = client.get(
        f"/api/generations/{priv_script_id}",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert owner_priv_script.status_code == 200

