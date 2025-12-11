"""
Alpine.js Interactive Features

Tests for client-side JavaScript interactions powered by Alpine.js:
- Tab switching
- Bulk selection UI (checkboxes, count updates)
- Dynamic UI state management

E2E Test Setup:
- Requires app running at BASE_URL (default: http://localhost:5001)
- Uses real user credentials from .env: TEST_EMAIL, TEST_PASSWORD, TEST_HAFIZ
- Works with dev database (real prod data) - no isolation needed

Run: uv run pytest tests/e2e -v
"""

import os
import re
import pytest
from playwright.sync_api import Page, expect
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# Tab Switching Tests (Alpine.js x-show)
# ============================================================================


def test_full_cycle_tab_is_active_by_default(authenticated_page: Page):
    """Full Cycle tab is active on page load."""
    fc_tab = authenticated_page.get_by_role("tab", name="Full cycle")
    expect(fc_tab).to_be_visible()
    expect(authenticated_page.get_by_role("table").first).to_be_visible()


def test_clicking_srs_tab_activates_it(authenticated_page: Page):
    """Clicking SRS tab applies the active class."""
    srs_tab = authenticated_page.get_by_role("tab", name="SRS - Variable Reps")
    srs_tab.click()
    expect(srs_tab).to_have_class(re.compile(r"tab-active"))


def test_switching_tabs_shows_correct_mode_content(authenticated_page: Page):
    """Tab switching changes active state correctly."""
    page = authenticated_page

    fc_tab = page.get_by_role("tab", name="Full Cycle")
    expect(fc_tab).to_have_class(re.compile(r"tab-active"))

    srs_tab = page.get_by_role("tab", name="SRS", exact=False)
    if srs_tab.is_visible():
        srs_tab.click()
        expect(srs_tab).to_have_class(re.compile(r"tab-active"))
        expect(fc_tab).not_to_have_class(re.compile(r"tab-active"))


# ============================================================================
# Bulk Selection Tests (Alpine.js @change handlers)
# ============================================================================


def test_bulk_action_bar_shows_when_checkbox_selected(authenticated_page: Page):
    """Bulk action bar appears when checking a checkbox."""
    page = authenticated_page

    bulk_bar = page.locator("text=Selected:").first
    expect(bulk_bar).not_to_be_visible()

    # Note: Using CSS class selector because checkboxes don't have accessible labels
    page.locator(".bulk-select-checkbox").first.click()

    expect(bulk_bar).to_be_visible()
    expect(page.locator("text=Selected: 1").first).to_be_visible()
    expect(page.get_by_role("button", name="Good").first).to_be_visible()
    expect(page.get_by_role("button", name="Ok").first).to_be_visible()
    expect(page.get_by_role("button", name="Bad").first).to_be_visible()


def test_bulk_action_bar_count_updates_with_multiple_selections(
    authenticated_page: Page, base_url: str
):
    """Count updates as checkboxes are checked/unchecked.

    Note: If fewer than 2 items in Full Cycle mode, will delete revisions to create test data.
    """
    page = authenticated_page

    visible_checkboxes = get_visible_checkboxes(page)

    # If insufficient data, create it by deleting revisions
    if len(visible_checkboxes) < 2:
        ensure_minimum_items_for_bulk_test(page, base_url, minimum=5)
        # Return to home and re-check
        page.goto(base_url)
        expect(page.get_by_text("System Date")).to_be_visible()
        visible_checkboxes = get_visible_checkboxes(page)

    visible_checkboxes[0].click()
    expect(page.get_by_text("Selected: 1")).to_be_visible()

    visible_checkboxes[1].click()
    expect(page.get_by_text("Selected: 2")).to_be_visible()

    visible_checkboxes[0].click()
    expect(page.get_by_text("Selected: 1")).to_be_visible()


