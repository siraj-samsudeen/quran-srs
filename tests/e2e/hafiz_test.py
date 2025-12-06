"""
Tests for Hafiz Management functionality.

Tests the hafiz settings and selection:
- Access settings page
- Update hafiz settings (daily capacity)
- Switch between multiple hafizs
"""

import os
import pytest
from playwright.sync_api import expect
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def authenticated_page(page):
    """Login with credentials from .env and select hafiz."""
    email = os.getenv("TEST_EMAIL")
    password = os.getenv("TEST_PASSWORD")
    hafiz = os.getenv("TEST_HAFIZ")

    page.goto("/users/login")
    page.fill("input[name='email']", email)
    page.fill("input[name='password']", password)
    page.click("button[type='submit']")

    # After login, select hafiz to go to home page
    page.click(f"button:has-text('{hafiz}')")

    # Wait for home page to load
    expect(page.locator("text=System Date")).to_be_visible()

    yield page


def test_settings_page_loads(authenticated_page):
    """
    Settings page loads with the expected form fields.
    """
    page = authenticated_page

    # Navigate to Settings page
    page.click("a:has-text('Settings')")

    # Wait for the settings page to load
    expect(page.locator("h1:has-text('Hafiz Preferences')")).to_be_visible()

    # Verify form fields are visible
    expect(page.locator("label:has-text('Name')")).to_be_visible()
    expect(page.locator("label:has-text('Daily Capacity')")).to_be_visible()
    expect(page.locator("label:has-text('Current Date')")).to_be_visible()

    # Verify Update button is visible
    expect(page.locator("button:has-text('Update')")).to_be_visible()


def test_settings_update_daily_capacity(authenticated_page):
    """
    Updating daily capacity saves the new value.
    """
    page = authenticated_page

    # Navigate to Settings page
    page.click("a:has-text('Settings')")
    expect(page.locator("h1:has-text('Hafiz Preferences')")).to_be_visible()

    # Get current daily capacity
    capacity_input = page.locator("input[id='daily_capacity']")
    current_capacity = capacity_input.input_value()

    # Calculate a new value (toggle between 3 and 4 to ensure change)
    new_capacity = "4" if current_capacity == "3" else "3"

    # Clear and set new value
    capacity_input.fill(new_capacity)

    # Submit the form
    page.click("button:has-text('Update')")

    # Wait for redirect back to home
    page.wait_for_load_state("networkidle")
    expect(page.locator("text=System Date")).to_be_visible()

    # Go back to settings and verify the value was saved
    page.click("a:has-text('Settings')")
    expect(page.locator("h1:has-text('Hafiz Preferences')")).to_be_visible()

    updated_input = page.locator("input[id='daily_capacity']")
    expect(updated_input).to_have_value(new_capacity)


def test_hafiz_selection_page_accessible(authenticated_page):
    """
    Hafiz selection page is accessible from the navbar.
    """
    page = authenticated_page

    # Click on the hafiz name in the navbar to go to selection page
    page.click("a[href='/users/hafiz_selection']")

    # Wait for the selection page to load
    page.wait_for_load_state("networkidle")

    # Verify we're on the selection page - look for add hafiz form
    expect(page.locator("input[name='name']")).to_be_visible()
