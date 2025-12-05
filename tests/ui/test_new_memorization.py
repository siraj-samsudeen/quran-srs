"""
Tests for New Memorization workflow.

Tests the new memorization page functionality:
- Navigation to new memorization page
- Tab switching between juz/surah/page views
- Marking pages as newly memorized
"""

import os
import re
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


def test_new_memorization_page_loads(authenticated_page):
    """
    New Memorization page loads with the expected sections.
    """
    page = authenticated_page

    # Navigate to New Memorization page
    page.click("a:has-text('New Memorization')")

    # Wait for the page to load
    expect(page.locator("h1:has-text('New Memorization')")).to_be_visible()

    # Verify both main sections are visible
    expect(page.locator("text=Recently Memorized Pages")).to_be_visible()
    expect(page.locator("text=Select a Page Not Yet Memorized")).to_be_visible()


def test_new_memorization_tab_switching(authenticated_page):
    """
    Tab switching between juz/surah/page views works correctly.
    """
    page = authenticated_page

    # Navigate to New Memorization page (default is surah view)
    page.goto("/new_memorization/surah")

    # Wait for the page to load
    expect(page.locator("h1:has-text('New Memorization')")).to_be_visible()

    # Verify the surah tab is active
    surah_tab = page.locator("li:has-text('by surah')")
    expect(surah_tab).to_have_class(re.compile(r"uk-active"))

    # Click on juz tab
    page.click("a:has-text('by juz')")
    page.wait_for_load_state("networkidle")

    # Verify juz tab is now active
    juz_tab = page.locator("li:has-text('by juz')")
    expect(juz_tab).to_have_class(re.compile(r"uk-active"))

    # Click on page tab
    page.click("a:has-text('by page')")
    page.wait_for_load_state("networkidle")

    # Verify page tab is now active
    page_tab = page.locator("li:has-text('by page')")
    expect(page_tab).to_have_class(re.compile(r"uk-active"))
