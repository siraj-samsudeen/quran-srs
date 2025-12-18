"""Integration tests for graduation helper functions and constants.

Tests GRADUATABLE_MODES constant and helper functions used in mode management.
"""

from constants import (
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
    NEW_MEMORIZATION_MODE_CODE,
    SRS_MODE_CODE,
    GRADUATABLE_MODES,
)
from app.fixed_reps import REP_MODES_CONFIG
from app.common_function import get_mode_icon, can_graduate


class TestGraduatableModes:
    """Test GRADUATABLE_MODES constant configuration."""

    def test_graduatable_modes_includes_rep_modes(self):
        """GRADUATABLE_MODES includes all rep modes."""
        assert DAILY_REPS_MODE_CODE in GRADUATABLE_MODES
        assert WEEKLY_REPS_MODE_CODE in GRADUATABLE_MODES
        assert FORTNIGHTLY_REPS_MODE_CODE in GRADUATABLE_MODES
        assert MONTHLY_REPS_MODE_CODE in GRADUATABLE_MODES

    def test_graduatable_modes_excludes_non_rep_modes(self):
        """GRADUATABLE_MODES excludes FC, NM, SR modes."""
        assert FULL_CYCLE_MODE_CODE not in GRADUATABLE_MODES
        assert NEW_MEMORIZATION_MODE_CODE not in GRADUATABLE_MODES
        assert SRS_MODE_CODE not in GRADUATABLE_MODES

    def test_graduatable_modes_matches_rep_modes_config(self):
        """All modes in GRADUATABLE_MODES have REP_MODES_CONFIG entries."""
        for mode_code in GRADUATABLE_MODES:
            assert mode_code in REP_MODES_CONFIG


class TestHelperFunctions:
    """Test helper functions for mode management."""

    def test_get_mode_icon_returns_icons(self):
        """get_mode_icon returns emoji icons for all modes."""
        assert get_mode_icon(DAILY_REPS_MODE_CODE) == "☀️"
        assert get_mode_icon(WEEKLY_REPS_MODE_CODE) == "📅"
        assert get_mode_icon(FORTNIGHTLY_REPS_MODE_CODE) == "📆"
        assert get_mode_icon(MONTHLY_REPS_MODE_CODE) == "🗓️"
        assert get_mode_icon(FULL_CYCLE_MODE_CODE) == "🔄"
        assert get_mode_icon(SRS_MODE_CODE) == "🧠"
        assert get_mode_icon(NEW_MEMORIZATION_MODE_CODE) == "🆕"

    def test_get_mode_icon_unknown_mode(self):
        """get_mode_icon returns default icon for unknown modes."""
        assert get_mode_icon("UNKNOWN") == "📖"

    def test_can_graduate_rep_modes(self):
        """can_graduate returns True for rep modes."""
        assert can_graduate(DAILY_REPS_MODE_CODE) is True
        assert can_graduate(WEEKLY_REPS_MODE_CODE) is True
        assert can_graduate(FORTNIGHTLY_REPS_MODE_CODE) is True
        assert can_graduate(MONTHLY_REPS_MODE_CODE) is True

    def test_can_graduate_non_rep_modes(self):
        """can_graduate returns False for non-rep modes."""
        assert can_graduate(FULL_CYCLE_MODE_CODE) is False
        assert can_graduate(NEW_MEMORIZATION_MODE_CODE) is False
        assert can_graduate(SRS_MODE_CODE) is False
