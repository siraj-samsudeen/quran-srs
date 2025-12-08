"""
Integration tests for authentication and hafiz selection routes.
Tests the complete user journey from signup to selecting a hafiz.
"""

import pytest
from app.globals import users
from app.hafiz_model import hafizs


def test_auth_journey(client, unique_id):
    """
    Complete auth journey:
    1. Signup → redirects to login + user created in DB
    2. Login → redirects to hafiz_selection
    3. Logout → redirects to login
    """
    email = f"journey_{unique_id}@test.com"
    name = f"Journey Test User {unique_id}"

    # 1. Signup
    response = client.post(
        "/users/signup",
        data={
            "email": email,
            "password": "testpass123",
            "confirm_password": "testpass123",
            "name": name,
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert "/users/login" in response.headers["location"]

    # Verify user was created in database
    user = users(where=f"email = '{email}'")
    assert len(user) == 1
    assert user[0].name == name

    # 2. Login
    response = client.post(
        "/users/login",
        data={
            "email": email,
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


def test_hafiz_journey(client, unique_id):
    """
    Hafiz creation and selection journey:
    1. Signup and login
    2. Create hafiz → redirects to hafiz_selection
    3. Select hafiz → redirects to home page
    """
    email = f"hafiz_test_{unique_id}@test.com"
    user_name = f"Hafiz Test User {unique_id}"
    hafiz_name = f"Test Hafiz {unique_id}"

    # Setup: Create user and login
    client.post(
        "/users/signup",
        data={
            "email": email,
            "password": "testpass123",
            "confirm_password": "testpass123",
            "name": user_name,
        },
    )
    client.post(
        "/users/login",
        data={
            "email": email,
            "password": "testpass123",
        },
    )

    # 1. Create hafiz
    response = client.post(
        "/users/add_hafiz",
        data={
            "name": hafiz_name,
            "daily_capacity": 5,
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert "/users/hafiz_selection" in response.headers["location"]

    # Verify hafiz was created in database and get the ID
    hafiz = hafizs(where=f"name = '{hafiz_name}'")
    assert len(hafiz) == 1
    assert hafiz[0].daily_capacity == 5
    hafiz_id = hafiz[0].id

    # 2. Visit hafiz_selection to verify hafiz appears
    response = client.get("/users/hafiz_selection")
    assert response.status_code == 200
    assert hafiz_name in response.text

    # 3. Select hafiz using the actual ID from database
    response = client.post(
        "/users/hafiz_selection",
        data={"current_hafiz_id": hafiz_id},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/"

    # 4. Verify home page loads with system date and Close Date button
    response = client.get("/")
    assert response.status_code == 200
    assert "System Date:" in response.text
    assert "Close Date" in response.text
