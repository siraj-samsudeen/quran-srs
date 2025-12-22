"""Unit tests for mode predicate factory and helper functions.

Tests the pure predicate logic. Full integration tests with database
are in tests/integration/test_mode_filtering.py.
"""

import pytest
from constants import (
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    SRS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
)
from app.common_function import (
    _is_review_due,
    _is_reviewed_today,
    _has_memorized,
    _create_standard_rep_mode_predicate,
)


class TestIsReviewDue:
    """Test the _is_review_due helper predicate."""

    def test_due_today(self):
        item = {"next_review": "2024-01-15"}
        assert _is_review_due(item, "2024-01-15") is True

    def test_overdue(self):
        item = {"next_review": "2024-01-10"}
        assert _is_review_due(item, "2024-01-15") is True

    def test_not_due_yet(self):
        item = {"next_review": "2024-01-20"}
        assert _is_review_due(item, "2024-01-15") is False

    def test_empty_next_review(self):
        # Empty string returns True because day_diff returns 0 for empty/None, and 0 >= 0
        item = {"next_review": ""}
        assert _is_review_due(item, "2024-01-15") is True

    def test_none_next_review(self):
        # None returns True because day_diff returns 0 for empty/None, and 0 >= 0
        item = {"next_review": None}
        assert _is_review_due(item, "2024-01-15") is True


class TestIsReviewedToday:
    """Test the _is_reviewed_today helper predicate."""

    def test_reviewed_today(self):
        item = {"last_review": "2024-01-15"}
        assert _is_reviewed_today(item, "2024-01-15") is True

    def test_reviewed_yesterday(self):
        item = {"last_review": "2024-01-14"}
        assert _is_reviewed_today(item, "2024-01-15") is False

    def test_empty_last_review(self):
        item = {"last_review": ""}
        assert _is_reviewed_today(item, "2024-01-15") is False

    def test_none_last_review(self):
        item = {"last_review": None}
        assert _is_reviewed_today(item, "2024-01-15") is False


class TestHasMemorized:
    """Test the _has_memorized helper predicate."""

    def test_memorized_true(self):
        item = {"memorized": True}
        assert _has_memorized(item) is True

    def test_memorized_false(self):
        item = {"memorized": False}
        assert _has_memorized(item) is False

    def test_memorized_one(self):
        # SQLite stores booleans as integers, returns truthy 1
        item = {"memorized": 1}
        assert _has_memorized(item)

    def test_memorized_zero(self):
        # SQLite stores booleans as integers, returns falsy 0
        item = {"memorized": 0}
        assert not _has_memorized(item)


class TestCreateStandardRepModePredicate:
    """Test the factory function for standard rep mode predicates.

    These tests only verify the mode filtering aspect.
    Full tests with _has_revisions_in_mode require database integration.
    """

    def test_rejects_item_in_wrong_mode(self):
        predicate = _create_standard_rep_mode_predicate(WEEKLY_REPS_MODE_CODE)
        item = {
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-14",
        }
        assert predicate(item, "2024-01-15") is False

    def test_accepts_due_item_in_correct_mode(self):
        predicate = _create_standard_rep_mode_predicate(WEEKLY_REPS_MODE_CODE)
        item = {
            "mode_code": WEEKLY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-08",
        }
        assert predicate(item, "2024-01-15") is True

    def test_accepts_overdue_item_in_correct_mode(self):
        predicate = _create_standard_rep_mode_predicate(FORTNIGHTLY_REPS_MODE_CODE)
        item = {
            "mode_code": FORTNIGHTLY_REPS_MODE_CODE,
            "next_review": "2024-01-10",
            "last_review": "2023-12-27",
        }
        assert predicate(item, "2024-01-15") is True

    def test_factory_creates_distinct_predicates(self):
        weekly_pred = _create_standard_rep_mode_predicate(WEEKLY_REPS_MODE_CODE)
        fortnightly_pred = _create_standard_rep_mode_predicate(FORTNIGHTLY_REPS_MODE_CODE)
        monthly_pred = _create_standard_rep_mode_predicate(MONTHLY_REPS_MODE_CODE)

        weekly_item = {"mode_code": WEEKLY_REPS_MODE_CODE, "next_review": "2024-01-15", "last_review": ""}
        fortnightly_item = {"mode_code": FORTNIGHTLY_REPS_MODE_CODE, "next_review": "2024-01-15", "last_review": ""}
        monthly_item = {"mode_code": MONTHLY_REPS_MODE_CODE, "next_review": "2024-01-15", "last_review": ""}

        # Each predicate only accepts its own mode
        assert weekly_pred(weekly_item, "2024-01-15") is True
        assert weekly_pred(fortnightly_item, "2024-01-15") is False
        assert weekly_pred(monthly_item, "2024-01-15") is False

        assert fortnightly_pred(weekly_item, "2024-01-15") is False
        assert fortnightly_pred(fortnightly_item, "2024-01-15") is True
        assert fortnightly_pred(monthly_item, "2024-01-15") is False

        assert monthly_pred(weekly_item, "2024-01-15") is False
        assert monthly_pred(fortnightly_item, "2024-01-15") is False
        assert monthly_pred(monthly_item, "2024-01-15") is True


