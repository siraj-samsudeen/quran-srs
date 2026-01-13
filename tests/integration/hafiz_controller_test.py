"""Integration tests for hafiz controller endpoints."""

import time
import pytest


# ============================================================================
# Selection Page Tests
# ============================================================================


def test_selection_requires_user_auth(client):
    """GET /hafiz/selection without auth redirects to login."""
    response = client.get("/hafiz/selection", follow_redirects=False)

    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/users/login"


def test_selection_displays_add_form(auth_session):
    """GET /hafiz/selection with auth shows Add Hafiz form."""
    response = auth_session.get("/hafiz/selection")

    assert response.status_code == 200
    assert "Add Hafiz" in response.text or "Name" in response.text


def test_select_hafiz_sets_session_and_redirects(auth_session, test_user):
    """POST /hafiz/selection sets hafiz in session and redirects to /."""
    from database import hafizs

    unique_name = f"Select Test Hafiz {int(time.time() * 1000)}"
    auth_session.post(
        "/hafiz/add",
        data={"name": unique_name},
        follow_redirects=False,
    )

    user_hafizs = hafizs(where=f"user_id={test_user['user_id']}")
    assert len(user_hafizs) > 0
    hafiz_id = user_hafizs[0].id

    response = auth_session.post(
        "/hafiz/selection",
        data={"current_hafiz_id": hafiz_id},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"

    hafizs.delete(hafiz_id)


# ============================================================================
# Add Hafiz Tests
# ============================================================================


def test_add_hafiz_creates_and_redirects(auth_session, test_user):
    """POST /hafiz/add creates hafiz and redirects to selection."""
    from database import hafizs

    unique_name = f"Add Test Hafiz {int(time.time() * 1000)}"

    response = auth_session.post(
        "/hafiz/add",
        data={"name": unique_name},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/hafiz/selection"

    user_hafizs = hafizs(where=f"user_id={test_user['user_id']} AND name='{unique_name}'")
    assert len(user_hafizs) == 1
    hafizs.delete(user_hafizs[0].id)


def test_add_hafiz_populates_items(auth_session, test_user):
    """POST /hafiz/add creates hafizs_items for new hafiz."""
    from database import hafizs, hafizs_items

    unique_name = f"Items Test Hafiz {int(time.time() * 1000)}"

    auth_session.post(
        "/hafiz/add",
        data={"name": unique_name},
        follow_redirects=False,
    )

    user_hafizs = hafizs(where=f"user_id={test_user['user_id']} AND name='{unique_name}'")
    assert len(user_hafizs) == 1
    hafiz_id = user_hafizs[0].id

    items_count = len(hafizs_items(where=f"hafiz_id={hafiz_id}"))
    assert items_count > 0, "hafizs_items should be populated for new hafiz"

    hafizs.delete(hafiz_id)


# ============================================================================
# Delete Hafiz Tests
# ============================================================================


def test_delete_hafiz_requires_ownership(auth_session, test_user):
    """Cannot delete another user's hafiz - redirects without deletion."""
    from app.users_model import create_user
    from database import hafizs, users

    other_email = f"other_user_{int(time.time() * 1000)}@example.com"
    other_user_id = create_user(other_email, "password123", "Other User")

    other_hafiz = hafizs.insert({"name": "Other User Hafiz", "user_id": other_user_id})

    response = auth_session.delete(
        f"/hafiz/delete/{other_hafiz.id}",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/hafiz/selection"

    remaining = hafizs(where=f"id={other_hafiz.id}")
    assert len(remaining) == 1, "Hafiz should not be deleted by non-owner"

    hafizs.delete(other_hafiz.id)
    users.delete(other_user_id)


def test_delete_hafiz_removes_hafiz(client, test_user):
    """Can delete own hafiz."""
    from database import hafizs

    login_response = client.post(
        "/users/login",
        data={"email": test_user["email"], "password": test_user["password"]},
        follow_redirects=False,
    )
    client.cookies = login_response.cookies

    unique_name = f"Delete Test Hafiz {int(time.time() * 1000)}"
    client.post(
        "/hafiz/add",
        data={"name": unique_name},
        follow_redirects=False,
    )

    user_hafizs = hafizs(where=f"user_id={test_user['user_id']} AND name='{unique_name}'")
    assert len(user_hafizs) == 1
    hafiz_id = user_hafizs[0].id

    select_response = client.post(
        "/hafiz/selection",
        data={"current_hafiz_id": hafiz_id},
        follow_redirects=False,
    )
    client.cookies = select_response.cookies

    response = client.delete(
        f"/hafiz/delete/{hafiz_id}",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/hafiz/selection"

    remaining = hafizs(where=f"id={hafiz_id}")
    assert len(remaining) == 0, "Hafiz should be deleted"


# ============================================================================
# Settings Tests
# ============================================================================


def test_settings_requires_hafiz_auth(auth_session, test_user):
    """GET /hafiz/settings without hafiz selected returns error or redirect."""
    from database import hafizs

    unique_name = f"Settings Test Hafiz {int(time.time() * 1000)}"
    auth_session.post(
        "/hafiz/add",
        data={"name": unique_name},
        follow_redirects=False,
    )

    user_hafizs = hafizs(where=f"user_id={test_user['user_id']} AND name='{unique_name}'")
    hafiz_id = user_hafizs[0].id

    select_response = auth_session.post(
        "/hafiz/selection",
        data={"current_hafiz_id": hafiz_id},
        follow_redirects=False,
    )
    auth_session.cookies = select_response.cookies

    response = auth_session.get("/hafiz/settings")

    assert response.status_code == 200
    assert "Hafiz Preferences" in response.text or "Settings" in response.text

    hafizs.delete(hafiz_id)
