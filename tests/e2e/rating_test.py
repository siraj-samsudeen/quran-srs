"""
Tests for individual rating operations.

Tests the rating dropdown functionality:
- Add rating via dropdown (new revision)
- Change rating (update existing)
- Unrate (delete revision)
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


def test_individual_rating_adds_revision_via_dropdown(authenticated_page):
    """
    Selecting a rating from dropdown on an unrated item:
    - Creates a new revision
    - Row background changes to reflect rating color
    """
    page = authenticated_page

    # Find an unrated item (dropdown shows "-")
    unrated_dropdown = page.locator("select.select-bordered:has(option[value='None']:checked)").first

    if not unrated_dropdown.is_visible():
        pytest.skip("No unrated items available in current view")

    # Get the row ID before making changes
    row = unrated_dropdown.locator("xpath=ancestor::tr")
    row_id = row.get_attribute("id")

    # Select "Good" rating
    unrated_dropdown.select_option("1")

    # Wait for HTMX swap to complete
    page.wait_for_load_state("networkidle")

    # Verify the row now has green background (Good rating)
    # The row is replaced by HTMX, so we find it by ID again
    row_after = page.locator(f"#{row_id}")
    expect(row_after).to_have_class(re.compile(r"bg-green-100"))


def test_individual_rating_change_updates_revision(authenticated_page):
    """
    Changing rating on an already-rated item:
    - Updates the revision
    - Row background color changes accordingly
    """
    page = authenticated_page

    # Find a rated item (not showing "-" selected)
    # First, look for green rows (Good rating)
    green_row = page.locator("tr.bg-green-100").first

    if not green_row.is_visible():
        # Try to find any rated row
        yellow_row = page.locator("tr.bg-yellow-50").first
        if yellow_row.is_visible():
            rated_row = yellow_row
        else:
            red_row = page.locator("tr.bg-red-50").first
            if red_row.is_visible():
                rated_row = red_row
            else:
                pytest.skip("No rated items available to test rating change")
    else:
        rated_row = green_row

    # Get the row ID before making changes (HTMX replaces the entire row)
    row_id = rated_row.get_attribute("id")

    # Get the dropdown in this row
    dropdown = rated_row.locator("select.select-bordered")

    # Change to "Bad" rating (-1)
    dropdown.select_option("-1")

    # Wait for HTMX swap to complete
    page.wait_for_load_state("networkidle")

    # Verify the row now has red background (find by ID since HTMX replaced it)
    updated_row = page.locator(f"#{row_id}")
    expect(updated_row).to_have_class(re.compile(r"bg-red-50"))


def test_unrating_removes_revision(authenticated_page):
    """
    Selecting "-" (None) on a rated item:
    - Deletes the revision
    - Row returns to unrated state (no background color)
    """
    page = authenticated_page

    # Find any rated row
    rated_row = None
    for color_class in ["bg-green-100", "bg-yellow-50", "bg-red-50"]:
        row = page.locator(f"tr.{color_class}").first
        if row.is_visible():
            rated_row = row
            break

    if rated_row is None:
        pytest.skip("No rated items available to test unrating")

    row_id = rated_row.get_attribute("id")

    # Get the dropdown and select "-" (None)
    dropdown = rated_row.locator("select.select-bordered")
    dropdown.select_option("None")

    # Wait for HTMX swap to complete
    page.wait_for_load_state("networkidle")

    # Verify the row no longer has any rating background class
    updated_row = page.locator(f"#{row_id}")
    expect(updated_row).not_to_have_class(re.compile(r"bg-green-100"))
    expect(updated_row).not_to_have_class(re.compile(r"bg-yellow-50"))
    expect(updated_row).not_to_have_class(re.compile(r"bg-red-50"))

    # Verify the checkbox is now visible (unrated items have checkboxes)
    checkbox = updated_row.locator(".bulk-select-checkbox")
    expect(checkbox).to_be_visible()