def test_bulk_action_bar_hides_when_all_unchecked(authenticated_page: Page):
    """Bulk action bar disappears when all checkboxes are unchecked."""
    page = authenticated_page

    # Note: Using CSS class selector because checkboxes don't have accessible labels
    checkbox = page.locator(".bulk-select-checkbox").first
    checkbox.click()

    bulk_bar = page.locator("text=Selected:").first
    expect(bulk_bar).to_be_visible()

    # Note: Using evaluate() because bulk bar overlay blocks checkbox click
    page.evaluate(
        """
        const cb = document.querySelector('.bulk-select-checkbox:checked');
        cb.checked = false;
        cb.dispatchEvent(new Event('change', { bubbles: true }));
    """
    )

    expect(bulk_bar).not_to_be_visible()


def test_select_all_checkbox_selects_all_unrated_items(authenticated_page: Page):
    """Select-all checkbox checks all visible checkboxes."""
    page = authenticated_page

    visible_count = len(get_visible_checkboxes(page))

    # Note: Using CSS class selector because select-all doesn't have accessible label
    page.locator(".select-all-checkbox").first.click()

    expect(page.get_by_text(f"Selected: {visible_count}")).to_be_visible()

    # Note: Using CSS class selector because checkboxes don't have accessible labels
    all_checkboxes = page.locator(".bulk-select-checkbox")
    for i in range(all_checkboxes.count()):
        if all_checkboxes.nth(i).is_visible():
            expect(all_checkboxes.nth(i)).to_be_checked()


def test_select_all_checkbox_unchecks_all(authenticated_page: Page):
    """Clicking select-all again unchecks all checkboxes."""
    page = authenticated_page

    # Note: Using CSS class selector because select-all doesn't have accessible label
    select_all = page.locator(".select-all-checkbox").first
    select_all.click()

    bulk_bar = page.locator("text=Selected:").first
    expect(bulk_bar).to_be_visible()

    select_all.click()
    expect(bulk_bar).not_to_be_visible()


def test_bulk_action_bar_hides_after_rating_applied(authenticated_page: Page):
    """Bulk action bar disappears after rating is applied via HTMX."""
    page = authenticated_page

    # Note: Using CSS class selector because checkboxes don't have accessible labels
    page.locator(".bulk-select-checkbox").first.click()

    bulk_bar = page.locator("text=Selected:").first
    expect(bulk_bar).to_be_visible()

    page.get_by_role("button", name="Good").first.click()

    page.wait_for_timeout(500)
    expect(bulk_bar).not_to_be_visible()


# ============================================================================
# Helper Functions (Implementation Details)
# ============================================================================


def login_and_select_hafiz(page: Page, base_url: str):
    """Login and select hafiz to access home page."""
    email = os.getenv("TEST_EMAIL")
    password = os.getenv("TEST_PASSWORD")
    hafiz = os.getenv("TEST_HAFIZ")

    page.goto(f"{base_url}/users/login")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Login").click()
    page.wait_for_url("**/hafiz/selection")
    page.get_by_role("button", name=hafiz).click()
    page.wait_for_url(f"{base_url}/")


def get_visible_checkboxes(page: Page):
    """Get list of checkboxes that are currently visible (active tab only).

    Note: Using CSS class selector because checkboxes don't have accessible labels.
    """
    all_checkboxes = page.locator(".bulk-select-checkbox")
    visible = []
    for i in range(all_checkboxes.count()):
        if all_checkboxes.nth(i).is_visible():
            visible.append(all_checkboxes.nth(i))
    return visible


def ensure_minimum_items_for_bulk_test(page: Page, base_url: str, minimum: int = 2):
    """Delete revisions to ensure at least `minimum` items appear in Full Cycle mode."""
    page.on("dialog", lambda dialog: dialog.accept())

    page.goto(f"{base_url}/revision/")

    # Check the first N checkboxes
    checkboxes = page.locator("input[type='checkbox']")
    for i in range(min(minimum, checkboxes.count())):
        checkboxes.nth(i).check()

    # Click Bulk Delete
    page.get_by_role("button", name="Bulk Delete").click()

    # Wait for navigation back to home
    page.wait_for_timeout(500)


# ============================================================================
# Fixtures (Test Setup)
# ============================================================================


@pytest.fixture
def authenticated_page(page: Page, base_url: str):
    """Authenticated page at home with hafiz selected."""
    login_and_select_hafiz(page, base_url)
    expect(page.get_by_text("System Date")).to_be_visible()
    yield page
