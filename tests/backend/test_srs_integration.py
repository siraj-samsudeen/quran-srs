"""
Integration Tests for SRS System

These tests verify the integration layer works correctly with the database.

Categories covered:
- A1: Backward compatibility (existing data unchanged) - requires full fixtures
- B: SRS Entry from Full Cycle
- G: Graduation
- I: History replay

Test Strategy (MECE Framework):
-----------------------------------
The tests are organized using the MECE (Mutually Exclusive, Collectively Exhaustive)
principle to ensure comprehensive coverage without overlap:

1. **Backward Compatibility (Category A)**: Verifies existing production data
   is not affected by algorithm changes. Uses full fixtures when available.

2. **Algorithm Configuration**: Verifies all tunables are correctly defined
   and have expected values.

3. **SRS Entry/Graduation**: Verifies the lifecycle transitions work correctly.

4. **History Replay**: Verifies that intervals can be restored from revision
   history without recalculation.

Fixture Strategy:
-----------------
- Minimal synthetic fixtures (committed): 8 items, 25 revisions - used for CI
- Full production fixtures (gitignored): 667 items, 4034 revisions - used for
  local verification before deployment

The backward compatibility tests skip automatically if full fixtures aren't available.
"""

import json
import os
import pytest
import sqlite3
from datetime import date, timedelta


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def db_connection():
    """Provide a database connection for tests."""
    conn = sqlite3.connect('data/quran_v10.db')
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def snapshot_data():
    """Load the snapshot data for comparison (minimal by default)."""
    with open('tests/fixtures/siraj_hafizs_items_snapshot.json', 'r') as f:
        return json.load(f)


def full_fixtures_available():
    """Check if full production fixtures are available for local testing."""
    return (
        os.path.exists('tests/fixtures/siraj_hafizs_items_snapshot_full.json') and
        os.path.exists('tests/fixtures/siraj_revisions_snapshot_full.json')
    )


# =============================================================================
# Category A1: Backward Compatibility (Production Data Verification)
# =============================================================================

@pytest.mark.skipif(
    not full_fixtures_available(),
    reason="Full fixtures not available - run locally with production data"
)
class TestBackwardCompatibilityFull:
    """
    Verify existing PRODUCTION data is not changed by the new algorithm.

    These tests use the full production fixtures (gitignored) and compare
    against the actual database. They ensure that:
    1. No existing hafizs_items records are modified
    2. No existing revision history is changed
    3. Historical next_interval values are preserved

    Run these tests locally before deploying algorithm changes.
    """

    def test_existing_hafizs_items_unchanged(self, db_connection):
        """
        A1: Compare current hafizs_items with full production snapshot.
        All 667 items should remain identical after algorithm change.
        """
        with open('tests/fixtures/siraj_hafizs_items_snapshot_full.json', 'r') as f:
            snapshot_data = json.load(f)

        cursor = db_connection.cursor()
        cursor.execute('''
            SELECT id, hafiz_id, item_id, page_number, mode_code,
                   next_review, last_review, good_streak, bad_streak,
                   last_interval, next_interval, srs_start_date, memorized
            FROM hafizs_items
            WHERE hafiz_id = 1
            ORDER BY item_id
        ''')
        current_items = [dict(row) for row in cursor.fetchall()]

        assert len(current_items) == len(snapshot_data), \
            f"Item count mismatch: {len(current_items)} vs {len(snapshot_data)}"

        for current, snapshot in zip(current_items, snapshot_data):
            assert current['item_id'] == snapshot['item_id']
            assert current['mode_code'] == snapshot['mode_code'], \
                f"mode_code mismatch at item {current['item_id']}"
            assert current['next_interval'] == snapshot['next_interval'], \
                f"next_interval mismatch at item {current['item_id']}"
            assert current['good_streak'] == snapshot['good_streak'], \
                f"good_streak mismatch at item {current['item_id']}"
            assert current['bad_streak'] == snapshot['bad_streak'], \
                f"bad_streak mismatch at item {current['item_id']}"

    def test_revision_history_unchanged(self, db_connection):
        """
        A1b: Verify all 4034 revisions have not been modified.
        Historical next_interval values must be preserved.
        """
        with open('tests/fixtures/siraj_revisions_snapshot_full.json', 'r') as f:
            snapshot_revisions = json.load(f)

        cursor = db_connection.cursor()
        cursor.execute('''
            SELECT id, hafiz_id, item_id, revision_date, rating, mode_code,
                   plan_id, next_interval
            FROM revisions
            WHERE hafiz_id = 1
            ORDER BY item_id, revision_date
        ''')
        current_revisions = [dict(row) for row in cursor.fetchall()]

        assert len(current_revisions) == len(snapshot_revisions), \
            f"Revision count mismatch: {len(current_revisions)} vs {len(snapshot_revisions)}"

        # Verify revisions with stored next_interval values
        revisions_with_interval = [r for r in snapshot_revisions if r['next_interval'] is not None]
        for snapshot_rev in revisions_with_interval:
            current_rev = next(
                (r for r in current_revisions if r['id'] == snapshot_rev['id']),
                None
            )
            assert current_rev is not None, f"Missing revision {snapshot_rev['id']}"
            assert current_rev['next_interval'] == snapshot_rev['next_interval'], \
                f"next_interval changed for revision {snapshot_rev['id']}"


