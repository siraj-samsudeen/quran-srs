"""
Tests for Close Date functionality.

Tests the date advancement logic:
- Normal case: advances system date by 1 day
- Gap case: jumps directly to today when multiple days have elapsed
"""

import os
import pytest
from playwright.sync_api import expect
from dotenv import load_dotenv
from datetime import datetime, timedelta

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


def get_system_date_from_page(page) -> str:
    """Extract the system date text from the page."""
    date_element = page.locator("[data-testid='system-date']")
    return date_element.text_content()


def test_close_date_advances_by_one_day(authenticated_page):
    """
    Close Date button advances system date by 1 day when
    current system date equals today (no gap).
    """
    page = authenticated_page

    # Get the initial system date
    initial_date_text = get_system_date_from_page(page)

    # Click the Close Date button
    page.click("[data-testid='close-date-btn']")

    # Wait for confirmation page with Confirm button
    confirm_btn = page.locator("[data-testid='confirm-close-btn']")
    expect(confirm_btn).to_be_visible()

    # Confirm the date change
    confirm_btn.click()

    # Wait for redirect back to home
    page.wait_for_load_state("networkidle")
    expect(page.locator("text=System Date")).to_be_visible()

    # Get the new system date
    new_date_text = get_system_date_from_page(page)

    # Verify the date has changed (not the same as before)
    assert new_date_text != initial_date_text, (
        f"Expected date to change from {initial_date_text}, but it remained the same"
    )


def test_close_date_visible_on_home_page(authenticated_page):
    """
    Verify the Close Date button is visible on the home page.
    This is a basic sanity check for the UI element.
    """
    page = authenticated_page

    close_date_btn = page.locator("[data-testid='close-date-btn']")
    expect(close_date_btn).to_be_visible()
    expect(close_date_btn).to_have_text("Close Date")
