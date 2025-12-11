"""
Journey 1a: New User First Cycle

E2E test verifying complete user onboarding and first Full Cycle workflow.
"""

import pytest
from playwright.sync_api import Page, expect
from app.users_model import get_user_by_email
from database import users


# ============================================================================
# Journey Test - Most important (what this file tests)
# ============================================================================


def test_new_user_onboarding_journey(page: Page, test_user_data: dict):
    """
    Complete user journey: New user signs up → Logs in → Redirects to hafiz selection

    NOTE: Currently testing signup + login only (user module).
    Hafiz creation and full cycle steps to be added.
    """
    signup_new_user(
        page,
        test_user_data["user_name"],
        test_user_data["email"],
        test_user_data["password"],
    )
    login_user(page, test_user_data["email"], test_user_data["password"])
    expect(page).to_have_url("/hafiz/selection")

    # TODO: Add remaining journey steps (hafiz creation → mark pages → first cycle → plan completion)


# ============================================================================
# Helper Functions - Implementation details
# ============================================================================


def signup_new_user(page: Page, name: str, email: str, password: str):
    """User creates a new account via signup form."""
    page.goto("/users/signup")
    page.get_by_label("Name").fill(name)
    page.get_by_label("Email").fill(email)
    # Note: Using exact=True because there are two password fields (Password + Confirm Password)
    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_label("Confirm Password").fill(password)
    page.get_by_role("button", name="Signup").click()


def login_user(page: Page, email: str, password: str):
    """User logs in with email and password."""
    page.goto("/users/login")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Login").click()


# ============================================================================
# Fixtures - Test setup/configuration
# ============================================================================


@pytest.fixture(scope="module")
def test_user_data():
    """Prepare test user credentials and cleanup previous runs."""
    data = {
        "email": "journey_1a_test@example.com",
        "password": "TestPass123!",
        "user_name": "Journey 1A Test User",
        "hafiz_name": "Journey 1A Hafiz",
    }

    existing_user = get_user_by_email(data["email"])
    if existing_user:
        users.delete(existing_user.id)

    return data