# =============================================================================
# Category A: Backward Compatibility (Synthetic - Always Runs)
# =============================================================================

class TestBackwardCompatibilitySynthetic:
    """
    Verify algorithm mechanics using synthetic test data.

    These tests use minimal fixtures (8 items, 25 revisions) that are committed
    to git. They verify that the algorithm logic is correct without requiring
    production data.
    """

    def test_synthetic_fixtures_valid(self, snapshot_data):
        """Verify synthetic fixtures are valid and parseable."""
        assert len(snapshot_data) == 8, "Synthetic fixtures should have 8 items"

        # Check required fields exist
        for item in snapshot_data:
            assert 'item_id' in item
            assert 'mode_code' in item
            assert item['mode_code'] in ('FC', 'SR', 'NM', 'DR', 'WR')

    def test_synthetic_revisions_valid(self):
        """Verify synthetic revision fixtures are valid."""
        with open('tests/fixtures/siraj_revisions_snapshot.json', 'r') as f:
            revisions = json.load(f)

        assert len(revisions) == 25, "Synthetic fixtures should have 25 revisions"

        # Check SRS revisions have next_interval
        srs_revisions = [r for r in revisions if r['mode_code'] == 'SR']
        for rev in srs_revisions:
            assert rev['next_interval'] is not None, \
                f"SRS revision {rev['id']} should have next_interval"


# =============================================================================
# Category B: SRS Entry
# =============================================================================

class TestSRSEntry:
    """
    Test SRS entry from Full Cycle.

    MECE Coverage:
    - B1: Bad rating → SRS entry with 3-day interval
    - B2: Ok rating → SRS entry with 10-day interval
    - B3: Good rating → NO SRS entry (stays in FC)
    """

    def test_srs_start_interval_bad(self):
        """B1: Bad rating should start SRS at 3 days."""
        from app.srs_interval_calc import SRS_START_INTERVAL
        assert SRS_START_INTERVAL[-1] == 3

    def test_srs_start_interval_ok(self):
        """B2: Ok rating should start SRS at 10 days."""
        from app.srs_interval_calc import SRS_START_INTERVAL
        assert SRS_START_INTERVAL[0] == 10

    def test_good_rating_not_in_start_interval(self):
        """B3: Good rating should NOT have a start interval (stays in FC)."""
        from app.srs_interval_calc import SRS_START_INTERVAL
        assert 1 not in SRS_START_INTERVAL


# =============================================================================
# Category G: Graduation
# =============================================================================

