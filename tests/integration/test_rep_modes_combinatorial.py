"""Combinatorial tests for rep mode behavior.

Uses pytest parametrize to test all combinations of mode, review status,
and graduation status to ensure consistent behavior across all rep modes.
"""

import pytest
from constants import (
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
)
from app.fixed_reps import REP_MODES_CONFIG
from app.common_function import (
    should_include_in_daily_reps,
    should_include_in_weekly_reps,
    should_include_in_fortnightly_reps,
    should_include_in_monthly_reps,
    MODE_PREDICATES,
)


# All rep modes (excluding SRS and Full Cycle which have different logic)
REP_MODE_CODES = [
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
]

# Standard rep modes (use factory-generated predicates)
STANDARD_REP_MODE_CODES = [
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
]


class TestRepModeConfigConsistency:
    """Test that REP_MODES_CONFIG is consistent and complete."""

    @pytest.mark.parametrize("mode_code", REP_MODE_CODES)
    def test_config_has_required_keys(self, mode_code):
        """Each mode config has interval, threshold, and next_mode_code."""
        config = REP_MODES_CONFIG[mode_code]
        assert "interval" in config
        assert "threshold" in config
        assert "next_mode_code" in config

    @pytest.mark.parametrize("mode_code", REP_MODE_CODES)
    def test_threshold_is_seven(self, mode_code):
        """All rep modes use threshold of 7."""
        config = REP_MODES_CONFIG[mode_code]
        assert config["threshold"] == 7

    def test_graduation_chain_is_complete(self):
        """Verify the graduation chain is: DR → WR → FR → MR → FC."""
        assert REP_MODES_CONFIG[DAILY_REPS_MODE_CODE]["next_mode_code"] == WEEKLY_REPS_MODE_CODE
        assert REP_MODES_CONFIG[WEEKLY_REPS_MODE_CODE]["next_mode_code"] == FORTNIGHTLY_REPS_MODE_CODE
        assert REP_MODES_CONFIG[FORTNIGHTLY_REPS_MODE_CODE]["next_mode_code"] == MONTHLY_REPS_MODE_CODE
        assert REP_MODES_CONFIG[MONTHLY_REPS_MODE_CODE]["next_mode_code"] == FULL_CYCLE_MODE_CODE

    def test_intervals_increase_progressively(self):
        """Intervals increase: 1 → 7 → 14 → 30."""
        assert REP_MODES_CONFIG[DAILY_REPS_MODE_CODE]["interval"] == 1
        assert REP_MODES_CONFIG[WEEKLY_REPS_MODE_CODE]["interval"] == 7
        assert REP_MODES_CONFIG[FORTNIGHTLY_REPS_MODE_CODE]["interval"] == 14
        assert REP_MODES_CONFIG[MONTHLY_REPS_MODE_CODE]["interval"] == 30


class TestModePredicatesConsistency:
    """Test that MODE_PREDICATES has all required modes."""

    @pytest.mark.parametrize("mode_code", REP_MODE_CODES)
    def test_predicate_exists_for_each_rep_mode(self, mode_code):
        """Each rep mode has a predicate in MODE_PREDICATES."""
        assert mode_code in MODE_PREDICATES
        assert callable(MODE_PREDICATES[mode_code])


class TestStandardRepModePredicateBehavior:
    """Test that standard rep modes (WR/FR/MR) have identical filtering behavior."""

    @pytest.mark.parametrize("mode_code", STANDARD_REP_MODE_CODES)
    def test_rejects_item_in_wrong_mode(self, mode_code):
        """Standard rep mode predicates reject items in wrong mode."""
        predicate = MODE_PREDICATES[mode_code]
        # Create item in different mode
        wrong_mode = DAILY_REPS_MODE_CODE if mode_code != DAILY_REPS_MODE_CODE else WEEKLY_REPS_MODE_CODE
        item = {
            "item_id": 1,
            "mode_code": wrong_mode,
            "next_review": "2024-01-15",
            "last_review": "2024-01-14",
        }
        assert predicate(item, "2024-01-15") is False

    @pytest.mark.parametrize("mode_code", STANDARD_REP_MODE_CODES)
    def test_accepts_due_item_in_correct_mode(self, mode_code):
        """Standard rep mode predicates accept due items in correct mode."""
        predicate = MODE_PREDICATES[mode_code]
        item = {
            "item_id": 1,
            "mode_code": mode_code,
            "next_review": "2024-01-15",
            "last_review": "2024-01-08",
        }
        assert predicate(item, "2024-01-15") is True

    @pytest.mark.parametrize("mode_code", STANDARD_REP_MODE_CODES)
    def test_accepts_overdue_item_in_correct_mode(self, mode_code):
        """Standard rep mode predicates accept overdue items in correct mode."""
        predicate = MODE_PREDICATES[mode_code]
        item = {
            "item_id": 1,
            "mode_code": mode_code,
            "next_review": "2024-01-10",
            "last_review": "2024-01-03",
        }
        assert predicate(item, "2024-01-15") is True

    @pytest.mark.parametrize("mode_code", STANDARD_REP_MODE_CODES)
    def test_rejects_not_due_item_without_today_review(self, mode_code):
        """Standard rep mode predicates reject not-due items without today's review."""
        predicate = MODE_PREDICATES[mode_code]
        item = {
            "item_id": 1,
            "mode_code": mode_code,
            "next_review": "2024-01-20",
            "last_review": "2024-01-10",
        }
        assert predicate(item, "2024-01-15") is False


