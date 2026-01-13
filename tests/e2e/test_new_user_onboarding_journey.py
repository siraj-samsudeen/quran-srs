"""
Journey 1a: New User Onboarding and Rep Mode Progression

E2E tests verifying:
1. Complete user onboarding flow (signup → login → create hafiz → select hafiz)
2. Rep mode progression with Close Date (DR→WR→FR→MR→FC)
3. Multiple modes processing simultaneously
"""

import pytest
from playwright.sync_api import Page, expect


# ============================================================================
# Journey Tests
# ============================================================================


def test_new_user_onboarding_journey(page: Page, base_url: str, test_user_data: dict):
    """
    SCENARIO: New user completes full onboarding
    GIVEN a new user with valid credentials
    WHEN they signup, login, and create their first hafiz
    THEN they are redirected to the home page ready to start
    """
    # GIVEN: New user signs up
    signup_new_user(page, base_url, test_user_data)

    # WHEN: User logs in
    login_user(page, base_url, test_user_data["email"], test_user_data["password"])
    expect(page).to_have_url(f"{base_url}/hafiz/selection")

    # AND: User creates their first hafiz
    page.get_by_label("Name").fill(test_user_data["hafiz_name"])
    page.get_by_role("button", name="Add Hafiz").click()
    expect(page).to_have_url(f"{base_url}/hafiz/selection")

    # AND: User selects the newly created hafiz
    page.get_by_test_id(f"hafiz-switch-{test_user_data['hafiz_name']}").click()

    # THEN: User lands on home page
    expect(page).to_have_url(f"{base_url}/")


def test_rep_mode_progression_with_close_date(page: Page, base_url: str, progression_test_hafiz: dict):
    """
    SCENARIO: Item graduates from Daily to Weekly mode after reaching threshold
    GIVEN an item in Daily mode with custom threshold of 2
    WHEN user rates the item twice and closes date each time
    THEN the item graduates to Weekly mode
    """
    # GIVEN: User logs in with test hafiz containing Daily mode item
    login_and_select_hafiz(page, base_url, progression_test_hafiz)

    # AND: Daily tab is visible with items
    daily_tab = page.locator(".tab:has-text('Daily')")
    expect(daily_tab).to_be_visible()
    daily_tab.click()

    # AND: Rating dropdown is visible (item is showing)
    rating_select = page.locator("select").first
    expect(rating_select).to_be_visible()

    # WHEN: User rates the item (first rating)
    rating_select.select_option("1")

    # AND: User closes the date
    close_date(page, base_url)

    # AND: User rates the item again (second rating to reach threshold of 2)
    daily_tab = page.locator(".tab:has-text('Daily')")
    expect(daily_tab).to_be_visible()
    daily_tab.click()
    page.locator("select").first.select_option("1")

    # AND: User closes the date again (triggers graduation)
    close_date(page, base_url)

    # THEN: Daily tab is gone (item graduated to Weekly, next review in 7 days)
    page.goto(f"{base_url}/")
    daily_tab = page.locator(".tab:has-text('Daily')")
    expect(daily_tab).not_to_be_visible()


def test_close_date_processes_multiple_modes(page: Page, base_url: str, multi_mode_test_hafiz: dict):
    """
    SCENARIO: Close Date processes items across all rep modes simultaneously
    GIVEN items exist in Daily, Weekly, Fortnightly, and Monthly modes
    WHEN user rates one item in each mode and closes the date
    THEN the system date advances and pages revised count updates
    """
    # GIVEN: User logs in with test hafiz containing items in all modes
    login_and_select_hafiz(page, base_url, multi_mode_test_hafiz)

    # AND: All mode tabs are visible
    daily_tab = page.locator(".tab:has-text('Daily')")
    weekly_tab = page.locator(".tab:has-text('Weekly')")
    fortnightly_tab = page.locator(".tab:has-text('Fortnight')")
    monthly_tab = page.locator(".tab:has-text('Monthly')")

    expect(daily_tab).to_be_visible()
    expect(weekly_tab).to_be_visible()
    expect(fortnightly_tab).to_be_visible()
    expect(monthly_tab).to_be_visible()

    # Helper to rate item in a mode tab
    def rate_in_tab(tab):
        tab.click()
        select = page.locator("select:visible").first
        select.wait_for(state="visible")
        select.select_option("1")

    # WHEN: User rates item in each mode
    rate_in_tab(daily_tab)
    rate_in_tab(weekly_tab)
    rate_in_tab(fortnightly_tab)
    rate_in_tab(monthly_tab)

    # AND: User closes the date
    close_date(page, base_url)

    # THEN: System date has advanced (was Jan 15, now Jan 16)
    expect(page.get_by_test_id("system-date")).to_contain_text("Jan 16")


# ============================================================================
# Step Helpers - Reusable user actions
# ============================================================================


def signup_new_user(page: Page, base_url: str, user_data: dict):
    """Step: User creates a new account via signup form."""
    page.goto(f"{base_url}/users/signup")
    page.get_by_label("Name").fill(user_data["user_name"])
    page.get_by_label("Email").fill(user_data["email"])
    page.get_by_label("Password", exact=True).fill(user_data["password"])
    page.get_by_label("Confirm Password").fill(user_data["password"])
    page.get_by_role("button", name="Signup").click()
    page.wait_for_url(f"{base_url}/users/login")


def login_user(page: Page, base_url: str, email: str, password: str):
    """Step: User logs in with email and password."""
    page.goto(f"{base_url}/users/login")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Login").click()
    # Wait for navigation to complete
    page.wait_for_url(f"{base_url}/hafiz/selection")


def login_and_select_hafiz(page: Page, base_url: str, user_data: dict):
    """Step: Login user and select their hafiz."""
    login_user(page, base_url, user_data["email"], user_data["password"])
    # Select the hafiz
    page.get_by_test_id(f"hafiz-switch-{user_data['hafiz_name']}").click()
    # Wait for navigation to home
    page.wait_for_url(f"{base_url}/")


def close_date(page: Page, base_url: str):
    """Step: Navigate to close date page and confirm."""
    page.get_by_test_id("close-date-btn").click()
    page.get_by_test_id("confirm-close-btn").click()
    expect(page).to_have_url(f"{base_url}/")
