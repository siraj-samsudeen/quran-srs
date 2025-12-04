"""
Unit Tests for SRS Interval Calculation

MECE Test Framework:
- Category C: On-time reviews by phase and rating
- Category D: Late reviews
- Category E: Early reviews
- Category G: Graduation
- Category H: Constraints (min interval, caps, floors)

Each test follows the pattern:
1. Given: Setup input values
2. When: Call the function
3. Then: Assert expected output
"""

import pytest
from app.srs_interval_calc import (
    get_phase_config,
    get_base_interval,
    calculate_good_interval,
    calculate_ok_interval,
    calculate_bad_interval,
    calculate_next_interval,
    should_graduate,
    should_reschedule_only,
    SRS_PHASE_CONFIG,
    SRS_MIN_INTERVAL,
    SRS_OK_CAP,
    SRS_BAD_FLOOR,
    SRS_GRADUATION_STREAK,
)


# =============================================================================
# Category: Phase Configuration
# =============================================================================

class TestGetPhaseConfig:
    """Test phase configuration lookup."""

    def test_phase1_interval_0(self):
        """Interval 0 is in phase 1 (0-14)."""
        config = get_phase_config(0)
        assert config["good_multiplier"] == 2.0
        assert config["ok_increment"] == 2

    def test_phase1_interval_7(self):
        """Interval 7 is in phase 1 (0-14)."""
        config = get_phase_config(7)
        assert config["good_multiplier"] == 2.0
        assert config["ok_increment"] == 2

    def test_phase1_interval_13(self):
        """Interval 13 is in phase 1 (0-14)."""
        config = get_phase_config(13)
        assert config["good_multiplier"] == 2.0

    def test_phase2_interval_14(self):
        """Interval 14 is in phase 2 (14-30)."""
        config = get_phase_config(14)
        assert config["good_multiplier"] == 1.5
        assert config["ok_increment"] == 1

    def test_phase2_interval_20(self):
        """Interval 20 is in phase 2 (14-30)."""
        config = get_phase_config(20)
        assert config["good_multiplier"] == 1.5

    def test_phase2_interval_29(self):
        """Interval 29 is in phase 2 (14-30)."""
        config = get_phase_config(29)
        assert config["good_multiplier"] == 1.5

    def test_phase3_interval_30(self):
        """Interval 30 is in phase 3 (30-40)."""
        config = get_phase_config(30)
        assert config["good_multiplier"] == 1.0
        assert config["ok_increment"] == 0

    def test_phase3_interval_35(self):
        """Interval 35 is in phase 3 (30-40)."""
        config = get_phase_config(35)
        assert config["good_multiplier"] == 1.0

    def test_phase3_interval_39(self):
        """Interval 39 is in phase 3 (30-40)."""
        config = get_phase_config(39)
        assert config["good_multiplier"] == 1.0

    def test_phase4_interval_40(self):
        """Interval 40 is in phase 4 (40+)."""
        config = get_phase_config(40)
        assert config["good_increment"] == 3
        assert config["ok_increment"] == 0

    def test_phase4_interval_100(self):
        """Interval 100 is in phase 4 (40+)."""
        config = get_phase_config(100)
        assert config["good_increment"] == 3


# =============================================================================
# Category C: On-Time Reviews - Good Rating by Phase
# =============================================================================

