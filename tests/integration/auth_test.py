"""
Integration tests for authentication routes.
Tests signup, login, logout flows.
"""

import pytest


class TestSignup:
    """Tests for POST /users/signup"""

    def test_signup_creates_user_and_redirects_to_login(self, client):
        """
        Given: A new user's details
        When: POST /users/signup with valid data
        Then: Redirects to /users/login
        """
        response = client.post(
            "/users/signup",
            data={
                "email": "newuser@test.com",
                "password": "testpass123",
                "confirm_password": "testpass123",
                "name": "Test User",
            },
            follow_redirects=False,
        )

        assert response.status_code in (302, 303)
        assert "/users/login" in response.headers["location"]
