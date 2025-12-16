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
#
# MECE Test Coverage:
# 1. Default state - Full Cycle tab is active on load
# 2. Click behavior - clicking tab activates it and deactivates others
# ============================================================================


def test_full_cycle_tab_is_active_by_default(authenticated_page: Page):
    """Full Cycle tab is active on page load."""
    fc_tab = authenticated_page.get_by_role("tab", name="Full cycle")
    expect(fc_tab).to_have_class(re.compile(r"tab-active"))
    expect(authenticated_page.get_by_role("table").first).to_be_visible()


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
# Bulk Selection Tests (Alpine.js @change handlers)
#
# MECE Test Coverage:
# 1. Bar visibility - shows when checkbox selected, hides when all unchecked
# 2. Count updates - increments/decrements as checkboxes are toggled
# 3. Select-all - selects all, clicking again deselects all
# 4. HTMX integration - bar hides after bulk rating is applied
# ============================================================================


def test_bulk_action_bar_is_always_visible(authenticated_page: Page):
    """Bulk action bar is always visible with Select All and rating buttons."""
    page = authenticated_page

    # Bulk bar for FC tab is always visible
    bulk_bar = page.locator("#bulk-bar-FC")
    expect(bulk_bar.get_by_text("Select All")).to_be_visible()
    expect(bulk_bar.get_by_role("button", name="Good")).to_be_visible()
    expect(bulk_bar.get_by_role("button", name="Ok")).to_be_visible()
    expect(bulk_bar.get_by_role("button", name="Bad")).to_be_visible()


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

    # Count in bulk bar shows number of selected items (bold text after separator)
    bulk_bar = page.locator("#bulk-bar-FC")

    visible_checkboxes[0].click()
    expect(bulk_bar.locator(".font-bold")).to_have_text("1")

    visible_checkboxes[1].click()
    expect(bulk_bar.locator(".font-bold")).to_have_text("2")

    visible_checkboxes[0].click()
    expect(bulk_bar.locator(".font-bold")).to_have_text("1")


def test_bulk_action_bar_count_resets_when_all_unchecked(authenticated_page: Page):
    """Count resets to 0 when all checkboxes are unchecked."""
    page = authenticated_page

    bulk_bar = page.locator("#bulk-bar-FC")
    checkbox = page.locator(".bulk-select-checkbox").first
    checkbox.click()

    expect(bulk_bar.locator(".font-bold")).to_have_text("1")

    # Uncheck via JavaScript to avoid bulk bar overlay blocking click
    page.evaluate(
        """
        const cb = document.querySelector('.bulk-select-checkbox:checked');
        cb.checked = false;
        cb.dispatchEvent(new Event('change', { bubbles: true }));
    """
    )

    expect(bulk_bar.locator(".font-bold")).to_have_text("0")


def test_select_all_checkbox_selects_all_unrated_items(authenticated_page: Page):
    """Select-all checkbox in bulk bar checks all visible checkboxes."""
    page = authenticated_page

    visible_count = len(get_visible_checkboxes(page))
    bulk_bar = page.locator("#bulk-bar-FC")

    # Click the select-all checkbox in the bulk bar
    bulk_bar.get_by_role("checkbox").click()

    # Count should match total visible checkboxes
    expect(bulk_bar.locator(".font-bold")).to_have_text(str(visible_count))

    # All checkboxes should be checked
    all_checkboxes = page.locator(".bulk-select-checkbox")
    for i in range(all_checkboxes.count()):
        if all_checkboxes.nth(i).is_visible():
            expect(all_checkboxes.nth(i)).to_be_checked()


def test_select_all_checkbox_unchecks_all(authenticated_page: Page):
    """Clicking select-all checkbox again unchecks all checkboxes."""
    page = authenticated_page

    bulk_bar = page.locator("#bulk-bar-FC")
    select_all = bulk_bar.get_by_role("checkbox")

    # Select all
    select_all.click()
    expect(bulk_bar.get_by_text("Clear All")).to_be_visible()

    # Unselect all
    select_all.click()
    expect(bulk_bar.get_by_text("Select All")).to_be_visible()
    expect(bulk_bar.locator(".font-bold")).to_have_text("0")


