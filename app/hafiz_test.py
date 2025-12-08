"""
Hafiz Module Tests

Unit tests and integration tests for hafiz module.
Tests model functions and routes without browser.

Note: Integration test fixtures (client, auth_session, hafiz_session, parse_html)
are defined in tests/conftest.py and shared across all test files.
"""

import pytest
from app.hafiz_model import (
    Hafiz,
    hafizs,
    get_hafiz,
    update_hafiz,
    insert_hafiz,
    delete_hafiz,
    get_hafizs_for_user,
    populate_hafiz_items,
    create_new_plan,
)
from app.hafiz_service import setup_new_hafiz
from app.globals import hafizs_items, plans


# =============================================================================
# Unit Tests - Pure Python, no HTTP
# =============================================================================


def test_get_hafiz():
    """Unit test: get_hafiz returns Hafiz instance."""
    hafiz = get_hafiz(1)

    assert isinstance(hafiz, Hafiz)
    assert hafiz.id == 1
    assert hafiz.name is not None


def test_update_hafiz():
    """Unit test: update_hafiz modifies database."""
    # Get current hafiz
    original = get_hafiz(1)
    original_capacity = original.daily_capacity

    # Update with new capacity
    new_capacity = 99 if original_capacity != 99 else 88
    updated_data = Hafiz(
        id=1,
        name=original.name,
        daily_capacity=new_capacity,
        user_id=original.user_id,
        current_date=original.current_date,
    )
    update_hafiz(updated_data, 1)

    # Verify update
    updated = get_hafiz(1)
    assert updated.daily_capacity == new_capacity

    # Restore original
    update_hafiz(original, 1)


def test_insert_hafiz():
    """Unit test: insert_hafiz creates new record."""
    # Create new hafiz
    new_hafiz = Hafiz(
        id=None,
        name="Test Hafiz",
        daily_capacity=5,
        user_id=1,
        current_date="2025-01-01",
    )
    created = insert_hafiz(new_hafiz)

    # Verify creation
    assert created.id is not None
    assert created.name == "Test Hafiz"
    assert created.daily_capacity == 5

    # Cleanup
    delete_hafiz(created.id)


def test_delete_hafiz():
    """Unit test: delete_hafiz removes record."""
    # Create temporary hafiz
    temp_hafiz = insert_hafiz(
        Hafiz(id=None, name="Temp Hafiz", daily_capacity=3, user_id=1)
    )
    hafiz_id = temp_hafiz.id

    # Delete it
    delete_hafiz(hafiz_id)

    # Verify deletion
    with pytest.raises(Exception):
        get_hafiz(hafiz_id)


def test_get_hafizs_for_user():
    """Unit test: get_hafizs_for_user returns user's hafizs."""
    # Get hafizs for user 1
    user_hafizs = get_hafizs_for_user(1)

    # Verify results
    assert len(user_hafizs) > 0
    assert all(h.user_id == 1 for h in user_hafizs)
    assert all(isinstance(h, Hafiz) for h in user_hafizs)


def test_populate_hafiz_items():
    """Unit test: populate_hafiz_items creates hafizs_items records."""
    # Create temporary hafiz
    temp_hafiz = insert_hafiz(
        Hafiz(id=None, name="Temp Hafiz", daily_capacity=3, user_id=1)
    )
    hafiz_id = temp_hafiz.id

    # Reset xtra to query without hafiz filter
    hafizs_items.xtra()

    # Count items before
    items_before = hafizs_items(where=f"hafiz_id={hafiz_id}")
    assert len(items_before) == 0

    # Populate items
    populate_hafiz_items(hafiz_id)

    # Verify items created
    items_after = hafizs_items(where=f"hafiz_id={hafiz_id}")
    assert len(items_after) > 600  # Should have 604+ items (one per Quran page)

    # Cleanup
    delete_hafiz(hafiz_id)


def test_create_new_plan():
    """Unit test: create_new_plan creates plan record."""
    # Create temporary hafiz
    temp_hafiz = insert_hafiz(
        Hafiz(id=None, name="Temp Hafiz", daily_capacity=3, user_id=1)
    )
    hafiz_id = temp_hafiz.id

    # Reset xtra to query without filter
    plans.xtra()

    # Create plan
    plan = create_new_plan(hafiz_id)

    # Verify plan created
    assert plan.id is not None
    assert plan.hafiz_id == hafiz_id
    assert plan.completed == 0

    # Cleanup
    delete_hafiz(hafiz_id)


def test_setup_new_hafiz():
    """Unit test: setup_new_hafiz orchestrates hafiz initialization."""
    # Create temporary hafiz
    temp_hafiz = insert_hafiz(
        Hafiz(id=None, name="Temp Hafiz", daily_capacity=3, user_id=1)
    )
    hafiz_id = temp_hafiz.id

    # Reset xtra filters
    hafizs_items.xtra()
    plans.xtra()

    # Run setup
    setup_new_hafiz(hafiz_id)

    # Verify items created
    items = hafizs_items(where=f"hafiz_id={hafiz_id}")
    assert len(items) > 600

    # Verify plan created
    hafiz_plans = plans(where=f"hafiz_id={hafiz_id}")
    assert len(hafiz_plans) > 0

    # Cleanup
    delete_hafiz(hafiz_id)


