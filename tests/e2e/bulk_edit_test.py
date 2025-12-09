"""
Tests for the bulk edit feature on the home page.

On the home page, each unrated item has a checkbox. When you check one or more
checkboxes, a "bulk action bar" appears at the bottom with Good/Ok/Bad buttons
to rate all selected items at once.
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


def test_bulk_action_bar_shows_when_checkbox_selected(authenticated_page):
    """
    When you check a checkbox next to an unrated item, a "bulk action bar"
    appears at the bottom showing "Selected: 1" with Good/Ok/Bad buttons.
    """
    page = authenticated_page

    # Verify bulk action bar is initially hidden (use first since there's one per mode)
    bulk_bar = page.locator("text=Selected:").first
    expect(bulk_bar).not_to_be_visible()

    # Click a checkbox for an unrated item
    checkbox = page.locator(".bulk-select-checkbox").first
    checkbox.click()

    # Verify bulk action bar appears
    expect(bulk_bar).to_be_visible()
    expect(page.locator("text=Selected: 1").first).to_be_visible()

    # Verify action buttons are present (use first since there's one set per mode)
    expect(page.locator("button:has-text('Good')").first).to_be_visible()
    expect(page.locator("button:has-text('Ok')").first).to_be_visible()
    expect(page.locator("button:has-text('Bad')").first).to_be_visible()


def test_bulk_action_bar_count_updates_with_multiple_selections(authenticated_page):
    """
    When you check multiple checkboxes, the count updates: "Selected: 2".
    When you uncheck one, the count goes back to "Selected: 1".
    """
    page = authenticated_page

    # With tabs, only checkboxes in active tab are visible
    # Get visible checkboxes only
    all_checkboxes = page.locator(".bulk-select-checkbox")
    visible_checkboxes = []
    for i in range(all_checkboxes.count()):
        if all_checkboxes.nth(i).is_visible():
            visible_checkboxes.append(all_checkboxes.nth(i))

    # Need at least 2 visible checkboxes for this test
    if len(visible_checkboxes) < 2:
        pytest.skip("Need at least 2 visible checkboxes in active tab")

    # Select first visible checkbox
    visible_checkboxes[0].click()
    expect(page.locator("text=Selected: 1")).to_be_visible()

    # Select second visible checkbox
    visible_checkboxes[1].click()
    expect(page.locator("text=Selected: 2")).to_be_visible()

    # Uncheck first checkbox
    visible_checkboxes[0].click()
    expect(page.locator("text=Selected: 1")).to_be_visible()


def test_bulk_action_bar_hides_when_all_unchecked(authenticated_page):
    """
    When you uncheck all checkboxes, the bulk action bar disappears.
    """
    page = authenticated_page

    # Select a checkbox
    checkbox = page.locator(".bulk-select-checkbox").first
    checkbox.click()

    # Verify bar is visible (use first since there's one per mode)
    bulk_bar = page.locator("text=Selected:").first
    expect(bulk_bar).to_be_visible()

    # Uncheck the checkbox via JS (bar overlay is fixed bottom and blocks normal click)
    # This simulates what the user would do if they could reach the checkbox
    page.evaluate("""
        const cb = document.querySelector('.bulk-select-checkbox:checked');
        cb.checked = false;
        cb.dispatchEvent(new Event('change', { bubbles: true }));
    """)

    # Verify bar is hidden
    expect(bulk_bar).not_to_be_visible()


def test_select_all_checkbox_selects_all_unrated_items(authenticated_page):
    """
    When you click the "select all" checkbox in the table header,
    all item checkboxes get checked and the count shows the total.
    """
    page = authenticated_page

    # With tabs UI, only one mode is visible at a time.
    # Count visible checkboxes in the active tab.
    all_checkboxes = page.locator(".bulk-select-checkbox")
    visible_count = 0
    for i in range(all_checkboxes.count()):
        if all_checkboxes.nth(i).is_visible():
            visible_count += 1

    # Click select-all (first visible one)
    select_all = page.locator(".select-all-checkbox").first
    select_all.click()

    # Verify count matches visible unrated items
    expect(page.locator(f"text=Selected: {visible_count}")).to_be_visible()

    # Verify all visible checkboxes are checked
    for i in range(all_checkboxes.count()):
        if all_checkboxes.nth(i).is_visible():
            expect(all_checkboxes.nth(i)).to_be_checked()


def test_select_all_checkbox_unchecks_all(authenticated_page):
    """
    When you click "select all" again (after selecting all),
    all checkboxes get unchecked and the bulk action bar disappears.
    """
    page = authenticated_page

    # Click select-all to select all
    select_all = page.locator(".select-all-checkbox").first
    select_all.click()

    # Verify bar is visible (use first since there's one per mode)
    bulk_bar = page.locator("text=Selected:").first
    expect(bulk_bar).to_be_visible()

    # Click select-all again to uncheck all
    select_all.click()

    # Verify bar is hidden
    expect(bulk_bar).not_to_be_visible()


def test_bulk_action_bar_hides_after_rating_applied(authenticated_page):
    """
    When you click Good/Ok/Bad, the bulk action bar disappears after
    HTMX swaps in the updated content (no "Selected: 0" visible).
    """
    page = authenticated_page

    # Select a checkbox to show the bulk bar
    checkbox = page.locator(".bulk-select-checkbox").first
    checkbox.click()

    # Verify bar is visible
    bulk_bar = page.locator("text=Selected:").first
    expect(bulk_bar).to_be_visible()

    # Click Good button to apply rating
    good_btn = page.locator("button:has-text('Good')").first
    good_btn.click()

    # Wait for HTMX swap to complete (table gets replaced)
    page.wait_for_timeout(500)

    # Verify bar is hidden (not showing "Selected: 0")
    expect(bulk_bar).not_to_be_visible()


def test_switching_tabs_shows_correct_mode_content(authenticated_page):
    """
    The home page uses tabs (not accordion). Clicking a tab switches
    to that mode's content.
    """
    page = authenticated_page

    # Default tab is Full Cycle (FC)
    fc_tab = page.locator("a.tab:has-text('Full Cycle')")
    expect(fc_tab).to_have_class(re.compile(r"tab-active"))

    # Click SRS tab (if visible)
    srs_tab = page.locator("a.tab:has-text('SRS')")
    if srs_tab.is_visible():
        srs_tab.click()
        expect(srs_tab).to_have_class(re.compile(r"tab-active"))
        # Full Cycle tab should no longer be active
        expect(fc_tab).not_to_have_class(re.compile(r"tab-active"))

    # Click Daily Reps tab (if visible)
    dr_tab = page.locator("a.tab:has-text('Daily Reps')")
    if dr_tab.is_visible():
        dr_tab.click()
        expect(dr_tab).to_have_class(re.compile(r"tab-active"))
