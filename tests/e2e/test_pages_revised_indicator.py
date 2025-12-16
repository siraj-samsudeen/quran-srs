"""
Pages Revised Indicator HTMX Updates

Tests that the "X vs Y ↑" indicator updates immediately via HTMX OOB swaps when:
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
# Pages Revised Indicator Tests (HTMX OOB Swaps)
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

    # Find an unrated dropdown (one with "-" selected) and add a rating
    unrated_dropdown = page.locator("select.select-sm:has(option[value='None']:checked)").first
    if not unrated_dropdown.is_visible():
        pytest.skip("No unrated items available")

    unrated_dropdown.select_option("1")  # Select "Good"

    # Verify indicator updated (today count should increase by 1)
    expect(page.locator("[data-testid='pages-today']")).to_contain_text(str(initial_today + 1))


def test_indicator_updates_when_removing_rating_via_dropdown(
    authenticated_page: Page, base_url: str
):
    """Indicator updates immediately when rating is removed via dropdown."""
    page = authenticated_page

    # First, ensure we have a rated item by adding a rating
    first_dropdown = page.locator("select.select-sm").first
    first_dropdown.select_option("1")  # Select "Good"
    page.wait_for_timeout(500)

    # Get indicator value after adding
    indicator = page.locator("#pages-revised-indicator")
    after_add_text = indicator.inner_text()

    # Now remove the rating by selecting "-"
    first_dropdown.select_option("None")
    page.wait_for_timeout(500)

    # Verify indicator updated (should show decrease)
    after_remove_text = indicator.inner_text()
    assert (
        after_remove_text != after_add_text
    ), "Indicator should update after removing rating"


def test_indicator_updates_when_bulk_rating_items(
    authenticated_page: Page, base_url: str
):
    """Indicator updates immediately when bulk rating multiple items."""
    page = authenticated_page

    # Get initial indicator value
    indicator = page.locator("#pages-revised-indicator")
    initial_text = indicator.inner_text()

    # Select multiple visible checkboxes
    visible_checkboxes = get_visible_checkboxes(page)
    if len(visible_checkboxes) < 2:
        pytest.skip("Need at least 2 unrated items for bulk test")

    visible_checkboxes[0].check()
    visible_checkboxes[1].check()

    # Click bulk "Good" button
    page.get_by_role("button", name="Good").click()
    page.wait_for_timeout(500)

    # Verify indicator updated
    updated_text = indicator.inner_text()
    assert updated_text != initial_text, "Indicator should update after bulk rating"


# ============================================================================
# Helper Functions (Implementation Details)
# ============================================================================


def get_visible_checkboxes(page: Page):
    """Get list of checkboxes that are currently visible (active tab only)."""
    all_checkboxes = page.locator(".bulk-select-checkbox")
    visible = []
    for i in range(all_checkboxes.count()):
        if all_checkboxes.nth(i).is_visible():
            visible.append(all_checkboxes.nth(i))
    return visible


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
    yield page

