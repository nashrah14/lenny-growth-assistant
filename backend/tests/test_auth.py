"""
Unit & Integration Tests for Authentication & Authorization System
"""
import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.db.session import get_db
from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.db.models.user import User

@pytest.mark.asyncio
async def test_password_hashing():
    raw_pass = "SuperSecretPassword123!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

@pytest.mark.asyncio
async def test_signup_flow(test_db_session):
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Successful Signup
        payload = {
            "name": "Elena Verna",
            "email": "elena@growth.com",
            "password": "Password123!",
            "confirm_password": "Password123!"
        }
        res = await client.post("/api/v1/auth/signup", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["user"]["email"] == "elena@growth.com"
        assert data["user"]["name"] == "Elena Verna"
        assert "password" not in data["user"]
        # Verify cookie is set
        assert "lenny_auth_session" in res.cookies

        # 2. Duplicate Email Signup -> 409 Conflict
        res_dup = await client.post("/api/v1/auth/signup", json=payload)
        assert res_dup.status_code == 409
        assert res_dup.json()["error"]["code"] == "USER_ALREADY_EXISTS"

        # 3. Password Mismatch -> 422
        mismatch_payload = {
            "name": "Elena Verna",
            "email": "elena2@growth.com",
            "password": "Password123!",
            "confirm_password": "DifferentPassword123!"
        }
        res_mis = await client.post("/api/v1/auth/signup", json=mismatch_payload)
        assert res_mis.status_code == 422
        assert res_mis.json()["error"]["code"] == "PASSWORD_MISMATCH"

        # 4. Weak Password -> 422
        weak_payload = {
            "name": "Elena Verna",
            "email": "elena3@growth.com",
            "password": "short",
            "confirm_password": "short"
        }
        res_weak = await client.post("/api/v1/auth/signup", json=weak_payload)
        assert res_weak.status_code == 422

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_and_logout_flow(test_db_session):
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create user
        signup_payload = {
            "name": "Rahul Vohra",
            "email": "rahul@superhuman.com",
            "password": "Superhuman123!",
            "confirm_password": "Superhuman123!"
        }
        await client.post("/api/v1/auth/signup", json=signup_payload)

        # 1. Successful Login
        login_res = await client.post("/api/v1/auth/login", json={
            "email": "rahul@superhuman.com",
            "password": "Superhuman123!"
        })
        assert login_res.status_code == 200
        assert login_res.json()["user"]["name"] == "Rahul Vohra"
        assert "lenny_auth_session" in login_res.cookies

        # 2. Get Me (/api/v1/auth/me) with Cookie
        me_res = await client.get("/api/v1/auth/me")
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "rahul@superhuman.com"

        # 3. Wrong Password -> 401
        wrong_res = await client.post("/api/v1/auth/login", json={
            "email": "rahul@superhuman.com",
            "password": "WrongPassword!"
        })
        assert wrong_res.status_code == 401

        # 4. Logout
        logout_res = await client.post("/api/v1/auth/logout")
        assert logout_res.status_code == 200

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_authorization_user_isolation(test_db_session):
    """Ensure User A cannot view, access, or modify User B's sessions."""
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client_a:
        # User A sign up
        await client_a.post("/api/v1/auth/signup", json={
            "name": "User Alpha",
            "email": "alpha@growth.com",
            "password": "Password123!"
        })
        # User A creates a session
        sess_a_res = await client_a.post("/api/v1/sessions", json={"title": "Alpha PMF Strategy"})
        assert sess_a_res.status_code == 201
        session_a_id = sess_a_res.json()["id"]

    async with AsyncClient(transport=transport, base_url="http://test") as client_b:
        # User B sign up
        await client_b.post("/api/v1/auth/signup", json={
            "name": "User Beta",
            "email": "beta@growth.com",
            "password": "Password123!"
        })

        # User B lists sessions -> MUST NOT see User A's session
        list_b = await client_b.get("/api/v1/sessions")
        assert list_b.status_code == 200
        assert len(list_b.json()) == 0

        # User B attempts to access User A's session directly by ID -> MUST return 404 (Not Found / Unauthorized)
        get_a_by_b = await client_b.get(f"/api/v1/sessions/{session_a_id}")
        assert get_a_by_b.status_code == 404

        # User B attempts to delete User A's session -> MUST return 404
        del_a_by_b = await client_b.delete(f"/api/v1/sessions/{session_a_id}")
        assert del_a_by_b.status_code == 404

    app.dependency_overrides.clear()
