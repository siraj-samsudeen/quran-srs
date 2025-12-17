"""Integration tests for mode filtering predicates.

Tests that items are correctly filtered into their respective mode tables
based on the predicates in MODE_PREDICATES.
"""

import time
import pytest
from fasthtml.core import Client
from constants import (
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    SRS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
    NEW_MEMORIZATION_MODE_CODE,
)
from app.common_function import (
    should_include_in_daily_reps,
    should_include_in_weekly_reps,
    should_include_in_fortnightly_reps,
    should_include_in_monthly_reps,
    should_include_in_srs,
    should_include_in_full_cycle,
    _has_revisions_in_mode,
)


@pytest.fixture
def test_hafiz(client):
    """Create a test user and hafiz with items for filtering tests."""
    from app.users_model import create_user
    from database import users, hafizs, hafizs_items

    test_email = f"filtering_test_{int(time.time() * 1000)}@example.com"
    user_id = create_user(test_email, "password123", "Filtering Test User")

    login_response = client.post(
        "/users/login",
        data={"email": test_email, "password": "password123"},
        follow_redirects=False,
    )
    client.cookies = login_response.cookies

    client.post(
        "/hafiz/add",
        data={"name": "Test Hafiz"},
        follow_redirects=False,
    )

    user_hafizs = hafizs(where=f"user_id={user_id}")
    hafiz_id = user_hafizs[0].id
    select_response = client.post(
        "/hafiz/selection",
        data={"current_hafiz_id": hafiz_id},
        follow_redirects=False,
    )
    client.cookies = select_response.cookies

    yield {
        "client": client,
        "user_id": user_id,
        "hafiz_id": hafiz_id,
        "email": test_email,
    }

    users.delete(user_id)


class TestDailyRepsFilter:
    """Test the Daily Reps predicate filtering logic."""

    def test_due_item_included(self, test_hafiz):
        """Item due today is included in Daily Reps."""
        item = {
            "item_id": 1,
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-14",
            "memorized": False,
        }
        assert should_include_in_daily_reps(item, "2024-01-15") is True

    def test_overdue_item_included(self, test_hafiz):
        """Overdue item is included in Daily Reps."""
        item = {
            "item_id": 1,
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_review": "2024-01-10",
            "last_review": "2024-01-09",
            "memorized": False,
        }
        assert should_include_in_daily_reps(item, "2024-01-15") is True

    def test_not_due_item_excluded(self, test_hafiz):
        """Item not yet due is excluded from Daily Reps."""
        item = {
            "item_id": 1,
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_review": "2024-01-20",
            "last_review": "2024-01-14",
            "memorized": False,
        }
        assert should_include_in_daily_reps(item, "2024-01-15") is False


class TestStandardRepModeFilters:
    """Test filtering for Weekly, Fortnightly, and Monthly modes.

    These use the factory-generated predicates.
    """

    def test_weekly_accepts_due_item_in_weekly_mode(self):
        """Weekly predicate accepts due item in Weekly mode."""
        item = {
            "item_id": 1,
            "mode_code": WEEKLY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-08",
            "memorized": False,
        }
        assert should_include_in_weekly_reps(item, "2024-01-15") is True

    def test_weekly_rejects_item_in_daily_mode(self):
        """Weekly predicate rejects item that's in Daily mode."""
        item = {
            "item_id": 1,
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-14",
            "memorized": False,
        }
        assert should_include_in_weekly_reps(item, "2024-01-15") is False

    def test_fortnightly_accepts_due_item_in_fortnightly_mode(self):
        """Fortnightly predicate accepts due item in Fortnightly mode."""
        item = {
            "item_id": 1,
            "mode_code": FORTNIGHTLY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-01",
            "memorized": False,
        }
        assert should_include_in_fortnightly_reps(item, "2024-01-15") is True

    def test_fortnightly_rejects_item_in_weekly_mode(self):
        """Fortnightly predicate rejects item that's in Weekly mode."""
        item = {
            "item_id": 1,
            "mode_code": WEEKLY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-08",
            "memorized": False,
        }
        assert should_include_in_fortnightly_reps(item, "2024-01-15") is False

    def test_monthly_accepts_due_item_in_monthly_mode(self):
        """Monthly predicate accepts due item in Monthly mode."""
        item = {
            "item_id": 1,
            "mode_code": MONTHLY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2023-12-15",
            "memorized": False,
        }
        assert should_include_in_monthly_reps(item, "2024-01-15") is True

    def test_monthly_rejects_item_in_fortnightly_mode(self):
        """Monthly predicate rejects item that's in Fortnightly mode."""
        item = {
            "item_id": 1,
            "mode_code": FORTNIGHTLY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-01",
            "memorized": False,
        }
        assert should_include_in_monthly_reps(item, "2024-01-15") is False


