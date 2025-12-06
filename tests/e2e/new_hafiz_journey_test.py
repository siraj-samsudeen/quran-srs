"""
Journey Test: New Hafiz Day 1

Tests the complete flow for a new user:
1. Signup
2. Login
3. Create hafiz profile
4. Navigate to home page
5. Cleanup (delete hafiz)

All interactions through UI only - no direct DB access.
"""

import time
import pytest
from playwright.sync_api import expect, Page


# Generate unique test data to avoid conflicts
TEST_TIMESTAMP = int(time.time() * 1000)
TEST_EMAIL = f"journey_test_{TEST_TIMESTAMP}@example.com"
TEST_PASSWORD = "testpassword123"
TEST_NAME = "Journey Test User"
TEST_HAFIZ_NAME = f"Test Hafiz {TEST_TIMESTAMP}"


def test_new_hafiz_journey(page: Page):
    """
    Complete journey: Signup -> Login -> Create Hafiz -> Home Page -> Cleanup
    """
    # Step 1: Signup
    page.goto("http://localhost:5001/users/signup")
    page.get_by_label("Name").fill(TEST_NAME)
    page.get_by_label("Email").fill(TEST_EMAIL)
    page.get_by_label("Password", exact=True).fill(TEST_PASSWORD)
    page.get_by_label("Confirm Password").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Signup").click()

    # Should redirect to login after signup
    expect(page).to_have_url("http://localhost:5001/users/login")

    # Step 2: Login
    page.get_by_label("Email").fill(TEST_EMAIL)
    page.get_by_label("Password").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Login").click()

    # Should redirect to hafiz selection (no hafiz yet)
    expect(page).to_have_url("http://localhost:5001/users/hafiz_selection")
    expect(page.get_by_role("heading", name="Hafiz Selection")).to_be_visible()

    # Step 3: Create hafiz profile
    page.get_by_label("Name").fill(TEST_HAFIZ_NAME)
    page.get_by_label("Daily Capacity").fill("5")
    page.get_by_role("button", name="Add Hafiz").click()

    # Should stay on hafiz selection, now showing the new hafiz
    expect(page).to_have_url("http://localhost:5001/users/hafiz_selection")
    expect(page.get_by_test_id(f"hafiz-switch-{TEST_HAFIZ_NAME}")).to_be_visible()

    # Step 4: Select the hafiz to go to home page
    page.get_by_test_id(f"hafiz-switch-{TEST_HAFIZ_NAME}").click()

    # Should be on home page with system date visible
    expect(page.get_by_text("System Date:")).to_be_visible()

    # Step 5: Cleanup - logout first (current hafiz can't be deleted)
    page.goto("http://localhost:5001/users/logout")

    # Login again
    page.get_by_label("Email").fill(TEST_EMAIL)
    page.get_by_label("Password").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Login").click()

    # Now on hafiz selection, hafiz is NOT current (auth cleared on logout)
    expect(page).to_have_url("http://localhost:5001/users/hafiz_selection")

    # Handle the confirmation dialog (must be set BEFORE triggering action)
    page.on("dialog", lambda dialog: dialog.accept())

    # Open the menu for this hafiz (Alpine.js dropdown)
    page.get_by_test_id(f"hafiz-menu-{TEST_HAFIZ_NAME}").click()

    # Wait for delete button to be visible (Alpine.js x-show)
    delete_button = page.get_by_test_id(f"hafiz-delete-{TEST_HAFIZ_NAME}")
    expect(delete_button).to_be_visible()

    # Click delete
    delete_button.click()
    page.wait_for_load_state("networkidle")

    # Hafiz should be deleted - button no longer visible
    expect(page.get_by_test_id(f"hafiz-switch-{TEST_HAFIZ_NAME}")).not_to_be_visible()
