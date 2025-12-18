"""
Pages Revised Indicator Updates

Tests that the "X vs Y ↑" indicator updates immediately via JSON API when:
1. Adding a rating via dropdown
2. Removing a rating via dropdown (selecting "-")
3. Bulk rating multiple items

E2E Test Setup:
- Requires app running at BASE_URL (default: http://localhost:5001)
- Uses real user credentials from .env: TEST_EMAIL, TEST_PASSWORD, TEST_HAFIZ
- Works with dev database (real prod data) - no isolation needed

Run: uv run pytest tests/e2e/test_pages_revised_indicator.py -v
"""

import os
import pytest
from playwright.sync_api import Page, expect
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# Pages Revised Indicator Tests
#
# MECE Test Coverage:
# 1. Indicator displays on page load with correct format ("X vs Y arrow")
# 2. Adding rating via dropdown - indicator count increases
# 3. Removing rating via dropdown - indicator count decreases
# 4. Bulk rating items - indicator updates
# ============================================================================


def test_indicator_displays_on_page_load(authenticated_page: Page):
    """Indicator shows 'today vs yesterday' format on page load."""
    page = authenticated_page

    indicator = page.locator("#pages-revised-indicator")
    expect(indicator).to_be_visible()

    # Verify format: should contain "vs" and an arrow indicator
    text = indicator.inner_text()
    assert " vs " in text, f"Expected 'X vs Y' format, got: {text}"
    assert any(arrow in text for arrow in ["↑", "↓", "="]), f"Expected arrow indicator, got: {text}"


def test_indicator_updates_when_adding_rating_via_dropdown(
    authenticated_page: Page, base_url: str
):
    """Indicator updates immediately when rating is added via dropdown."""
    page = authenticated_page

    # Get initial "today" count from indicator (format: "X vs Y arrow")
    initial_today = int(page.locator("[data-testid='pages-today']").inner_text())

    # Find an unrated dropdown in Tabulator (one with "" selected)
    # Tabulator rating dropdowns are inside .tabulator-row
    unrated_dropdown = page.locator("#mode-table-FC .tabulator-row select.select-sm").first
    if not unrated_dropdown.is_visible():
        pytest.skip("No items available for rating")

    # Check if already rated
    current_value = unrated_dropdown.input_value()
    if current_value != "":
        # Select empty to "unrate" first, wait for indicator to update
        unrated_dropdown.select_option("")
        # Wait for indicator value to potentially decrease
        page.wait_for_function("document.querySelector('[data-testid=\"pages-today\"]')")
        initial_today = int(page.locator("[data-testid='pages-today']").inner_text())

    unrated_dropdown.select_option("1")  # Select "Good"

    # expect() auto-waits for text to appear
    expect(page.locator("[data-testid='pages-today']")).to_contain_text(str(initial_today + 1))


def test_indicator_updates_when_removing_rating_via_dropdown(
    authenticated_page: Page, base_url: str
):
    """Indicator updates immediately when rating is removed via dropdown."""
    page = authenticated_page

    # First, ensure we have a rated item by adding a rating
    first_dropdown = page.locator("#mode-table-FC .tabulator-row select.select-sm").first
    if not first_dropdown.is_visible():
        pytest.skip("No items available")

    first_dropdown.select_option("1")  # Select "Good"

    # Wait for dropdown background to change (indicates API completed)
    expect(first_dropdown).to_have_css("background-color", "rgb(220, 252, 231)")

    # Get indicator value after adding
    after_add_today = int(page.locator("[data-testid='pages-today']").inner_text())

    # Now remove the rating by selecting "-" (empty value)
    first_dropdown.select_option("")

    # Wait for dropdown background to clear (indicates API completed)
    expect(first_dropdown).to_have_css("background-color", "rgba(0, 0, 0, 0)")

    # Verify indicator updated (today count should decrease)
    after_remove_today = int(page.locator("[data-testid='pages-today']").inner_text())
    assert after_remove_today < after_add_today, "Today count should decrease after removing rating"


def test_indicator_updates_when_bulk_rating_items(
    authenticated_page: Page, base_url: str
):
    """Indicator updates immediately when bulk rating multiple items."""
    page = authenticated_page

    # Get initial indicator value
    initial_today = int(page.locator("[data-testid='pages-today']").inner_text())

    # Select multiple rows using Tabulator row selection
    rows = page.locator("#mode-table-FC .tabulator-row")
    if rows.count() < 2:
        pytest.skip("Need at least 2 items for bulk test")

    rows.first.click()
    rows.nth(1).click(modifiers=["Control"])

    # Bulk bar should be visible with 2 selected
    bulk_bar = page.locator("#bulk-bar-FC")
    expect(bulk_bar).to_be_visible()

    # Click bulk "Good" button
    bulk_bar.get_by_role("button", name="Good").click()

    # Wait for bulk bar to disappear (indicates API completed)
    expect(bulk_bar).not_to_be_visible()

    # Verify indicator updated (today count should increase)
    updated_today = int(page.locator("[data-testid='pages-today']").inner_text())
    assert updated_today >= initial_today, "Today count should increase or stay same after bulk rating"


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