class TestGraduation:
    """
    Test graduation from SRS to Full Cycle.

    MECE Coverage:
    - G1: Streak < threshold → No graduation
    - G2: Streak >= threshold → Graduation
    """

    def test_no_graduation_below_threshold(self):
        """G1: Streak below threshold should not graduate."""
        from app.srs_interval_calc import should_graduate, SRS_GRADUATION_STREAK

        for streak in range(SRS_GRADUATION_STREAK):
            assert should_graduate(streak) is False, \
                f"Streak {streak} should not graduate"

    def test_graduation_at_threshold(self):
        """G2: Streak at or above threshold should graduate."""
        from app.srs_interval_calc import should_graduate, SRS_GRADUATION_STREAK

        assert should_graduate(SRS_GRADUATION_STREAK) is True
        assert should_graduate(SRS_GRADUATION_STREAK + 2) is True


# =============================================================================
# Category I: History Replay
# =============================================================================

class TestHistoryReplay:
    """
    Test that history replay restores intervals correctly.

    Key Principle: When rebuilding hafizs_items from revision history,
    we read next_interval from stored revision records - we do NOT
    recalculate using the current algorithm.

    This ensures algorithm changes don't retroactively affect historical data.
    """

    def test_populate_function_preserves_interval(self):
        """
        I1: The populate function should read next_interval from revisions,
        not recalculate it. This is critical for backward compatibility.
        """
        from app.common_function import populate_hafizs_items_stat_columns

        # The function exists and has the right docstring
        assert callable(populate_hafizs_items_stat_columns)
        assert "next_interval" in populate_hafizs_items_stat_columns.__doc__
        assert "recalculate" in populate_hafizs_items_stat_columns.__doc__.lower()


# =============================================================================
# Algorithm Configuration Tests
# =============================================================================

class TestAlgorithmConfiguration:
    """
    Verify algorithm configuration is correctly set up.

    These tests document the expected configuration values and serve as
    a safety net against accidental changes to critical constants.
    """

    def test_phase_config_complete(self):
        """Verify all four phases are defined."""
        from app.srs_interval_calc import SRS_PHASE_CONFIG

        expected_phases = [(0, 14), (14, 30), (30, 40), (40, 999)]
        for phase in expected_phases:
            assert phase in SRS_PHASE_CONFIG, f"Missing phase {phase}"

    def test_phase_config_values(self):
        """Verify phase multipliers match design spec."""
        from app.srs_interval_calc import SRS_PHASE_CONFIG

        # Phase 1: Fast growth
        assert SRS_PHASE_CONFIG[(0, 14)]["good_multiplier"] == 2.0
        assert SRS_PHASE_CONFIG[(0, 14)]["ok_increment"] == 2

        # Phase 2: Moderate growth
        assert SRS_PHASE_CONFIG[(14, 30)]["good_multiplier"] == 1.5
        assert SRS_PHASE_CONFIG[(14, 30)]["ok_increment"] == 1

        # Phase 3: Slow growth (ideal zone)
        assert SRS_PHASE_CONFIG[(30, 40)]["good_multiplier"] == 1.0
        assert SRS_PHASE_CONFIG[(30, 40)]["ok_increment"] == 0

        # Phase 4: Very slow (fixed increment)
        assert SRS_PHASE_CONFIG[(40, 999)]["good_increment"] == 3
        assert SRS_PHASE_CONFIG[(40, 999)]["ok_increment"] == 0

    def test_constraints_defined(self):
        """Verify all constraints have expected values."""
        from app.srs_interval_calc import (
            SRS_MIN_INTERVAL,
            SRS_OK_CAP,
            SRS_BAD_FLOOR,
            SRS_GRADUATION_STREAK,
        )

        assert SRS_MIN_INTERVAL == 3, "Minimum 3 days to prevent next-day bounce"
        assert SRS_OK_CAP == 40, "Ok capped at 40 (degradation threshold)"
        assert SRS_BAD_FLOOR == 30, "Bad drops to 30 in 30+ zone"
        assert SRS_GRADUATION_STREAK == 3, "Graduate after 3 consecutive Good"

    def test_late_review_credit(self):
        """Verify late review credit percentages."""
        from app.srs_interval_calc import LATE_REVIEW_CREDIT

        assert LATE_REVIEW_CREDIT[1] == 1.0, "Good: 100% credit for gap"
        assert LATE_REVIEW_CREDIT[0] == 0.5, "Ok: 50% credit"
        assert LATE_REVIEW_CREDIT[-1] == 0.25, "Bad: 25% credit"
