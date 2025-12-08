"""
Integration tests for authentication and hafiz selection routes.
Tests the complete user journey from signup to selecting a hafiz.
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


def test_hafiz_journey(client):
    """
    Hafiz creation and selection journey:
    1. Signup and login
    2. Create hafiz → redirects to hafiz_selection
    3. Select hafiz → redirects to home page
    """
    # Setup: Create user and login
    client.post(
        "/users/signup",
        data={
            "email": "hafiz_test@test.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "name": "Hafiz Test User",
        },
    )
    client.post(
        "/users/login",
        data={
            "email": "hafiz_test@test.com",
            "password": "testpass123",
        },
    )

    # 1. Create hafiz
    response = client.post(
        "/users/add_hafiz",
        data={
            "name": "Test Hafiz",
            "daily_capacity": 5,
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert "/users/hafiz_selection" in response.headers["location"]

    # 2. Visit hafiz_selection to get the hafiz id
    response = client.get("/users/hafiz_selection")
    assert response.status_code == 200
    assert "Test Hafiz" in response.text

    # 3. Select hafiz (need to find the hafiz id from the response)
    # The form posts current_hafiz_id - we need to extract it
    # For simplicity, assume hafiz id is 1 (first created in test db)
    response = client.post(
        "/users/hafiz_selection",
        data={"current_hafiz_id": 1},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/"

    # 4. Verify home page loads with system date and Close Date button
    response = client.get("/")
    assert response.status_code == 200
    assert "System Date:" in response.text
    assert "Close Date" in response.text
