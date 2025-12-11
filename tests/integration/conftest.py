"""Integration test fixtures using FastHTML's Client (TestClient)."""

import pytest
from fasthtml.core import Client


@pytest.fixture(scope="session")
def test_user():
    """Session-scoped test user with credentials for login tests."""
    from app.users_model import create_user, get_user_by_email

    email = "integration_test@example.com"
    password = "TestPassword123!"
    name = "Integration Test User"

    # Delete existing test user if it exists (from previous failed runs)
    existing_user = get_user_by_email(email)
    if existing_user:
        from database import users

        users.delete(existing_user.id)

    # Create fresh test user
    user_id = create_user(email, password, name)

    return {
        "user_id": user_id,
        "email": email,
        "password": password,
        "name": name,
    }


@pytest.fixture
def client():
    """
    FastHTML test client for in-process HTTP requests.
    """
    from main import app

    return Client(app)


@pytest.fixture
def htmx_headers():
    """HTMX request headers for testing fragment-returning endpoints."""
    return {"HX-Request": "true"}


@pytest.fixture
def auth_session(test_user):
    """Pre-authenticated client with session cookies set. Usage: auth_session.get("/")"""
    from main import app

    client = Client(app)

    response = client.post(
        "/users/login",
        data={
            "email": test_user["email"],
            "password": test_user["password"],
        },
    )

    # Set cookies directly on client instance (recommended approach)
    client.cookies = response.cookies

    return client
