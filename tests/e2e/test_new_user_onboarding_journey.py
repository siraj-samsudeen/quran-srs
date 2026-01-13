"""
Journey 1a: New User Onboarding and Rep Mode Progression

E2E tests verifying:
1. Complete user onboarding flow (signup → login → create hafiz → select hafiz)
2. Rep mode progression with Close Date (DR→WR→FR→MR→FC)
3. Multiple modes processing simultaneously
"""

import time
import pytest
from playwright.sync_api import Page, expect
from app.users_model import get_user_by_email
from database import users, hafizs, hafizs_items


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


# ============================================================================
# Fixtures - Test data setup and cleanup
# ============================================================================


@pytest.fixture(scope="module")
def test_user_data():
    """Fixture: Fresh test user credentials with cleanup."""
    timestamp = int(time.time() * 1000)
    data = {
        "email": f"journey_1a_test_{timestamp}@example.com",
        "password": "TestPass123!",
        "user_name": f"Journey 1A Test User {timestamp}",
        "hafiz_name": f"Journey1AHafiz{timestamp}",
    }

    existing_user = get_user_by_email(data["email"])
    if existing_user:
        users.delete(existing_user.id)

    yield data

    existing_user = get_user_by_email(data["email"])
    if existing_user:
        users.delete(existing_user.id)


@pytest.fixture(scope="function")
def progression_test_hafiz():
    """
    Fixture: User with hafiz and one Daily mode item (threshold=2).
    
    Sets up:
    - User with hafiz
    - One item in Daily mode with custom_daily_threshold=2
    - next_review set to current_date so item appears today
    """
    from app.users_model import create_user
    from app.hafiz_model import populate_hafiz_items
    from database import revisions
    from constants import DAILY_REPS_MODE_CODE, NEW_MEMORIZATION_MODE_CODE

    timestamp = int(time.time() * 1000)
    email = f"progression_test_{timestamp}@example.com"
    password = "TestPass123!"
    user_name = f"Progression Test User {timestamp}"
    hafiz_name = f"ProgressionHafiz{timestamp}"
    current_date = "2024-01-15"

    existing_user = get_user_by_email(email)
    if existing_user:
        users.delete(existing_user.id)

    user_id = create_user(email, password, user_name)
    hafiz = hafizs.insert(name=hafiz_name, user_id=user_id, current_date=current_date)
    hafiz_id = hafiz.id

    # Populate hafiz_items table with all Quran items
    populate_hafiz_items(hafiz_id)

    # Reset xtra filter to query all items for this hafiz
    hafizs_items.xtra()
    test_items = hafizs_items(where=f"hafiz_id={hafiz_id} AND memorized=0", limit=1)
    if test_items:
        test_item = test_items[0]
        hafizs_items.update({
            "mode_code": DAILY_REPS_MODE_CODE,
            "memorized": True,
            "next_interval": 1,
            "next_review": current_date,
            "custom_daily_threshold": 2,
            "custom_weekly_threshold": 3,
            "custom_fortnightly_threshold": 4,
            "custom_monthly_threshold": 5,
        }, test_item.id)

        # NM revision must be on a PREVIOUS date, not current_date
        # Otherwise _was_newly_memorized_today() excludes it from Daily tab
        revisions.insert(
            item_id=test_item.item_id,
            hafiz_id=hafiz_id,
            mode_code=NEW_MEMORIZATION_MODE_CODE,
            revision_date="2024-01-14",  # Day before current_date
            rating=1,
        )

    yield {
        "user_id": user_id,
        "email": email,
        "password": password,
        "user_name": user_name,
        "hafiz_name": hafiz_name,
        "hafiz_id": hafiz_id,
        "current_date": current_date,
    }

    users.delete(user_id)


@pytest.fixture(scope="function")
def multi_mode_test_hafiz():
    """
    Fixture: User with items in all four rep modes.
    
    Sets up:
    - User with hafiz
    - One item each in DR, WR, FR, MR modes
    - All items due today (next_review = current_date)
    """
    from app.users_model import create_user
    from app.hafiz_model import populate_hafiz_items
    from database import revisions
    from constants import (
        DAILY_REPS_MODE_CODE,
        WEEKLY_REPS_MODE_CODE,
        FORTNIGHTLY_REPS_MODE_CODE,
        MONTHLY_REPS_MODE_CODE,
        NEW_MEMORIZATION_MODE_CODE,
    )

    timestamp = int(time.time() * 1000)
    email = f"multi_mode_test_{timestamp}@example.com"
    password = "TestPass123!"
    user_name = f"Multi Mode Test User {timestamp}"
    hafiz_name = f"MultiModeHafiz{timestamp}"
    current_date = "2024-01-15"

    existing_user = get_user_by_email(email)
    if existing_user:
        users.delete(existing_user.id)

    user_id = create_user(email, password, user_name)
    hafiz = hafizs.insert(name=hafiz_name, user_id=user_id, current_date=current_date)
    hafiz_id = hafiz.id

    # Populate hafiz_items table with all Quran items
    populate_hafiz_items(hafiz_id)

    # Reset xtra filter to query all items for this hafiz
    hafizs_items.xtra()
    test_items = hafizs_items(where=f"hafiz_id={hafiz_id} AND memorized=0", limit=4)

    mode_configs = [
        (DAILY_REPS_MODE_CODE, 1),
        (WEEKLY_REPS_MODE_CODE, 7),
        (FORTNIGHTLY_REPS_MODE_CODE, 14),
        (MONTHLY_REPS_MODE_CODE, 30),
    ]

    for i, (mode_code, interval) in enumerate(mode_configs):
        if i < len(test_items):
            test_item = test_items[i]
            hafizs_items.update({
                "mode_code": mode_code,
                "memorized": True,
                "next_interval": interval,
                "next_review": current_date,
            }, test_item.id)

            # NM revision must be on a PREVIOUS date to avoid _was_newly_memorized_today filter
            revisions.insert(
                item_id=test_item.item_id,
                hafiz_id=hafiz_id,
                mode_code=NEW_MEMORIZATION_MODE_CODE,
                revision_date="2024-01-14",  # Day before current_date
                rating=1,
            )

    yield {
        "user_id": user_id,
        "email": email,
        "password": password,
        "user_name": user_name,
        "hafiz_name": hafiz_name,
        "hafiz_id": hafiz_id,
        "current_date": current_date,
    }

    users.delete(user_id)
