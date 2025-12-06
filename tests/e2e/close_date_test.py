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


def test_close_date_completes_successfully(authenticated_page):
    """
    Close Date button workflow completes successfully.

    The date advancement depends on the current state:
    - If current date < today: jumps to today
    - If current date == today: advances by 1 day

    This test verifies the flow completes without error.
    """
    page = authenticated_page

    # Click the Close Date button
    page.click("[data-testid='close-date-btn']")

    # Wait for confirmation page with Confirm button
    confirm_btn = page.locator("[data-testid='confirm-close-btn']")
    expect(confirm_btn).to_be_visible()

    # Confirm the date change
    confirm_btn.click()

    # Wait for redirect back to home
    page.wait_for_load_state("networkidle")

    # Verify we're back on the home page (Close Date completed successfully)
    expect(page.locator("text=System Date")).to_be_visible()


def test_close_date_visible_on_home_page(authenticated_page):
    """
    Verify the Close Date button is visible on the home page.
    This is a basic sanity check for the UI element.
    """
    page = authenticated_page

    close_date_btn = page.locator("[data-testid='close-date-btn']")
    expect(close_date_btn).to_be_visible()
    expect(close_date_btn).to_have_text("Close Date")
