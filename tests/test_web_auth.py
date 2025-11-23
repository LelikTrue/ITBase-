# tests/test_web_auth.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_web_login_flow(async_client: AsyncClient):
    # 1. Create user via API (since we fixed it)
    await async_client.post(
        "/users/",
        json={"email": "webuser@example.com", "password": "password123", "full_name": "Web User"},
    )
    
    # 2. Login via Web Form
    # Note: We need to use the SAME client to persist cookies if we were following redirects,
    # but here we might need to manually handle cookies if AsyncClient doesn't follow redirects by default or if we want to check intermediate steps.
    # AsyncClient(follow_redirects=False) is default.
    
    login_data = {
        "email": "webuser@example.com",
        "password": "password123"
    }
    
    response = await async_client.post(
        "/login",
        data=login_data,
        follow_redirects=False
    )
    
    # Expect redirect to dashboard
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    
    # Check if session cookie is set
    assert "session" in response.cookies
    
    # 3. Access Dashboard with the session cookie
    # The client should automatically store cookies from the response if we reuse it.
    
    dashboard_response = await async_client.get("/dashboard", follow_redirects=False)
    
    # Should be 200 OK (not redirect to login)
    assert dashboard_response.status_code == 200
    assert "Dashboard" in dashboard_response.text  # Assuming "Dashboard" is in the HTML title or body