class TestCalculateGoodInterval:
    """Test Good rating interval calculation by phase."""

    # Phase 1: interval + (streak × 2)
    def test_phase1_good_streak1(self):
        """Phase 1, Good, streak=1: 7 + (1 × 2) = 9."""
        result = calculate_good_interval(base=7, good_streak=1)
        assert result == 9

    def test_phase1_good_streak2(self):
        """Phase 1, Good, streak=2: 7 + (2 × 2) = 11."""
        result = calculate_good_interval(base=7, good_streak=2)
        assert result == 11

    def test_phase1_good_streak3(self):
        """Phase 1, Good, streak=3: 10 + (3 × 2) = 16."""
        result = calculate_good_interval(base=10, good_streak=3)
        assert result == 16

    # Phase 2: interval + (streak × 1.5)
    def test_phase2_good_streak1(self):
        """Phase 2, Good, streak=1: 20 + (1 × 1.5) = 21."""
        result = calculate_good_interval(base=20, good_streak=1)
        assert result == 21

    def test_phase2_good_streak2(self):
        """Phase 2, Good, streak=2: 20 + (2 × 1.5) = 23."""
        result = calculate_good_interval(base=20, good_streak=2)
        assert result == 23

    def test_phase2_good_streak4(self):
        """Phase 2, Good, streak=4: 25 + (4 × 1.5) = 31."""
        result = calculate_good_interval(base=25, good_streak=4)
        assert result == 31

    # Phase 3: interval + (streak × 1)
    def test_phase3_good_streak1(self):
        """Phase 3, Good, streak=1: 35 + (1 × 1) = 36."""
        result = calculate_good_interval(base=35, good_streak=1)
        assert result == 36

    def test_phase3_good_streak2(self):
        """Phase 3, Good, streak=2: 35 + (2 × 1) = 37."""
        result = calculate_good_interval(base=35, good_streak=2)
        assert result == 37

    def test_phase3_good_streak5(self):
        """Phase 3, Good, streak=5: 32 + (5 × 1) = 37."""
        result = calculate_good_interval(base=32, good_streak=5)
        assert result == 37

    # Phase 4: interval + 3 (fixed, streak ignored)
    def test_phase4_good_streak1(self):
        """Phase 4, Good, streak=1: 45 + 3 = 48 (fixed)."""
        result = calculate_good_interval(base=45, good_streak=1)
        assert result == 48

    def test_phase4_good_streak5(self):
        """Phase 4, Good, streak=5: 45 + 3 = 48 (streak ignored)."""
        result = calculate_good_interval(base=45, good_streak=5)
        assert result == 48

    def test_phase4_good_high_interval(self):
        """Phase 4, Good: 100 + 3 = 103."""
        result = calculate_good_interval(base=100, good_streak=2)
        assert result == 103


# =============================================================================
# Category C: On-Time Reviews - Ok Rating by Phase
# =============================================================================

class TestCalculateOkInterval:
    """Test Ok rating interval calculation by phase."""

    # Phase 1: interval + 2
    def test_phase1_ok(self):
        """Phase 1, Ok: 7 + 2 = 9."""
        result = calculate_ok_interval(base=7)
        assert result == 9

    def test_phase1_ok_higher(self):
        """Phase 1, Ok: 12 + 2 = 14."""
        result = calculate_ok_interval(base=12)
        assert result == 14

    # Phase 2: interval + 1
    def test_phase2_ok(self):
        """Phase 2, Ok: 20 + 1 = 21."""
        result = calculate_ok_interval(base=20)
        assert result == 21

    def test_phase2_ok_higher(self):
        """Phase 2, Ok: 28 + 1 = 29."""
        result = calculate_ok_interval(base=28)
        assert result == 29

    # Phase 3: interval + 0 (stay)
    def test_phase3_ok(self):
        """Phase 3, Ok: 35 + 0 = 35 (stay)."""
        result = calculate_ok_interval(base=35)
        assert result == 35

    def test_phase3_ok_at_cap(self):
        """Phase 3, Ok at 39: stays at 39."""
        result = calculate_ok_interval(base=39)
        assert result == 39

    # Phase 4: cap at 40
    def test_phase4_ok_caps_at_40(self):
        """Phase 4, Ok at 45: caps at 40."""
        result = calculate_ok_interval(base=45)
        assert result == 40

    def test_phase4_ok_high_interval(self):
        """Phase 4, Ok at 100: caps at 40."""
        result = calculate_ok_interval(base=100)
        assert result == 40


# =============================================================================
# Category C: On-Time Reviews - Bad Rating by Phase
# =============================================================================

class TestCalculateBadInterval:
    """Test Bad rating interval calculation by phase."""

    # Under 30: divide by (streak + 1)
    def test_phase1_bad_streak1(self):
        """Phase 1, Bad, streak=1: 10 ÷ 2 = 5."""
        result = calculate_bad_interval(base=10, bad_streak=1)
        assert result == 5

    def test_phase1_bad_streak2(self):
        """Phase 1, Bad, streak=2: 12 ÷ 3 = 4."""
        result = calculate_bad_interval(base=12, bad_streak=2)
        assert result == 4

    def test_phase2_bad_streak1(self):
        """Phase 2, Bad, streak=1: 20 ÷ 2 = 10."""
        result = calculate_bad_interval(base=20, bad_streak=1)
        assert result == 10

    def test_phase2_bad_streak2(self):
        """Phase 2, Bad, streak=2: 21 ÷ 3 = 7."""
        result = calculate_bad_interval(base=21, bad_streak=2)
        assert result == 7

    def test_phase2_bad_streak3(self):
        """Phase 2, Bad, streak=3: 28 ÷ 4 = 7."""
        result = calculate_bad_interval(base=28, bad_streak=3)
        assert result == 7

    # At or above 30: drop to floor
    def test_phase3_bad_drops_to_floor(self):
        """Phase 3, Bad at 35: drops to 30."""
        result = calculate_bad_interval(base=35, bad_streak=1)
        assert result == 30

    def test_phase3_bad_at_30(self):
        """Phase 3, Bad at exactly 30: stays at 30."""
        result = calculate_bad_interval(base=30, bad_streak=1)
        assert result == 30

    def test_phase4_bad_drops_to_floor(self):
        """Phase 4, Bad at 50: drops to 30."""
        result = calculate_bad_interval(base=50, bad_streak=1)
        assert result == 30

    def test_phase4_bad_high_interval(self):
        """Phase 4, Bad at 100: drops to 30."""
        result = calculate_bad_interval(base=100, bad_streak=2)
        assert result == 30


