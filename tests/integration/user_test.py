"""Integration tests for user authentication and account management."""

import time
import pytest


# ============================================================================
# Signup Tests
# ============================================================================


def test_signup_creates_user_and_redirects_to_login(client):
    """Signup with valid data creates user and redirects to login."""
    unique_email = f"signup_test_{int(time.time() * 1000)}@example.com"

    response = client.post(
        "/users/signup",
        data={
            "name": "Signup Test User",
            "email": unique_email,
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/users/login"


# ============================================================================
# Login Tests
# ============================================================================


def test_login_redirects_to_hafiz_selection(client, test_user):
    """Login with valid credentials redirects to hafiz selection."""
    response = client.post(
        "/users/login",
        data={
            "email": test_user["email"],
            "password": test_user["password"],
        },
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/hafiz/selection"


def test_login_with_invalid_email_redirects_to_signup(client):
    """Login with unregistered email redirects to signup."""
    response = client.post(
        "/users/login",
        data={
            "email": "nonexistent@example.com",
            "password": "password123",
        },
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/users/signup"


def test_login_with_wrong_password_redirects_to_login(client, test_user):
    """Login with incorrect password redirects to login."""
    response = client.post(
        "/users/login",
        data={
            "email": test_user["email"],
            "password": "wrongpassword",
        },
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/users/login"


def test_login_page_displays_form(client):
    """Login page displays email and password fields."""
    response = client.get("/users/login")

    assert response.status_code == 200
    assert "Email" in response.text
    assert "Password" in response.text
    assert "Login" in response.text


# ============================================================================
# Logout Tests
# ============================================================================


def test_logout_clears_session_and_redirects_to_login(auth_session):
    """Logout clears both user_auth and hafiz auth sessions."""
    hafiz_selection_response = auth_session.get("/hafiz/selection")
    assert hafiz_selection_response.status_code == 200

    logout_response = auth_session.get("/users/logout", follow_redirects=False)

    assert logout_response.status_code in (302, 303)
    assert logout_response.headers["location"] == "/users/login"

    protected_response = auth_session.get(
        "/hafiz/selection", follow_redirects=False
    )
    assert protected_response.status_code in (302, 303)
    assert protected_response.headers["location"] == "/users/login"


# ============================================================================
# Account Page Tests
# ============================================================================


def test_account_page_requires_authentication(client):
    """Account page redirects to login when not authenticated."""
    response = client.get("/users/account", follow_redirects=False)

    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/users/login"


def test_account_page_displays_user_profile(auth_session, test_user):
    """Account page displays user profile form when authenticated."""
    response = auth_session.get("/users/account")
    assert response.status_code == 200
    assert "User Profile" in response.text
    assert "Name" in response.text
    assert "Email" in response.text


# ============================================================================
# Account Update Tests
# ============================================================================


def test_account_update_requires_authentication(client):
    """Account update redirects to login when not authenticated."""
    response = client.post(
        "/users/account",
        data={"name": "Test", "email": "test@example.com"},
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/users/login"


def test_account_update_password_mismatch(auth_session, test_user):
    """Account update with mismatched passwords redirects to account page."""
    response = auth_session.post(
        "/users/account",
        data={
            "name": "Test Name",
            "email": test_user["email"],
            "password": "newpassword123",
            "confirm_password": "differentpassword",
        },
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/users/account"


def test_account_update_name_and_email_only(auth_session, test_user):
    """Update name and email without changing password."""
    update_response = auth_session.post(
        "/users/account",
        data={
            "name": "Updated Test Name",
            "email": test_user["email"],
            "password": "",
            "confirm_password": "",
        },
        follow_redirects=False,
    )

    assert update_response.status_code in (302, 303)
    assert update_response.headers["location"] == "/users/account"

    verify_response = auth_session.get("/users/account")
    assert "Updated Test Name" in verify_response.text

    auth_session.post(
        "/users/account",
        data={
            "name": test_user["name"],
            "email": test_user["email"],
            "password": "",
            "confirm_password": "",
        },
    )


def test_account_update_password(auth_session, test_user):
    """Update password with matching confirmation."""
    update_response = auth_session.post(
        "/users/account",
        data={
            "name": "Test User",
            "email": test_user["email"],
            "password": "newpassword123",
            "confirm_password": "newpassword123",
        },
        follow_redirects=False,
    )

    assert update_response.status_code in (302, 303)
    assert update_response.headers["location"] == "/users/account"

    auth_session.post(
        "/users/account",
        data={
            "name": "Test User",
            "email": test_user["email"],
            "password": test_user["password"],
            "confirm_password": test_user["password"],
        },
    )


# ============================================================================
# User Deletion Tests
# ============================================================================


def test_user_cannot_delete_other_users(auth_session):
    """User cannot delete another user's account."""
    response = auth_session.delete(
        "/users/delete/9999",
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/hafiz/selection"


def test_user_deletion_cascades_to_all_related_data(client):
    """User deletion cascades to hafizs, revisions, plans, and hafizs_items."""
    from app.users_model import create_user, get_user_by_email
    from database import hafizs, revisions, plans, hafizs_items

    test_email = f"delete_test_{int(time.time() * 1000)}@example.com"
    user_id = create_user(test_email, "password123", "Delete Test User")

    login_response = client.post(
        "/users/login",
        data={"email": test_email, "password": "password123"},
        follow_redirects=False,
    )
    client.cookies = login_response.cookies

    hafiz_response = client.post(
        "/hafiz/add",
        data={"name": "Test Hafiz"},
        follow_redirects=False,
    )

    # Note: Selecting hafiz to ensure session coverage
    user_hafizs = hafizs(where=f"user_id={user_id}")
    if len(user_hafizs) > 0:
        select_response = client.post(
            "/hafiz/selection",
            data={"current_hafiz_id": user_hafizs[0].id},
            follow_redirects=False,
        )
        client.cookies = select_response.cookies

    user_hafizs = hafizs(where=f"user_id={user_id}")
    assert len(user_hafizs) > 0, "Hafiz should be created"
    hafiz_id = user_hafizs[0].id

    hafizs_count = len(hafizs(where=f"user_id = {user_id}"))
    hafizs_items_count = len(hafizs_items(where=f"hafiz_id = {hafiz_id}"))
    plans_count = len(plans(where=f"hafiz_id = {hafiz_id}"))

    assert hafizs_count > 0, "Should have hafizs"
    assert hafizs_items_count > 0, "Should have hafizs_items"
    assert plans_count > 0, "Should have plans"

    delete_response = client.delete(
        f"/users/delete/{user_id}",
        follow_redirects=False,
    )

    assert delete_response.status_code in (302, 303)
    assert delete_response.headers["location"] == "/users/login"

    assert len(hafizs(where=f"user_id = {user_id}")) == 0, "Hafizs should be deleted"
    assert len(hafizs_items(where=f"hafiz_id = {hafiz_id}")) == 0, "Hafizs_items should be cascade deleted"
    assert len(plans(where=f"hafiz_id = {hafiz_id}")) == 0, "Plans should be cascade deleted"

    assert get_user_by_email(test_email) is None, "User should be deleted"
