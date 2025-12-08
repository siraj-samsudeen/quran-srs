"""
Integration tests for authentication routes.
Tests the complete signup → login → logout journey.
"""

import pytest


def test_auth_journey(client):
    """
    Complete auth journey:
    1. Signup → redirects to login
    2. Login → redirects to hafiz_selection
    3. Logout → redirects to login
    """
    # 1. Signup
    response = client.post(
        "/users/signup",
        data={
            "email": "journey@test.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "name": "Journey Test User",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert "/users/login" in response.headers["location"]

    # 2. Login
    response = client.post(
        "/users/login",
        data={
            "email": "journey@test.com",
            "password": "testpass123",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert "/users/hafiz_selection" in response.headers["location"]

    # 3. Logout
    response = client.get("/users/logout", follow_redirects=False)
    assert response.status_code in (302, 303)
    assert "/users/login" in response.headers["location"]
