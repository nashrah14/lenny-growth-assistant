"""
API Integration Tests for FastAPI Endpoints
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.db.session import get_db

@pytest.mark.asyncio
async def test_health_and_readiness_endpoints(test_db_session):
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test /api/v1/health
        health_resp = await client.get("/api/v1/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()
        assert "status" in health_data
        assert "database" in health_data

        # Test /api/v1/readiness
        ready_resp = await client.get("/api/v1/readiness")
        assert ready_resp.status_code == 200
        assert ready_resp.json()["status"] == "ready"

        # Test / root
        root_resp = await client.get("/")
        assert root_resp.status_code == 200
        assert "docs" in root_resp.json()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_session_api_flow(test_db_session):
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Sign up user first
        await client.post("/api/v1/auth/signup", json={
            "name": "PM Tester",
            "email": "tester@growth.com",
            "password": "Password123!"
        })

        # 1. Create Session
        create_resp = await client.post("/api/v1/sessions", json={"title": "Test PMF Chat"})
        assert create_resp.status_code == 201
        session_data = create_resp.json()
        session_id = session_data["id"]
        assert session_data["title"] == "Test PMF Chat"

        # 2. List Sessions
        list_resp = await client.get("/api/v1/sessions")
        assert list_resp.status_code == 200
        sessions = list_resp.json()
        assert any(s["id"] == session_id for s in sessions)

        # 3. Get Single Session
        get_resp = await client.get(f"/api/v1/sessions/{session_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == session_id

        # 4. Update Title
        patch_resp = await client.patch(f"/api/v1/sessions/{session_id}", json={"title": "Updated PMF Chat"})
        assert patch_resp.status_code == 200
        assert patch_resp.json()["title"] == "Updated PMF Chat"

        # 5. Delete Session
        del_resp = await client.delete(f"/api/v1/sessions/{session_id}")
        assert del_resp.status_code == 204

        # 6. Verify 404 after deletion
        not_found_resp = await client.get(f"/api/v1/sessions/{session_id}")
        assert not_found_resp.status_code == 404

    app.dependency_overrides.clear()