# =============================================================================
# Category H: Constraints - Minimum Interval
# =============================================================================

class TestMinimumInterval:
    """Test minimum interval enforcement."""

    def test_bad_enforces_minimum(self):
        """Bad at 4, streak=1: 4 ÷ 2 = 2 → enforced to 3."""
        result = calculate_bad_interval(base=4, bad_streak=1)
        assert result == SRS_MIN_INTERVAL
        assert result == 3

    def test_bad_high_streak_enforces_minimum(self):
        """Bad at 10, streak=4: 10 ÷ 5 = 2 → enforced to 3."""
        result = calculate_bad_interval(base=10, bad_streak=4)
        assert result == 3

    def test_bad_very_low_interval(self):
        """Bad at 3, streak=1: 3 ÷ 2 = 1 → enforced to 3."""
        result = calculate_bad_interval(base=3, bad_streak=1)
        assert result == 3

    def test_bad_result_exactly_minimum(self):
        """Bad at 6, streak=1: 6 ÷ 2 = 3 (exactly minimum)."""
        result = calculate_bad_interval(base=6, bad_streak=1)
        assert result == 3


# =============================================================================
# Category D: Late Reviews
# =============================================================================

class TestLateReviews:
    """Test base interval calculation for late reviews."""

    def test_late_good_full_credit(self):
        """Late + Good: 100% credit, base = actual."""
        result = get_base_interval(planned=10, actual=20, rating=1)
        assert result == 20

    def test_late_ok_half_credit(self):
        """Late + Ok: 50% credit, base = 10 + (10 × 0.5) = 15."""
        result = get_base_interval(planned=10, actual=20, rating=0)
        assert result == 15

    def test_late_bad_quarter_credit(self):
        """Late + Bad: 25% credit, base = 10 + (10 × 0.25) = 12."""
        result = get_base_interval(planned=10, actual=20, rating=-1)
        assert result == 12

    def test_late_good_large_gap(self):
        """Late + Good with large gap: actual = 50."""
        result = get_base_interval(planned=20, actual=50, rating=1)
        assert result == 50

    def test_late_ok_large_gap(self):
        """Late + Ok with large gap: 20 + (30 × 0.5) = 35."""
        result = get_base_interval(planned=20, actual=50, rating=0)
        assert result == 35

    def test_late_bad_large_gap(self):
        """Late + Bad with large gap: 20 + (30 × 0.25) = 27."""
        result = get_base_interval(planned=20, actual=50, rating=-1)
        assert result == 27


# =============================================================================
# Category E: Early Reviews
# =============================================================================

class TestEarlyReviews:
    """Test base interval calculation for early reviews."""

    def test_early_good_returns_none(self):
        """Early + Good: returns None (reschedule only)."""
        result = get_base_interval(planned=10, actual=7, rating=1)
        assert result is None

    def test_early_ok_uses_planned(self):
        """Early + Ok: uses planned as base."""
        result = get_base_interval(planned=10, actual=7, rating=0)
        assert result == 10

    def test_early_bad_uses_planned(self):
        """Early + Bad: uses planned as base."""
        result = get_base_interval(planned=10, actual=7, rating=-1)
        assert result == 10

    def test_ontime_good_not_none(self):
        """On-time + Good: returns planned (not None)."""
        result = get_base_interval(planned=10, actual=10, rating=1)
        # On-time is actual == planned, should use planned
        assert result == 10

    def test_ontime_ok(self):
        """On-time + Ok: uses planned."""
        result = get_base_interval(planned=10, actual=10, rating=0)
        assert result == 10


# =============================================================================
# Category G: Graduation
# =============================================================================

