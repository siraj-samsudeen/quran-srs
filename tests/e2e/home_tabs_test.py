"""Tests for home page tab switching."""
import os
import re
from playwright.sync_api import Page, expect

TEST_EMAIL = os.getenv("TEST_EMAIL")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")
TEST_HAFIZ = os.getenv("TEST_HAFIZ")


def login(page: Page, base_url: str):
    """Login and select hafiz."""
    page.goto(f"{base_url}/users/login")
    page.fill("input[name='email']", TEST_EMAIL)
    page.fill("input[name='password']", TEST_PASSWORD)
    page.click("button[type='submit']")
    page.wait_for_url("**/hafiz_selection")
    page.click(f"button:has-text('{TEST_HAFIZ}')")
    page.wait_for_url(f"{base_url}/")


def test_full_cycle_tab_is_active_by_default(page: Page, base_url: str):
    """Full Cycle tab is active and shows content on page load."""
    login(page, base_url)

    # Full Cycle tab should be visible
    fc_tab = page.locator("a:has-text('Full cycle')")
    expect(fc_tab).to_be_visible()

    # Table with pages should be visible
    expect(page.locator("table").first).to_be_visible()


def test_clicking_srs_tab_activates_it(page: Page, base_url: str):
    """Clicking SRS tab applies the active class."""
    login(page, base_url)

    # Click SRS tab
    srs_tab = page.locator("a:has-text('SRS - Variable Reps')")
    srs_tab.click()

    # SRS tab should now have tab-active class
    expect(srs_tab).to_have_class(re.compile(r"tab-active"))