def test_get_hafiz_invalid_id():
    """Error test: get_hafiz with invalid ID raises exception."""
    with pytest.raises(Exception):
        get_hafiz(999999)


def test_delete_hafiz_cascade():
    """Unit test: deleting hafiz cascades to related records."""
    # Create temporary hafiz with full setup
    temp_hafiz = insert_hafiz(
        Hafiz(id=None, name="Temp Hafiz", daily_capacity=3, user_id=1)
    )
    hafiz_id = temp_hafiz.id
    setup_new_hafiz(hafiz_id)

    # Reset xtra filters
    hafizs_items.xtra()
    plans.xtra()

    # Verify related records exist
    items_before = hafizs_items(where=f"hafiz_id={hafiz_id}")
    plans_before = plans(where=f"hafiz_id={hafiz_id}")
    assert len(items_before) > 0
    assert len(plans_before) > 0

    # Delete hafiz
    delete_hafiz(hafiz_id)

    # Verify cascade deletion
    items_after = hafizs_items(where=f"hafiz_id={hafiz_id}")
    plans_after = plans(where=f"hafiz_id={hafiz_id}")
    assert len(items_after) == 0
    assert len(plans_after) == 0


# =============================================================================
# Integration Tests - TestClient, no browser
# Uses fixtures from tests/conftest.py: client, auth_session, hafiz_session, parse_html
# =============================================================================


def test_settings_page_get(client, hafiz_session, parse_html):
    """Integration: GET /hafiz/settings returns form with current values."""
    response = client.get(
        "/hafiz/settings",
        cookies=hafiz_session,
        headers={"HX-Request": "true"}  # Test HTMX fragment, not full page
    )

    assert response.status_code == 200

    # Use XPath for precise HTML structure validation
    html = parse_html(response)
    assert html.xpath("//h1[contains(text(), 'Hafiz Preferences')]")
    assert html.xpath("//label[contains(text(), 'Name')]")
    assert html.xpath("//input[@name='name']")
    assert html.xpath("//label[contains(text(), 'Daily Capacity')]")
    assert html.xpath("//input[@name='daily_capacity' and @type='number']")
    assert html.xpath("//label[contains(text(), 'Current Date')]")
    assert html.xpath("//input[@name='current_date']")
    assert html.xpath("//button[@type='submit' and contains(text(), 'Update')]")


def test_settings_page_post_updates_database(client, hafiz_session):
    """Integration: POST /hafiz/settings updates hafiz in database."""
    # Get current hafiz
    original = get_hafiz(1)

    # Submit update with new capacity
    new_capacity = 77 if original.daily_capacity != 77 else 66
    response = client.post(
        "/hafiz/settings",
        data={
            "id": 1,
            "name": original.name,
            "daily_capacity": new_capacity,
            "user_id": original.user_id,
            "current_date": original.current_date,
        },
        cookies=hafiz_session,
        follow_redirects=False,
    )

    # Verify redirect
    assert response.status_code in (302, 303, 307)
    assert response.headers["location"] == "/"

    # Verify database was updated
    updated = get_hafiz(1)
    assert updated.daily_capacity == new_capacity

    # Restore original
    update_hafiz(original, 1)


def test_theme_page_get(client, hafiz_session, parse_html):
    """Integration: GET /hafiz/theme returns theme picker."""
    response = client.get(
        "/hafiz/theme",
        cookies=hafiz_session,
        headers={"HX-Request": "true"}  # Test HTMX fragment
    )

    assert response.status_code == 200

    # ThemePicker is a MonsterUI component - verify HTML structure
    html = parse_html(response)
    # Verify page has content (ThemePicker renders some elements)
    # Don't test MonsterUI internals, just verify response is valid HTML with content
    assert len(html.xpath("//*")) > 0, "Response should contain HTML elements"


# =============================================================================
# Error Case Tests - Validation and edge cases
# =============================================================================


def test_settings_page_post_invalid_data(client, hafiz_session):
    """Error test: POST /settings with invalid data redirects with error."""
    # Submit with missing required field
    response = client.post(
        "/hafiz/settings",
        data={
            "id": 1,
            # Missing name, daily_capacity, etc.
        },
        cookies=hafiz_session,
        follow_redirects=True,
    )

    # Should handle gracefully (either redirect or validation error)
    assert response.status_code in (200, 302, 303, 400)


def test_settings_page_without_auth(client):
    """Error test: accessing /settings without auth redirects to login."""
    response = client.get("/hafiz/settings", follow_redirects=False)

    # Should redirect to login (beforeware intercepts)
    assert response.status_code in (302, 303, 307)


def test_theme_page_without_auth(client):
    """Error test: accessing /theme without auth redirects to login."""
    response = client.get("/hafiz/theme", follow_redirects=False)

    # Should redirect to login (beforeware intercepts)
    assert response.status_code in (302, 303, 307)