class TestGraduation:
    """Test graduation logic."""

    def test_no_graduation_streak_0(self):
        """Streak 0: no graduation."""
        assert should_graduate(0) is False

    def test_no_graduation_streak_1(self):
        """Streak 1: no graduation."""
        assert should_graduate(1) is False

    def test_no_graduation_streak_2(self):
        """Streak 2: no graduation."""
        assert should_graduate(2) is False

    def test_graduation_streak_3(self):
        """Streak 3: graduation (default threshold)."""
        assert should_graduate(3) is True

    def test_graduation_streak_5(self):
        """Streak 5: graduation (above threshold)."""
        assert should_graduate(5) is True


# =============================================================================
# Category E: Reschedule Only Check
# =============================================================================

class TestRescheduleOnly:
    """Test reschedule-only detection."""

    def test_early_good_reschedule_only(self):
        """Early + Good: reschedule only."""
        assert should_reschedule_only(actual=7, planned=10, rating=1) is True

    def test_ontime_good_not_reschedule_only(self):
        """On-time + Good: not reschedule only."""
        assert should_reschedule_only(actual=10, planned=10, rating=1) is False

    def test_late_good_not_reschedule_only(self):
        """Late + Good: not reschedule only."""
        assert should_reschedule_only(actual=15, planned=10, rating=1) is False

    def test_early_ok_not_reschedule_only(self):
        """Early + Ok: not reschedule only (needs recalc)."""
        assert should_reschedule_only(actual=7, planned=10, rating=0) is False

    def test_early_bad_not_reschedule_only(self):
        """Early + Bad: not reschedule only (needs recalc)."""
        assert should_reschedule_only(actual=7, planned=10, rating=-1) is False


# =============================================================================
# Integration: calculate_next_interval
# =============================================================================

class TestCalculateNextInterval:
    """Test the main interval calculation function."""

    def test_good_phase1(self):
        """Good in phase 1 with streak."""
        result = calculate_next_interval(base=10, rating=1, good_streak=2, bad_streak=0)
        # Phase 1: 10 + (2 × 2) = 14
        assert result == 14

    def test_ok_phase2(self):
        """Ok in phase 2."""
        result = calculate_next_interval(base=20, rating=0, good_streak=0, bad_streak=0)
        # Phase 2: 20 + 1 = 21
        assert result == 21

    def test_bad_phase1(self):
        """Bad in phase 1 with streak."""
        result = calculate_next_interval(base=12, rating=-1, good_streak=0, bad_streak=2)
        # Phase 1: 12 ÷ 3 = 4
        assert result == 4

    def test_bad_phase3_drops_to_floor(self):
        """Bad in phase 3 drops to floor."""
        result = calculate_next_interval(base=35, rating=-1, good_streak=0, bad_streak=1)
        assert result == 30

    def test_ok_phase4_caps(self):
        """Ok in phase 4 caps at 40."""
        result = calculate_next_interval(base=50, rating=0, good_streak=0, bad_streak=0)
        assert result == 40


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_phase_boundary_13_to_14(self):
        """Boundary: 13 is phase 1, 14 is phase 2."""
        config_13 = get_phase_config(13)
        config_14 = get_phase_config(14)
        assert config_13["good_multiplier"] == 2.0
        assert config_14["good_multiplier"] == 1.5

    def test_phase_boundary_29_to_30(self):
        """Boundary: 29 is phase 2, 30 is phase 3."""
        config_29 = get_phase_config(29)
        config_30 = get_phase_config(30)
        assert config_29["good_multiplier"] == 1.5
        assert config_30["good_multiplier"] == 1.0

    def test_phase_boundary_39_to_40(self):
        """Boundary: 39 is phase 3, 40 is phase 4."""
        config_39 = get_phase_config(39)
        config_40 = get_phase_config(40)
        assert "good_multiplier" in config_39
        assert "good_increment" in config_40

    def test_streak_0_good(self):
        """Good with streak 0: interval + 0 = same."""
        result = calculate_good_interval(base=10, good_streak=0)
        # Phase 1: 10 + (0 × 2) = 10
        assert result == 10

    def test_very_high_streak(self):
        """High streak doesn't cause issues."""
        result = calculate_good_interval(base=10, good_streak=100)
        # Phase 1: 10 + (100 × 2) = 210
        assert result == 210

    def test_late_review_exactly_one_day(self):
        """Late by exactly 1 day."""
        result = get_base_interval(planned=10, actual=11, rating=0)
        # Ok: 10 + (1 × 0.5) = 10.5 → 10
        assert result == 10