class TestDailyPredicateEdgeCases:
    """Test edge cases for daily reps predicate.

    Daily Reps is unique: it excludes items that were newly memorized today.
    """

    def test_due_item_not_newly_memorized_included(self):
        """Item due today that wasn't just memorized should be included."""
        from app.common_function import should_include_in_daily_reps

        item = {
            "item_id": 999,  # Use high ID unlikely to have NM revision
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-14",
        }
        assert should_include_in_daily_reps(item, "2024-01-15") is True

    def test_empty_next_review_treated_as_due(self):
        """Item with empty next_review should be treated as due."""
        from app.common_function import should_include_in_daily_reps

        item = {
            "item_id": 999,
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_review": "",
            "last_review": "2024-01-14",
        }
        assert should_include_in_daily_reps(item, "2024-01-15") is True

    def test_none_next_review_treated_as_due(self):
        """Item with None next_review should be treated as due."""
        from app.common_function import should_include_in_daily_reps

        item = {
            "item_id": 999,
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_review": None,
            "last_review": "2024-01-14",
        }
        assert should_include_in_daily_reps(item, "2024-01-15") is True

    def test_not_due_item_excluded(self):
        """Item not yet due should be excluded (unless reviewed today)."""
        from app.common_function import should_include_in_daily_reps

        item = {
            "item_id": 999,
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_review": "2024-01-20",
            "last_review": "2024-01-14",
        }
        assert should_include_in_daily_reps(item, "2024-01-15") is False

    def test_reviewed_today_in_daily_mode_included(self):
        """Item reviewed today in Daily mode should be included."""
        from app.common_function import should_include_in_daily_reps

        item = {
            "item_id": 999,
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_review": "2024-01-20",  # Not due yet
            "last_review": "2024-01-15",  # But reviewed today
        }
        assert should_include_in_daily_reps(item, "2024-01-15") is True

    def test_reviewed_today_in_wrong_mode_excluded(self):
        """Item reviewed today but not in Daily mode should be excluded."""
        from app.common_function import should_include_in_daily_reps

        item = {
            "item_id": 999,
            "mode_code": WEEKLY_REPS_MODE_CODE,  # Wrong mode
            "next_review": "2024-01-20",
            "last_review": "2024-01-15",
        }
        # Not due and not in daily mode, so excluded
        assert should_include_in_daily_reps(item, "2024-01-15") is False


class TestModePredicatesMapping:
    """Test MODE_PREDICATES dictionary completeness and correctness."""

    def test_all_rep_modes_have_predicates(self):
        """All rep mode codes should have predicates in MODE_PREDICATES."""
        from app.common_function import MODE_PREDICATES

        expected_modes = [
            DAILY_REPS_MODE_CODE,
            WEEKLY_REPS_MODE_CODE,
            FORTNIGHTLY_REPS_MODE_CODE,
            MONTHLY_REPS_MODE_CODE,
            SRS_MODE_CODE,
            FULL_CYCLE_MODE_CODE,
        ]
        for mode in expected_modes:
            assert mode in MODE_PREDICATES, f"{mode} missing from MODE_PREDICATES"
            assert callable(MODE_PREDICATES[mode]), f"{mode} predicate is not callable"

    def test_predicates_accept_correct_arguments(self):
        """All predicates should accept (item, current_date) arguments."""
        from app.common_function import MODE_PREDICATES

        item = {
            "item_id": 1,
            "mode_code": FULL_CYCLE_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-14",
            "memorized": True,
        }
        current_date = "2024-01-15"

        for mode_code, predicate in MODE_PREDICATES.items():
            # Ensure predicate can be called without error
            result = predicate(item, current_date)
            assert isinstance(result, bool), f"{mode_code} predicate doesn't return bool"

    def test_factory_generated_predicates_match_named_predicates(self):
        """Factory-generated predicates should match the named exports."""
        from app.common_function import (
            MODE_PREDICATES,
            should_include_in_weekly_reps,
            should_include_in_fortnightly_reps,
            should_include_in_monthly_reps,
        )

        # The predicates in MODE_PREDICATES should be the same as the named exports
        assert MODE_PREDICATES[WEEKLY_REPS_MODE_CODE] is should_include_in_weekly_reps
        assert MODE_PREDICATES[FORTNIGHTLY_REPS_MODE_CODE] is should_include_in_fortnightly_reps
        assert MODE_PREDICATES[MONTHLY_REPS_MODE_CODE] is should_include_in_monthly_reps