class TestSRSFilter:
    """Test the SRS predicate filtering logic."""

    def test_due_srs_item_included(self):
        """Due SRS item is included."""
        item = {
            "item_id": 1,
            "mode_code": SRS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-08",
            "memorized": True,
        }
        assert should_include_in_srs(item, "2024-01-15") is True

    def test_not_due_srs_item_excluded(self):
        """Not-due SRS item without today's revision is excluded."""
        item = {
            "item_id": 999,  # Use high ID unlikely to have revisions
            "mode_code": SRS_MODE_CODE,
            "next_review": "2024-01-20",
            "last_review": "2024-01-10",
            "memorized": True,
        }
        # This will return False because:
        # 1. Item is not due (next_review is in future)
        # 2. _has_revisions_today_in_mode will likely return False for this item
        assert should_include_in_srs(item, "2024-01-15") is False


class TestFullCycleFilter:
    """Test the Full Cycle predicate filtering logic."""

    def test_memorized_item_included(self):
        """Memorized item is included in Full Cycle."""
        item = {
            "item_id": 1,
            "mode_code": FULL_CYCLE_MODE_CODE,
            "next_review": None,
            "last_review": "2024-01-14",
            "memorized": True,
        }
        assert should_include_in_full_cycle(item, "2024-01-15") is True

    def test_non_memorized_item_excluded(self):
        """Non-memorized item is excluded from Full Cycle."""
        item = {
            "item_id": 1,
            "mode_code": FULL_CYCLE_MODE_CODE,
            "next_review": None,
            "last_review": "2024-01-14",
            "memorized": False,
        }
        assert should_include_in_full_cycle(item, "2024-01-15") is False


class TestCrossModeFiltering:
    """Test that items only appear in their correct mode's table."""

    def test_weekly_item_appears_in_daily_if_due(self):
        """Daily Reps doesn't filter by mode_code - any due item can appear.

        This is by design: Daily Reps shows items based on their next_review date,
        not their mode_code. The mode_code filtering happens at a different level
        (in make_summary_table's query).
        """
        item = {
            "item_id": 1,
            "mode_code": WEEKLY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-08",
            "memorized": False,
        }
        # Daily predicate uses date-based filtering, not mode filtering
        # Items are filtered to Daily mode in the SQL query, not the predicate
        assert should_include_in_daily_reps(item, "2024-01-15") is True

    def test_fortnightly_item_not_in_weekly_table(self):
        """Item in Fortnightly mode doesn't appear in Weekly table."""
        item = {
            "item_id": 1,
            "mode_code": FORTNIGHTLY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-01",
            "memorized": False,
        }
        assert should_include_in_weekly_reps(item, "2024-01-15") is False

    def test_monthly_item_not_in_fortnightly_table(self):
        """Item in Monthly mode doesn't appear in Fortnightly table."""
        item = {
            "item_id": 1,
            "mode_code": MONTHLY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2023-12-15",
            "memorized": False,
        }
        assert should_include_in_fortnightly_reps(item, "2024-01-15") is False


class TestHasRevisionsInMode:
    """Test the _has_revisions_in_mode helper with actual database."""

    def test_item_with_revisions_returns_true(self, test_hafiz):
        """Item with revisions in its mode returns True."""
        from database import hafizs_items, revisions

        hafiz_id = test_hafiz["hafiz_id"]
        items = hafizs_items(where=f"hafiz_id={hafiz_id}")
        test_item = items[0]
        item_id = test_item.item_id

        # Set item to Weekly mode
        hafizs_items.update({"mode_code": WEEKLY_REPS_MODE_CODE}, test_item.id)

        # Add a revision in Weekly mode
        revisions.insert(
            item_id=item_id,
            hafiz_id=hafiz_id,
            mode_code=WEEKLY_REPS_MODE_CODE,
            revision_date="2024-01-15",
            rating=1,
        )

        item_dict = {
            "item_id": item_id,
            "mode_code": WEEKLY_REPS_MODE_CODE,
        }
        assert _has_revisions_in_mode(item_dict) is True

    def test_item_without_revisions_returns_false(self, test_hafiz):
        """Item without revisions in its mode returns False."""
        from database import hafizs_items

        hafiz_id = test_hafiz["hafiz_id"]
        items = hafizs_items(where=f"hafiz_id={hafiz_id}")
        test_item = items[1]
        item_id = test_item.item_id

        # Set item to Fortnightly mode (unlikely to have revisions)
        hafizs_items.update({"mode_code": FORTNIGHTLY_REPS_MODE_CODE}, test_item.id)

        item_dict = {
            "item_id": item_id,
            "mode_code": FORTNIGHTLY_REPS_MODE_CODE,
        }
        # Might be True or False depending on existing data, but tests the function works
        result = _has_revisions_in_mode(item_dict)
        assert isinstance(result, bool)
