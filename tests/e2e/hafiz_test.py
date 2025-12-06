"""
Tests for Hafiz Management functionality.

Uses pytest markers for authentication instead of explicit fixtures.
Tests hafiz settings and selection workflows.
"""

import pytest
from playwright.sync_api import expect


@pytest.mark.requires_hafiz(hafiz_id=1)
def test_settings_page_loads(page):
    """Settings page loads with expected form fields."""
    # Navigate to Settings page
    page.click("a:has-text('Settings')")

    # Verify page loaded
    expect(page.locator("h1:has-text('Hafiz Preferences')")).to_be_visible()

    # Verify form fields
    expect(page.locator("label:has-text('Name')")).to_be_visible()
    expect(page.locator("label:has-text('Daily Capacity')")).to_be_visible()
    expect(page.locator("label:has-text('Current Date')")).to_be_visible()
    expect(page.locator("button:has-text('Update')")).to_be_visible()


@pytest.mark.requires_hafiz(hafiz_id=1)
def test_settings_update_daily_capacity(page):
    """Updating daily capacity persists to database."""
    # Navigate to Settings
    page.click("a:has-text('Settings')")
    expect(page.locator("h1:has-text('Hafiz Preferences')")).to_be_visible()

    # Get current capacity
    capacity_input = page.locator("input[id='daily_capacity']")
    current_capacity = capacity_input.input_value()

    # Calculate new value (toggle between 3 and 4)
    new_capacity = "4" if current_capacity == "3" else "3"

    # Update value
    capacity_input.fill(new_capacity)

    # Submit form and validate HTMX redirect
    with page.expect_response("**/hafiz/settings") as response_info:
        page.click("button:has-text('Update')")

    response = response_info.value
    assert response.status in (200, 302, 303)

    # Wait for redirect
    page.wait_for_load_state("networkidle")
    expect(page.locator("text=System Date")).to_be_visible()

    # Verify value persisted
    page.click("a:has-text('Settings')")
    expect(page.locator("h1:has-text('Hafiz Preferences')")).to_be_visible()

    updated_input = page.locator("input[id='daily_capacity']")
    expect(updated_input).to_have_value(new_capacity)


@pytest.mark.requires_hafiz(hafiz_id=1)
def test_hafiz_selection_page_accessible(page):
    """Hafiz selection page accessible from navbar."""
    # Navigate to hafiz selection page
    page.click("a[href='/users/hafiz_selection']")
    page.wait_for_load_state("networkidle")

    # Verify add hafiz form visible
    expect(page.locator("input[name='name']")).to_be_visible()
