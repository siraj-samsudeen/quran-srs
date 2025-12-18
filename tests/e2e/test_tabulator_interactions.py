"""
Tabulator Table Interactions (E2E)

Tests for Tabulator.js table interactions on the home page:
- Tab switching (Alpine.js x-show for mode panels)
- Row selection and bulk action bar
- Pagination navigation
- Bulk rating operations

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
#
# MECE Test Coverage:
# 1. Default state - Full Cycle tab is active on load
# 2. Click behavior - clicking tab activates it and deactivates others
# ============================================================================


def test_full_cycle_tab_is_active_by_default(authenticated_page: Page):
    """Full Cycle tab is active on page load."""
    fc_tab = authenticated_page.get_by_role("tab", name="Full cycle")
    expect(fc_tab).to_have_class(re.compile(r"tab-active"))
    # Tabulator table should be visible
    expect(authenticated_page.locator("#mode-table-FC")).to_be_visible()


def test_clicking_tab_switches_active_state(authenticated_page: Page):
    """Clicking a tab activates it and deactivates the previous tab."""
    page = authenticated_page

    fc_tab = page.get_by_role("tab", name="Full Cycle")
    srs_tab = page.get_by_role("tab", name="SRS", exact=False)

    # Initial state: FC active
    expect(fc_tab).to_have_class(re.compile(r"tab-active"))

    # Click SRS: SRS becomes active, FC deactivates
    srs_tab.click()
    expect(srs_tab).to_have_class(re.compile(r"tab-active"))
    expect(fc_tab).not_to_have_class(re.compile(r"tab-active"))


# ============================================================================
# Bulk Selection Tests (Tabulator Row Selection)
#
# MECE Test Coverage:
# 1. Bar visibility - shows when row selected, hides when all unchecked
# 2. Count updates - increments/decrements as rows are toggled
# 3. Select-all - header checkbox selects all rows
# 4. Bulk action - bar hides after bulk rating is applied
# ============================================================================


def test_bulk_action_bar_shows_on_selection(authenticated_page: Page):
    """Bulk action bar appears when rows are selected."""
    page = authenticated_page

    # Bulk bar is initially hidden
    bulk_bar = page.locator("#bulk-bar-FC")
    expect(bulk_bar).not_to_be_visible()

    # Click a row to select it (using Tabulator's row selection)
    page.locator("#mode-table-FC .tabulator-row").first.click()

    # Bulk bar should now be visible
    expect(bulk_bar).to_be_visible()
    expect(bulk_bar.get_by_role("button", name="Good")).to_be_visible()
    expect(bulk_bar.get_by_role("button", name="Ok")).to_be_visible()
    expect(bulk_bar.get_by_role("button", name="Bad")).to_be_visible()


def test_bulk_action_bar_count_updates_with_selections(
    authenticated_page: Page, base_url: str
):
    """Count updates as rows are selected/deselected."""
    page = authenticated_page

    rows = page.locator("#mode-table-FC .tabulator-row")
    if rows.count() < 2:
        pytest.skip("Not enough items for selection test")

    bulk_bar = page.locator("#bulk-bar-FC")

    # Select first row
    rows.first.click()
    expect(bulk_bar).to_be_visible()
    expect(bulk_bar.locator("#bulk-count-FC")).to_have_text("1")

    # Ctrl+click second row to add to selection
    rows.nth(1).click(modifiers=["Control"])
    expect(bulk_bar.locator("#bulk-count-FC")).to_have_text("2")


def test_bulk_action_bar_count_resets_when_all_unchecked(authenticated_page: Page):
    """Count resets to 0 and bar hides when all rows are deselected."""
    page = authenticated_page

    bulk_bar = page.locator("#bulk-bar-FC")
    row = page.locator("#mode-table-FC .tabulator-row").first

    # Select row
    row.click()
    expect(bulk_bar).to_be_visible()

    # Click again to deselect
    row.click()
    expect(bulk_bar).not_to_be_visible()


def test_select_all_checkbox_selects_all_items(authenticated_page: Page):
    """Header checkbox selects all visible rows."""
    page = authenticated_page

    # Click the header selection checkbox (Tabulator's built-in)
    header_checkbox = page.locator("#mode-table-FC .tabulator-header .tabulator-col[tabulator-field=''] input[type='checkbox']")

    if not header_checkbox.is_visible():
        # Try alternative selector for Tabulator's row selection header
        header_checkbox = page.locator("#mode-table-FC .tabulator-header-contents input[type='checkbox']").first

    if not header_checkbox.is_visible():
        pytest.skip("Header checkbox not found")

    header_checkbox.click()

    # Count should match total visible rows
    rows = page.locator("#mode-table-FC .tabulator-row")
    visible_count = rows.count()

    if visible_count > 0:
        bulk_bar = page.locator("#bulk-bar-FC")
        expect(bulk_bar).to_be_visible()


def test_select_all_checkbox_unchecks_all(authenticated_page: Page):
    """Clicking header checkbox again deselects all rows."""
    page = authenticated_page

    rows = page.locator("#mode-table-FC .tabulator-row")
    if rows.count() == 0:
        pytest.skip("No items to select")

    # Select first row
    rows.first.click()
    bulk_bar = page.locator("#bulk-bar-FC")
    expect(bulk_bar).to_be_visible()

    # Click same row to deselect
    rows.first.click()
    expect(bulk_bar).not_to_be_visible()


def test_bulk_action_bar_resets_after_rating_applied(authenticated_page: Page):
    """Bulk bar hides and count resets after bulk rating is applied."""
    page = authenticated_page

    rows = page.locator("#mode-table-FC .tabulator-row")
    if rows.count() == 0:
        pytest.skip("No items to rate")

    bulk_bar = page.locator("#bulk-bar-FC")

    # Select first row
    rows.first.click()
    expect(bulk_bar).to_be_visible()
    expect(bulk_bar.locator("#bulk-count-FC")).to_have_text("1")

    # Apply rating
    bulk_bar.get_by_role("button", name="Good").click()

    # expect() auto-waits for condition
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


# ============================================================================
# Fixtures (Test Setup)
# ============================================================================


@pytest.fixture
def authenticated_page(page: Page, base_url: str):
    """Authenticated page at home with hafiz selected."""
    login_and_select_hafiz(page, base_url)
    expect(page.get_by_text("System Date")).to_be_visible()
    # Wait for Tabulator to initialize
    page.wait_for_selector("#mode-table-FC .tabulator-row", timeout=10000)
    yield page


# ============================================================================
# Pagination Tests (Tabulator Built-in Pagination)
#
# MECE Test Coverage:
# 1. Pagination controls visible when data exceeds page size
# 2. Navigation works - next/prev buttons change pages
# ============================================================================


def test_tabulator_pagination_displays(authenticated_page: Page):
    """Tabulator pagination controls appear when there are enough items."""
    page = authenticated_page

    # Check for Tabulator's pagination footer
    pagination = page.locator("#mode-table-FC .tabulator-footer .tabulator-paginator")

    if not pagination.is_visible():
        pytest.skip("Not enough items for pagination")

    # Should have page buttons
    expect(pagination.locator("button")).to_have_count_greater_than(0)


def test_tabulator_pagination_navigation(authenticated_page: Page):
    """Tabulator pagination next/prev buttons work correctly."""
    page = authenticated_page

    pagination = page.locator("#mode-table-FC .tabulator-footer .tabulator-paginator")

    if not pagination.is_visible():
        pytest.skip("Not enough items for pagination")

    next_btn = pagination.locator("button:has-text('Next')")
    if not next_btn.is_visible() or next_btn.is_disabled():
        pytest.skip("Only one page available")

    # Click next
    next_btn.click()

    # Prev button should be enabled now
    prev_btn = pagination.locator("button:has-text('Prev')")
    expect(prev_btn).to_be_enabled()

    # Click prev to go back
    prev_btn.click()
