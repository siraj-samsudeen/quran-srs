"""
Hafiz Module Tests

Unit tests and integration tests for hafiz module.
Tests model functions and routes without browser.
"""

import os
import pytest
import lxml.html
from starlette.testclient import TestClient
from dotenv import load_dotenv

os.environ["ENV"] = "test"
load_dotenv()

from app.hafiz_model import Hafiz, get_hafiz, update_hafiz


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


# =============================================================================
# Integration Tests - TestClient, no browser
# =============================================================================


@pytest.fixture
def client():
    """Create test client for the app."""
    from main import app
    return TestClient(app)


@pytest.fixture
def auth_session(client):
    """Login and return authenticated session cookies."""
    response = client.post("/users/login", data={
        "email": os.getenv("TEST_EMAIL"),
        "password": os.getenv("TEST_PASSWORD"),
    })
    return response.cookies


@pytest.fixture
def hafiz_session(client, auth_session):
    """Select hafiz and return session with both user and hafiz auth."""
    # Select hafiz by posting to hafiz_selection
    response = client.post(
        "/users/hafiz_selection",
        data={"current_hafiz_id": "1"},
        cookies=auth_session,
        follow_redirects=False,
    )
    # Merge cookies from both auth and hafiz selection
    all_cookies = {**auth_session, **response.cookies}
    return all_cookies


@pytest.fixture
def parse_html():
    """Parse HTML response to lxml tree for XPath queries."""
    def _parse(response):
        return lxml.html.fromstring(response.text)
    return _parse


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