def test_bulk_action_bar_resets_after_rating_applied(authenticated_page: Page):
    """Count resets to 0 after bulk rating is applied via HTMX."""
    page = authenticated_page

    bulk_bar = page.locator("#bulk-bar-FC")
    page.locator(".bulk-select-checkbox").first.click()

    expect(bulk_bar.locator(".font-bold")).to_have_text("1")

    page.get_by_role("button", name="Good").first.click()

    # After HTMX swap, count should reset to 0
    expect(bulk_bar.locator(".font-bold")).to_have_text("0")


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


# ============================================================================
# Pagination Tests (HTMX + Session State)
#
# MECE Test Coverage:
# 1. Pagination info displays when there are enough items
# 2. Navigation works - next/prev change pages correctly
# 3. First page - prev button is disabled
# ============================================================================


def get_pagination_locators(page: Page, mode_code: str):
    """Return pagination-related locators for a given mode."""
    return {
        "controls": page.locator(f"[data-testid='pagination-controls-{mode_code}']"),
        "next": page.locator(f"[data-testid='pagination-next-{mode_code}']"),
        "prev": page.locator(f"[data-testid='pagination-prev-{mode_code}']"),
        "info": page.locator(f"[data-testid='pagination-info-{mode_code}']"),
        "tbody": page.locator(f"#{mode_code}_tbody tr"),
    }


def test_pagination_info_displays_when_multiple_pages(authenticated_page: Page):
    """Pagination controls and info appear when there are enough items to paginate."""
    page = authenticated_page
    loc = get_pagination_locators(page, "FC")

    if not loc["controls"].is_visible():
        pytest.skip("Not enough items for pagination")

    info_text = loc["info"].text_content()
    assert "Page 1" in info_text


def test_pagination_next_and_prev_navigate_correctly(authenticated_page: Page):
    """Next button advances to next page, Prev button returns to previous page."""
    page = authenticated_page
    loc = get_pagination_locators(page, "FC")

    if not loc["controls"].is_visible():
        pytest.skip("Not enough items for pagination")
    if loc["next"].is_disabled():
        pytest.skip("Only one page available")

    loc["next"].click()
    expect(loc["info"]).to_contain_text("Page 2")

    loc["prev"].click()
    expect(loc["info"]).to_contain_text("Page 1")


def test_pagination_prev_hidden_on_first_page(authenticated_page: Page):
    """Previous button is hidden when on the first page."""
    page = authenticated_page
    loc = get_pagination_locators(page, "FC")

    if not loc["controls"].is_visible():
        pytest.skip("Not enough items for pagination")

    expect(loc["prev"]).not_to_be_visible()


def test_srs_pagination_navigation(authenticated_page: Page):
    """SRS tab pagination works the same as Full Cycle."""
    page = authenticated_page

    srs_tab = page.get_by_role("tab", name="SRS - Variable Reps")
    srs_tab.click()
    expect(srs_tab).to_have_class(re.compile(r"tab-active"))

    loc = get_pagination_locators(page, "SR")

    if not loc["controls"].is_visible():
        pytest.skip("Not enough SRS items for pagination")
    if loc["next"].is_disabled():
        pytest.skip("Only one page of SRS items available")

    expect(loc["prev"]).to_be_disabled()
    loc["next"].click()
    expect(loc["info"]).to_contain_text("Page 2")


def test_bulk_rating_preserves_pagination_controls(authenticated_page: Page):
    """Bulk rating on a paginated page keeps pagination controls visible."""
    page = authenticated_page
    loc = get_pagination_locators(page, "FC")

    if not loc["controls"].is_visible():
        pytest.skip("Not enough items for pagination")

    checkbox = page.locator("#FC_tbody .bulk-select-checkbox").first
    if not checkbox.is_visible():
        pytest.skip("No unrated items to select")

    checkbox.click()
    page.get_by_role("button", name="Good").first.click()

    expect(loc["controls"]).to_be_visible()
    expect(loc["info"]).to_contain_text("Page")


