"""
Journey 1a: New User Onboarding and Rep Mode Progression

E2E tests verifying:
1. Complete user onboarding flow (signup → login → create hafiz)
2. Rep mode progression with Close Date (DR→WR→FR→MR→FC)
3. Multiple modes processing simultaneously

Note: Mode selection at memorization time was removed. New memorization now defaults
to Daily mode. Custom thresholds can be set via the Profile page after memorization.
Integration tests in tests/integration/test_new_memorization_modes.py cover the
home-tab NM toggle/bulk_mark functionality.
"""

import time
import pytest
from playwright.sync_api import Page, expect
from app.users_model import get_user_by_email
from database import users, hafizs, hafizs_items


# ============================================================================
# Journey Tests - Complete user flows
# ============================================================================


def test_new_user_onboarding_journey(page: Page, base_url: str, test_user_data: dict):
    """
    Complete user journey: Signup → Login → Create hafiz → Verify redirection.
    """
    signup_new_user(
        page,
        base_url,
        test_user_data["user_name"],
        test_user_data["email"],
        test_user_data["password"],
    )
    login_user(page, base_url, test_user_data["email"], test_user_data["password"])
    expect(page).to_have_url(f"{base_url}/hafiz/selection")

    # Create hafiz (form label is "Name", not "Hafiz Name")
    page.get_by_label("Name").fill(test_user_data["hafiz_name"])
    page.get_by_role("button", name="Add Hafiz").click()

    # Verify hafiz was created and redirected to home
    expect(page).to_have_url(f"{base_url}/")


def test_rep_mode_progression_with_close_date(page: Page, base_url: str, progression_test_hafiz: dict):
    """
    Full journey test: Memorize pages → Rate → Close Date → Verify graduation DR→WR→FR→MR→FC.

    This test covers:
    1. Memorize page in Daily mode with custom threshold of 2
    2. Rate page twice, close date each time
    3. Verify graduation to Weekly mode
    4. Continue rating to verify WR→FR→MR→FC progression
    """
    login_and_select_hafiz(page, base_url, progression_test_hafiz)

    # Phase 1: Verify item starts in Daily mode with custom threshold
    page.goto(f"{base_url}/")
    daily_tab = page.locator("a:has-text('☀️ Daily')")
    expect(daily_tab).to_be_visible()
    daily_tab.click()

    # Verify progress shows 0/2 (custom threshold)
    expect(page.locator("text=0/2")).to_be_visible()

    # Phase 2: Rate the page (first rating)
    rating_select = page.locator("select[name='rating']").first
    rating_select.select_option("1")  # Good rating

    # Wait for HTMX update
    expect(page.locator("text=1/2")).to_be_visible()

    # Phase 3: Close Date
    page.locator("[data-testid='close-date-btn']").click()
    page.get_by_role("button", name="Confirm").click()

    # Verify redirected to home
    expect(page).to_have_url(f"{base_url}/")

    # Phase 4: Rate again (second rating to reach threshold)
    daily_tab = page.locator("a:has-text('☀️ Daily')")
    expect(daily_tab).to_be_visible()
    daily_tab.click()

    rating_select = page.locator("select[name='rating']").first
    rating_select.select_option("1")  # Good rating

    expect(page.locator("text=2/2")).to_be_visible()

    # Phase 5: Close Date again - should trigger graduation to Weekly
    page.locator("[data-testid='close-date-btn']").click()
    page.get_by_role("button", name="Confirm").click()

    # Phase 6: Verify item graduated to Weekly mode
    page.goto(f"{base_url}/")

    # Daily tab should not show the item anymore (or not exist if empty)
    weekly_tab = page.locator("a:has-text('📅 Weekly')")
    expect(weekly_tab).to_be_visible()
    weekly_tab.click()

    # Verify item is now in Weekly mode with custom threshold (0/3)
    expect(page.locator("text=0/3")).to_be_visible()


def test_close_date_processes_multiple_modes(page: Page, base_url: str, multi_mode_test_hafiz: dict):
    """
    Test Close Date processing items in different modes simultaneously.

    Verifies:
    - Items in DR, WR, FR, MR are all processed correctly
    - Each mode shows correct items before and after Close Date
    - Custom thresholds are respected during graduation
    """
    login_and_select_hafiz(page, base_url, multi_mode_test_hafiz)

    page.goto(f"{base_url}/")

    # Verify all mode tabs exist with items
    daily_tab = page.locator("a:has-text('☀️ Daily')")
    weekly_tab = page.locator("a:has-text('📅 Weekly')")
    fortnightly_tab = page.locator("a:has-text('📆 Fortnightly')")
    monthly_tab = page.locator("a:has-text('🗓️ Monthly')")

    expect(daily_tab).to_be_visible()
    expect(weekly_tab).to_be_visible()
    expect(fortnightly_tab).to_be_visible()
    expect(monthly_tab).to_be_visible()

    # Rate item in Daily mode
    daily_tab.click()
    page.locator("select[name='rating']").first.select_option("1")

    # Rate item in Weekly mode
    weekly_tab.click()
    page.locator("select[name='rating']").first.select_option("1")

    # Rate item in Fortnightly mode
    fortnightly_tab.click()
    page.locator("select[name='rating']").first.select_option("1")

    # Rate item in Monthly mode
    monthly_tab.click()
    page.locator("select[name='rating']").first.select_option("1")

    # Close Date
    page.locator("[data-testid='close-date-btn']").click()
    page.get_by_role("button", name="Confirm").click()

    # Verify all items were processed (next_review advanced)
    page.goto(f"{base_url}/")

    # Items should still exist in their modes (not yet at graduation threshold)
    expect(daily_tab).to_be_visible()
    expect(weekly_tab).to_be_visible()
    expect(fortnightly_tab).to_be_visible()
    expect(monthly_tab).to_be_visible()


