"""Shared test fixtures for all test types.

This module provides:
- Factory functions for creating test users and hafiz setups
- Reusable fixtures with cleanup for E2E and integration tests
"""

import os
import time
import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session")
def base_url():
    """Override pytest-playwright's base_url with our env var."""
    return os.getenv("BASE_URL", "http://localhost:5001")


# ============================================================================
# Factory Functions
# ============================================================================


def create_test_user(email: str, password: str, name: str) -> int:
    """Create a test user in the database, cleaning up existing user if needed.
    
    Returns the user_id of the created user.
    """
    from app.users_model import create_user, get_user_by_email
    from database import users

    existing_user = get_user_by_email(email)
    if existing_user:
        users.delete(existing_user.id)

    return create_user(email, password, name)


def create_hafiz_with_items(user_id: int, hafiz_name: str, current_date: str) -> int:
    """Create a hafiz with populated items for testing.
    
    Returns the hafiz_id of the created hafiz.
    """
    from database import hafizs
    from app.hafiz_model import populate_hafiz_items

    hafiz = hafizs.insert(name=hafiz_name, user_id=user_id, current_date=current_date)
    populate_hafiz_items(hafiz.id)
    return hafiz.id


# ============================================================================
# Shared Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def test_user_data():
    """Generate unique test user credentials with cleanup.
    
    Yields dict with: email, password, user_name, hafiz_name
    """
    from app.users_model import get_user_by_email
    from database import users

    timestamp = int(time.time() * 1000)
    data = {
        "email": f"test_user_{timestamp}@example.com",
        "password": "TestPass123!",
        "user_name": f"Test User {timestamp}",
        "hafiz_name": f"TestHafiz{timestamp}",
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
    """User with hafiz and one Daily mode item (threshold=2).
    
    Sets up:
    - User with hafiz
    - One item in Daily mode with custom_daily_threshold=2
    - next_review set to current_date so item appears today
    """
    from app.users_model import get_user_by_email
    from database import users, hafizs_items, revisions
    from constants import DAILY_REPS_MODE_CODE, NEW_MEMORIZATION_MODE_CODE

    timestamp = int(time.time() * 1000)
    email = f"progression_test_{timestamp}@example.com"
    password = "TestPass123!"
    user_name = f"Progression Test User {timestamp}"
    hafiz_name = f"ProgressionHafiz{timestamp}"
    current_date = "2024-01-15"

    user_id = create_test_user(email, password, user_name)
    hafiz_id = create_hafiz_with_items(user_id, hafiz_name, current_date)

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

        revisions.insert(
            item_id=test_item.item_id,
            hafiz_id=hafiz_id,
            mode_code=NEW_MEMORIZATION_MODE_CODE,
            revision_date="2024-01-14",
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

    existing_user = get_user_by_email(email)
    if existing_user:
        users.delete(existing_user.id)


@pytest.fixture(scope="function")
def multi_mode_test_hafiz():
    """User with items in all four rep modes.
    
    Sets up:
    - User with hafiz
    - One item each in DR, WR, FR, MR modes
    - All items due today (next_review = current_date)
    """
    from app.users_model import get_user_by_email
    from database import users, hafizs_items, revisions
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

    user_id = create_test_user(email, password, user_name)
    hafiz_id = create_hafiz_with_items(user_id, hafiz_name, current_date)

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

            revisions.insert(
                item_id=test_item.item_id,
                hafiz_id=hafiz_id,
                mode_code=NEW_MEMORIZATION_MODE_CODE,
                revision_date="2024-01-14",
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

    existing_user = get_user_by_email(email)
    if existing_user:
        users.delete(existing_user.id)
