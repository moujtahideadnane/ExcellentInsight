import pytest

# Note: Using shared fixtures from conftest.py (db_session, client)


@pytest.mark.asyncio
async def test_signup_creates_org_and_user(client):
    """Test that signup creates both organization and user."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "securepassword123", "org_name": "Test Org"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["role"] == "admin"
    assert "org_id" in data["user"]


@pytest.mark.asyncio
async def test_login_returns_valid_jwt(client):
    """Test that login returns valid JWT tokens."""
    # First signup
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "login@example.com", "password": "securepassword123", "org_name": "Login Test Org"},
    )

    # Then login
    response = await client.post(
        "/api/v1/auth/login", json={"email": "login@example.com", "password": "securepassword123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client):
    """Test that login with wrong password returns 401."""
    # First signup
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "wrongpass@example.com", "password": "securepassword123", "org_name": "Wrong Pass Org"},
    )

    # Try login with wrong password
    response = await client.post(
        "/api/v1/auth/login", json={"email": "wrongpass@example.com", "password": "wrongpassword"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_email_returns_400(client):
    """Test that duplicate email signup returns 400."""
    # First signup
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "duplicate@example.com", "password": "securepassword123", "org_name": "First Org"},
    )

    # Try duplicate signup
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "duplicate@example.com", "password": "anotherpassword", "org_name": "Second Org"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_refresh_token_endpoint(client):
    """Test that refresh token endpoint works."""
    # First signup
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "refresh@example.com", "password": "securepassword123", "org_name": "Refresh Org"},
    )

    refresh_token = signup_response.json()["refresh_token"]

    # Refresh tokens
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