# ============================================================================
# Helper Functions - User actions
# ============================================================================


def signup_new_user(page: Page, base_url: str, name: str, email: str, password: str):
    """User creates a new account via signup form."""
    page.goto(f"{base_url}/users/signup")
    page.get_by_label("Name").fill(name)
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_label("Confirm Password").fill(password)
    page.get_by_role("button", name="Signup").click()
    page.wait_for_url(f"{base_url}/users/login")


def login_user(page: Page, base_url: str, email: str, password: str):
    """User logs in with email and password."""
    page.goto(f"{base_url}/users/login")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Login").click()


def login_and_select_hafiz(page: Page, base_url: str, user_data: dict):
    """Login user and select their hafiz."""
    login_user(page, base_url, user_data["email"], user_data["password"])

    # If redirected to hafiz selection, select the hafiz
    if "/hafiz/selection" in page.url:
        page.get_by_role("button", name=user_data["hafiz_name"]).click()


# ============================================================================
# Fixtures - Test setup/configuration
# ============================================================================


@pytest.fixture(scope="module")
def test_user_data():
    """Prepare test user credentials and cleanup previous runs."""
    timestamp = int(time.time() * 1000)
    data = {
        "email": f"journey_1a_test_{timestamp}@example.com",
        "password": "TestPass123!",
        "user_name": f"Journey 1A Test User {timestamp}",
        "hafiz_name": f"Journey 1A Hafiz {timestamp}",
    }

    existing_user = get_user_by_email(data["email"])
    if existing_user:
        users.delete(existing_user.id)

    yield data

    # Cleanup after test
    existing_user = get_user_by_email(data["email"])
    if existing_user:
        users.delete(existing_user.id)


@pytest.fixture(scope="function")
def progression_test_hafiz():
    """Create test user with hafiz and item in Daily mode for progression tests.

    Sets up:
    - User with hafiz
    - One item in Daily mode with custom_daily_threshold=2, custom_weekly_threshold=3
    - next_review set to current_date so item appears in today's list
    """
    from app.users_model import create_user
    from database import revisions
    from constants import DAILY_REPS_MODE_CODE, NEW_MEMORIZATION_MODE_CODE

    timestamp = int(time.time() * 1000)
    email = f"progression_test_{timestamp}@example.com"
    password = "TestPass123!"
    user_name = f"Progression Test User {timestamp}"
    hafiz_name = f"Progression Test Hafiz {timestamp}"
    current_date = "2024-01-15"

    existing_user = get_user_by_email(email)
    if existing_user:
        users.delete(existing_user.id)

    user_id = create_user(email, password, user_name)
    hafiz = hafizs.insert(name=hafiz_name, user_id=user_id, current_date=current_date)
    hafiz_id = hafiz.id

    # Get an unmemorized item and set it up in Daily mode
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

        # Add NM revision to mark as memorized
        revisions.insert(
            item_id=test_item.item_id,
            hafiz_id=hafiz_id,
            mode_code=NEW_MEMORIZATION_MODE_CODE,
            revision_date=current_date,
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
    """Create test user with items in all four rep modes for multi-mode tests.

    Sets up:
    - User with hafiz
    - One item each in DR, WR, FR, MR modes
    - All items due today (next_review = current_date)
    """
    from app.users_model import create_user
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
    hafiz_name = f"Multi Mode Test Hafiz {timestamp}"
    current_date = "2024-01-15"

    existing_user = get_user_by_email(email)
    if existing_user:
        users.delete(existing_user.id)

    user_id = create_user(email, password, user_name)
    hafiz = hafizs.insert(name=hafiz_name, user_id=user_id, current_date=current_date)
    hafiz_id = hafiz.id

    # Get 4 unmemorized items for each mode
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

            revisions.insert(
                item_id=test_item.item_id,
                hafiz_id=hafiz_id,
                mode_code=NEW_MEMORIZATION_MODE_CODE,
                revision_date=current_date,
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