class TestDueDateScenarios:
    """Test various due date scenarios across all rep modes."""

    @pytest.mark.parametrize("mode_code", STANDARD_REP_MODE_CODES)
    @pytest.mark.parametrize(
        "next_review,expected",
        [
            ("2024-01-15", True),   # Due today
            ("2024-01-10", True),   # Overdue by 5 days
            ("2024-01-01", True),   # Overdue by 14 days
            ("2024-01-16", False),  # Due tomorrow
            ("2024-01-20", False),  # Due in 5 days
            ("2024-02-15", False),  # Due in 1 month
        ],
    )
    def test_due_date_filtering(self, mode_code, next_review, expected):
        """Test due date filtering for all standard rep modes."""
        predicate = MODE_PREDICATES[mode_code]
        item = {
            "item_id": 1,
            "mode_code": mode_code,
            "next_review": next_review,
            "last_review": "2024-01-01",
        }
        assert predicate(item, "2024-01-15") is expected


class TestMutualExclusivity:
    """Test that items can only belong to one rep mode at a time."""

    def test_item_in_weekly_not_accepted_by_other_standard_modes(self):
        """Item in Weekly mode is rejected by Fortnightly and Monthly predicates."""
        item = {
            "item_id": 1,
            "mode_code": WEEKLY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-08",
        }
        assert should_include_in_weekly_reps(item, "2024-01-15") is True
        assert should_include_in_fortnightly_reps(item, "2024-01-15") is False
        assert should_include_in_monthly_reps(item, "2024-01-15") is False

    def test_item_in_fortnightly_not_accepted_by_other_standard_modes(self):
        """Item in Fortnightly mode is rejected by Weekly and Monthly predicates."""
        item = {
            "item_id": 1,
            "mode_code": FORTNIGHTLY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2024-01-01",
        }
        assert should_include_in_weekly_reps(item, "2024-01-15") is False
        assert should_include_in_fortnightly_reps(item, "2024-01-15") is True
        assert should_include_in_monthly_reps(item, "2024-01-15") is False

    def test_item_in_monthly_not_accepted_by_other_standard_modes(self):
        """Item in Monthly mode is rejected by Weekly and Fortnightly predicates."""
        item = {
            "item_id": 1,
            "mode_code": MONTHLY_REPS_MODE_CODE,
            "next_review": "2024-01-15",
            "last_review": "2023-12-15",
        }
        assert should_include_in_weekly_reps(item, "2024-01-15") is False
        assert should_include_in_fortnightly_reps(item, "2024-01-15") is False
        assert should_include_in_monthly_reps(item, "2024-01-15") is True


class TestEdgeCases:
    """Test edge cases in predicate behavior."""

    @pytest.mark.parametrize("mode_code", STANDARD_REP_MODE_CODES)
    def test_empty_next_review_treated_as_due(self, mode_code):
        """Item with empty next_review is treated as due (day_diff returns 0)."""
        predicate = MODE_PREDICATES[mode_code]
        item = {
            "item_id": 1,
            "mode_code": mode_code,
            "next_review": "",
            "last_review": "2024-01-14",
        }
        # Empty next_review -> day_diff returns 0 -> 0 >= 0 -> True (due)
        assert predicate(item, "2024-01-15") is True

    @pytest.mark.parametrize("mode_code", STANDARD_REP_MODE_CODES)
    def test_none_next_review_treated_as_due(self, mode_code):
        """Item with None next_review is treated as due (day_diff returns 0)."""
        predicate = MODE_PREDICATES[mode_code]
        item = {
            "item_id": 1,
            "mode_code": mode_code,
            "next_review": None,
            "last_review": "2024-01-14",
        }
        # None next_review -> day_diff returns 0 -> 0 >= 0 -> True (due)
        assert predicate(item, "2024-01-15") is True
