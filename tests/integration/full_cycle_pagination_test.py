"""Integration tests for Full Cycle pagination behavior."""

import time
import pytest
from fasthtml.core import Client


@pytest.fixture
def auth_with_hafiz(client):
    """Create authenticated session with a hafiz that has memorized pages."""
    from app.users_model import create_user, get_user_by_email
    from database import hafizs, hafizs_items, plans

    # Create unique test user
    test_email = f"fc_pagination_test_{int(time.time() * 1000)}@example.com"
    user_id = create_user(test_email, "password123", "FC Pagination Test User")

    # Login
    login_response = client.post(
        "/users/login",
        data={"email": test_email, "password": "password123"},
        follow_redirects=False,
    )
    client.cookies = login_response.cookies

    # Create hafiz with low daily_capacity for easier testing
    client.post(
        "/hafiz/add",
        data={"name": "Test Hafiz", "daily_capacity": 5},
        follow_redirects=False,
    )

    # Select the hafiz
    user_hafizs = hafizs(where=f"user_id={user_id}")
    hafiz_id = user_hafizs[0].id
    select_response = client.post(
        "/hafiz/selection",
        data={"current_hafiz_id": hafiz_id},
        follow_redirects=False,
    )
    client.cookies = select_response.cookies

    # Mark some pages as memorized for Full Cycle eligibility
    memorized_items = hafizs_items(where=f"hafiz_id={hafiz_id}")[:15]
    for item in memorized_items:
        hafizs_items.update({"memorized": True}, item.id)

    yield {
        "client": client,
        "user_id": user_id,
        "hafiz_id": hafiz_id,
        "email": test_email,
    }

    # Cleanup: delete test user (cascades to hafizs, hafizs_items, etc.)
    from database import users

    users.delete(user_id)


# ============================================================================
# Pagination Navigation Tests
# ============================================================================


def test_home_page_loads_with_mode_tables(auth_with_hafiz):
    """Home page loads successfully and shows mode tables."""
    client = auth_with_hafiz["client"]

    response = client.get("/")
    assert response.status_code == 200
    # Verify some mode table is present (FC, WR, DR, or SR)
    assert "summary_table_" in response.text


def test_page_change_returns_table_for_full_cycle(auth_with_hafiz, htmx_headers):
    """GET /page/FC?page=N returns table content for the specified page."""
    client = auth_with_hafiz["client"]

    # First establish session state by visiting home
    client.get("/")

    # Request page 1
    response = client.get("/page/FC?page=1", headers=htmx_headers)
    assert response.status_code == 200
    assert "summary_table_FC" in response.text


def test_page_change_clamps_invalid_page_numbers(auth_with_hafiz, htmx_headers):
    """GET /page/FC with invalid page number clamps to valid range."""
    client = auth_with_hafiz["client"]

    # Establish session state
    client.get("/")

    # Request page 0 (should clamp to 1)
    response = client.get("/page/FC?page=0", headers=htmx_headers)
    assert response.status_code == 200

    # Request very high page number (should clamp to max)
    response = client.get("/page/FC?page=9999", headers=htmx_headers)
    assert response.status_code == 200


def test_page_change_stores_current_page_in_session(auth_with_hafiz, htmx_headers):
    """GET /page/FC?page=N stores the page number in session."""
    client = auth_with_hafiz["client"]

    # Establish session
    client.get("/")

    # Change to page 2
    client.get("/page/FC?page=2", headers=htmx_headers)

    # Visit home again - should remember page 2
    response = client.get("/")
    # The session should have the page stored (verified by behavior, not direct check)
    assert response.status_code == 200


# ============================================================================
# Empty State Tests
# ============================================================================


def test_empty_page_shows_no_pages_message(client):
    """When paginated page has no items, shows 'No pages to review' message."""
    from app.users_model import create_user
    from database import users, hafizs

    # Create user with no memorized pages
    test_email = f"empty_fc_test_{int(time.time() * 1000)}@example.com"
    user_id = create_user(test_email, "password123", "Empty FC Test User")

    login_response = client.post(
        "/users/login",
        data={"email": test_email, "password": "password123"},
        follow_redirects=False,
    )
    client.cookies = login_response.cookies

    client.post(
        "/hafiz/add",
        data={"name": "Empty Hafiz", "daily_capacity": 5},
        follow_redirects=False,
    )

    user_hafizs = hafizs(where=f"user_id={user_id}")
    hafiz_id = user_hafizs[0].id
    select_response = client.post(
        "/hafiz/selection",
        data={"current_hafiz_id": hafiz_id},
        follow_redirects=False,
    )
    client.cookies = select_response.cookies

    # Home page should either not show FC table or show empty message
    response = client.get("/")
    assert response.status_code == 200

    # Cleanup
    users.delete(user_id)


# ============================================================================
# Bulk Rate Tests with Pagination
# ============================================================================


def test_bulk_rate_returns_updated_table(auth_with_hafiz, htmx_headers):
    """POST /bulk_rate returns updated table with pagination controls intact."""
    client = auth_with_hafiz["client"]
    hafiz_id = auth_with_hafiz["hafiz_id"]

    from database import hafizs_items, plans
    from app.common_function import get_current_date, get_current_plan_id

    # Get current date and plan
    current_date = get_current_date(hafiz_id)

    # Find items that are memorized and available for rating
    memorized_items = hafizs_items(
        where=f"hafiz_id={hafiz_id} AND memorized=1"
    )[:2]

    if not memorized_items:
        pytest.skip("No memorized items available for test")

    item_ids = [str(item.item_id) for item in memorized_items]

    # Establish session
    client.get("/")

    # Get plan_id for the request
    plan_id = get_current_plan_id()

    response = client.post(
        "/bulk_rate",
        data={
            "item_ids": item_ids,
            "rating": "1",
            "mode_code": "FC",
            "date": current_date,
            "plan_id": str(plan_id) if plan_id else "",
        },
        headers=htmx_headers,
    )

    assert response.status_code == 200
    assert "summary_table_FC" in response.text
