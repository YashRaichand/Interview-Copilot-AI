import pytest
from httpx import AsyncClient
from tests.conftest import SAMPLE_JD_TEXT


class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/register", json={"email": "newuser@example.com", "full_name": "New User", "password": "SecurePass1"})
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        response = await client.post("/api/v1/auth/register", json={"email": "test@example.com", "full_name": "Duplicate", "password": "SecurePass1"})
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/register", json={"email": "weak@example.com", "full_name": "Weak", "password": "weak"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        response = await client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "TestPassword1"})
        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        response = await client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "WrongPassword1"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403


class TestJobDescriptionAPI:
    @pytest.mark.asyncio
    async def test_create_jd_text(self, client: AsyncClient, auth_headers):
        response = await client.post("/api/v1/job-descriptions/", json={"title": "Senior Python Developer", "company": "TechCorp", "raw_text": SAMPLE_JD_TEXT}, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["title"] == "Senior Python Developer"

    @pytest.mark.asyncio
    async def test_create_jd_too_short(self, client: AsyncClient, auth_headers):
        response = await client.post("/api/v1/job-descriptions/", json={"title": "Job", "raw_text": "Too short"}, headers=auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_jds(self, client: AsyncClient, auth_headers):
        await client.post("/api/v1/job-descriptions/", json={"title": "Test JD", "raw_text": SAMPLE_JD_TEXT}, headers=auth_headers)
        response = await client.get("/api/v1/job-descriptions/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "running"

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        assert "checks" in response.json()

    @pytest.mark.asyncio
    async def test_docs_accessible(self, client: AsyncClient):
        response = await client.get("/docs")
        assert response.status_code == 200


class TestDashboardAPI:
    @pytest.mark.asyncio
    async def test_get_stats_empty(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total_resumes"] >= 0

    @pytest.mark.asyncio
    async def test_stats_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/dashboard/stats")
        assert response.status_code == 403


class TestCORSConfig:
    """Regression test: BACKEND_CORS_ORIGINS must parse as a JSON array, not crash the app."""

    def test_cors_origins_is_a_list(self):
        from app.config import settings
        assert isinstance(settings.BACKEND_CORS_ORIGINS, list)

    def test_redis_url_property_never_raises(self):
        from app.config import settings
        # Whether REDIS_URL, or host/port fields are set, this must always return a string.
        assert isinstance(settings.get_redis_url, str)
        assert settings.get_redis_url.startswith("redis://")
