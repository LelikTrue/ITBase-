# tests/test_auth.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio()
async def test_create_user(async_client: AsyncClient):
    response = await async_client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.asyncio()
async def test_login_access_token(async_client: AsyncClient):
    # Create user first
    await async_client.post(
        "/users/",
        json={
            "email": "login@example.com",
            "password": "password123",
            "full_name": "Login User",
        },
    )

    response = await async_client.post(
        "/login/access-token",
        data={"username": "login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio()
async def test_read_users_me(async_client: AsyncClient):
    # Create user
    await async_client.post(
        "/users/",
        json={
            "email": "me@example.com",
            "password": "password123",
            "full_name": "Me User",
        },
    )

    # Login
    login_response = await async_client.post(
        "/login/access-token",
        data={"username": "me@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    # Get me
    response = await async_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
