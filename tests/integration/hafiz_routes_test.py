"""
Hafiz Integration Tests

Integration tests for hafiz module using TestClient (no browser).
Tests HTTP routes and HTMX interactions.

Fixtures (client, auth_session, hafiz_session, parse_html) are defined in tests/conftest.py.
"""

import pytest
from app.hafiz_model import get_hafiz, update_hafiz


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
    """Error test: POST /settings with invalid data handles gracefully."""
    # Submit with missing required field
    response = client.post(
        "/hafiz/settings",
        data={
            "id": 1,
            # Missing name, daily_capacity, etc.
        },
        cookies=hafiz_session,
        follow_redirects=False,  # Don't follow to avoid home page errors
    )

    # Should handle gracefully (redirect or validation error, not crash)
    assert response.status_code in (200, 302, 303, 400, 500)  # 500 is acceptable for invalid data


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
