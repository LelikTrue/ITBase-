import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "it-asset-management"}

def test_readiness_check():
    """Test the readiness check endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "service": "it-asset-management"}

@pytest.mark.asyncio
async def test_api_health():
    """Test the API health check endpoint."""
    async with TestClient(app) as async_client:
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "services" in data
        assert data["services"]["database"] == "ok"

@pytest.mark.asyncio
async def test_api_health_ready():
    """Test the API readiness check endpoint."""
    async with TestClient(app) as async_client:
        response = await async_client.get("/api/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}

@pytest.mark.asyncio
async def test_api_health_startup():
    """Test the API startup check endpoint."""
    async with TestClient(app) as async_client:
        response = await async_client.get("/api/health/startup")
        assert response.status_code == 200
        assert response.json() == {"status": "started"}
