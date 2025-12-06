"""
Backend tests for mode transitions.

Tests the core business logic of mode progression:
- DR → WR (after 7 reviews)
- WR → FC (after 7 reviews)
- FC → SRS (on Ok/Bad rating via Close Date)
- SRS → FC (when interval > 99)

These tests call functions directly without browser interaction.
"""

import os
import pytest

os.environ["ENV"] = "test"

from app.globals import (
    hafizs_items,
    revisions,
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
    SRS_MODE_CODE,
    Revision,
)
from app.hafiz_model import hafizs
from app.fixed_reps_service import update_rep_item, REP_MODES_CONFIG
from app.srs_reps_service import (
    start_srs,
    update_hafiz_item_for_srs,
    SRS_END_INTERVAL,
)
from app.common_model import get_current_date
from app.utils import add_days_to_date


def get_hafiz_item(hafiz_id: int, item_id: int):
    """Helper to get hafizs_items record."""
    items = hafizs_items(where=f"hafiz_id = {hafiz_id} AND item_id = {item_id}")
    return items[0] if items else None


@pytest.fixture
def test_hafiz_id():
    """Return the ID of an existing test hafiz."""
    return 1


@pytest.fixture
def test_item_in_dr(test_hafiz_id):
    """Find or prepare an item in Daily Reps mode."""
    dr_items = hafizs_items(
        where=f"hafiz_id = {test_hafiz_id} AND mode_code = '{DAILY_REPS_MODE_CODE}'"
    )
    if dr_items:
        return dr_items[0].item_id
    # If none, find any item and set it to DR mode
    any_item = hafizs_items(where=f"hafiz_id = {test_hafiz_id}")[0]
    any_item.mode_code = DAILY_REPS_MODE_CODE
    any_item.next_interval = 1
    hafizs_items.update(any_item)
    return any_item.item_id


@pytest.fixture
def test_item_in_wr(test_hafiz_id):
    """Find or prepare an item in Weekly Reps mode."""
    wr_items = hafizs_items(
        where=f"hafiz_id = {test_hafiz_id} AND mode_code = '{WEEKLY_REPS_MODE_CODE}'"
    )
    if wr_items:
        return wr_items[0].item_id
    any_item = hafizs_items(where=f"hafiz_id = {test_hafiz_id}")[0]
    any_item.mode_code = WEEKLY_REPS_MODE_CODE
    any_item.next_interval = 7
    hafizs_items.update(any_item)
    return any_item.item_id


@pytest.fixture
def test_item_in_fc(test_hafiz_id):
    """Find or prepare an item in Full Cycle mode."""
    fc_items = hafizs_items(
        where=f"hafiz_id = {test_hafiz_id} AND mode_code = '{FULL_CYCLE_MODE_CODE}' AND memorized = 1"
    )
    if fc_items:
        return fc_items[0].item_id
    any_item = hafizs_items(where=f"hafiz_id = {test_hafiz_id}")[0]
    any_item.mode_code = FULL_CYCLE_MODE_CODE
    any_item.memorized = True
    any_item.next_interval = None
    any_item.next_review = None
    hafizs_items.update(any_item)
    return any_item.item_id


@pytest.fixture
def test_item_in_srs(test_hafiz_id):
    """Find or prepare an item in SRS mode."""
    srs_items = hafizs_items(
        where=f"hafiz_id = {test_hafiz_id} AND mode_code = '{SRS_MODE_CODE}'"
    )
    if srs_items:
        return srs_items[0].item_id
    any_item = hafizs_items(where=f"hafiz_id = {test_hafiz_id}")[0]
    any_item.mode_code = SRS_MODE_CODE
    any_item.next_interval = 7
    any_item.memorized = True
    hafizs_items.update(any_item)
    return any_item.item_id


class TestDailyRepsTransition:
    """Tests for Daily Reps → Weekly Reps transition."""

    def test_dr_stays_in_dr_before_threshold(self, test_hafiz_id, test_item_in_dr):
        """Item remains in DR mode when review count < 7."""
        item_id = test_item_in_dr
        current_date = get_current_date(test_hafiz_id)

        # Clear existing DR revisions for this item
        for rev in revisions(
            where=f"item_id = {item_id} AND mode_code = '{DAILY_REPS_MODE_CODE}'"
        ):
            revisions.delete(rev.id)

        # Add 5 revisions (below threshold of 7)
        for i in range(5):
            revisions.insert(
                hafiz_id=test_hafiz_id,
                item_id=item_id,
                mode_code=DAILY_REPS_MODE_CODE,
                revision_date=current_date,
                rating=1,
            )

        # Ensure item is in DR mode
        item = get_hafiz_item(test_hafiz_id, item_id)
        item.mode_code = DAILY_REPS_MODE_CODE
        item.next_interval = 1
        hafizs_items.update(item)

        # Create a revision object to pass to update_rep_item
        rev = Revision(
            id=0,
            hafiz_id=test_hafiz_id,
            item_id=item_id,
            mode_code=DAILY_REPS_MODE_CODE,
            revision_date=current_date,
            rating=1,
        )

        # Act
        update_rep_item(rev)

        # Assert - still in DR mode
        item = get_hafiz_item(test_hafiz_id, item_id)
        assert item.mode_code == DAILY_REPS_MODE_CODE
        assert item.next_interval == 1

    def test_dr_to_wr_at_threshold(self, test_hafiz_id, test_item_in_dr):
        """Item graduates to WR mode after 7 DR reviews."""
        item_id = test_item_in_dr
        current_date = get_current_date(test_hafiz_id)

        # Clear existing DR revisions
        for rev in revisions(
            where=f"item_id = {item_id} AND mode_code = '{DAILY_REPS_MODE_CODE}'"
        ):
            revisions.delete(rev.id)

        # Add exactly 7 revisions (at threshold)
        for i in range(7):
            revisions.insert(
                hafiz_id=test_hafiz_id,
                item_id=item_id,
                mode_code=DAILY_REPS_MODE_CODE,
                revision_date=current_date,
                rating=1,
            )

        # Ensure item is in DR mode
        item = get_hafiz_item(test_hafiz_id, item_id)
        item.mode_code = DAILY_REPS_MODE_CODE
        item.next_interval = 1
        hafizs_items.update(item)

        # Create revision object
        rev = Revision(
            id=0,
            hafiz_id=test_hafiz_id,
            item_id=item_id,
            mode_code=DAILY_REPS_MODE_CODE,
            revision_date=current_date,
            rating=1,
        )

        # Act
        update_rep_item(rev)

        # Assert - graduated to WR mode
        item = get_hafiz_item(test_hafiz_id, item_id)
        assert item.mode_code == WEEKLY_REPS_MODE_CODE
        assert item.next_interval == 7  # WR interval


class TestWeeklyRepsTransition:
    """Tests for Weekly Reps → Full Cycle transition."""

    def test_wr_stays_in_wr_before_threshold(self, test_hafiz_id, test_item_in_wr):
        """Item remains in WR mode when review count < 7."""
        item_id = test_item_in_wr
        current_date = get_current_date(test_hafiz_id)

        # Clear existing WR revisions
        for rev in revisions(
            where=f"item_id = {item_id} AND mode_code = '{WEEKLY_REPS_MODE_CODE}'"
        ):
            revisions.delete(rev.id)

        # Add 5 revisions (below threshold)
        for i in range(5):
            revisions.insert(
                hafiz_id=test_hafiz_id,
                item_id=item_id,
                mode_code=WEEKLY_REPS_MODE_CODE,
                revision_date=current_date,
                rating=1,
            )

        # Ensure item is in WR mode
        item = get_hafiz_item(test_hafiz_id, item_id)
        item.mode_code = WEEKLY_REPS_MODE_CODE
        item.next_interval = 7
        hafizs_items.update(item)

        rev = Revision(
            id=0,
            hafiz_id=test_hafiz_id,
            item_id=item_id,
            mode_code=WEEKLY_REPS_MODE_CODE,
            revision_date=current_date,
            rating=1,
        )

        # Act
        update_rep_item(rev)

        # Assert - still in WR mode
        item = get_hafiz_item(test_hafiz_id, item_id)
        assert item.mode_code == WEEKLY_REPS_MODE_CODE
        assert item.next_interval == 7

    def test_wr_to_fc_at_threshold(self, test_hafiz_id, test_item_in_wr):
        """Item graduates to FC mode after 7 WR reviews."""
        item_id = test_item_in_wr
        current_date = get_current_date(test_hafiz_id)

        # Clear existing WR revisions
        for rev in revisions(
            where=f"item_id = {item_id} AND mode_code = '{WEEKLY_REPS_MODE_CODE}'"
        ):
            revisions.delete(rev.id)

        # Add exactly 7 revisions
        for i in range(7):
            revisions.insert(
                hafiz_id=test_hafiz_id,
                item_id=item_id,
                mode_code=WEEKLY_REPS_MODE_CODE,
                revision_date=current_date,
                rating=1,
            )

        # Ensure item is in WR mode
        item = get_hafiz_item(test_hafiz_id, item_id)
        item.mode_code = WEEKLY_REPS_MODE_CODE
        item.next_interval = 7
        hafizs_items.update(item)

        rev = Revision(
            id=0,
            hafiz_id=test_hafiz_id,
            item_id=item_id,
            mode_code=WEEKLY_REPS_MODE_CODE,
            revision_date=current_date,
            rating=1,
        )

        # Act
        update_rep_item(rev)

        # Assert - graduated to FC mode
        item = get_hafiz_item(test_hafiz_id, item_id)
        assert item.mode_code == FULL_CYCLE_MODE_CODE
        assert item.memorized == True
        assert item.next_interval is None  # FC doesn't use intervals
        assert item.next_review is None


class TestFullCycleToSRS:
    """Tests for Full Cycle → SRS transition."""

    def test_fc_to_srs_on_bad_rating(self, test_hafiz_id, test_item_in_fc):
        """Bad rating in FC triggers SRS with 3-day starting interval."""
        item_id = test_item_in_fc

        # Ensure item is in FC mode
        item = get_hafiz_item(test_hafiz_id, item_id)
        item.mode_code = FULL_CYCLE_MODE_CODE
        item.memorized = True
        item.next_interval = None
        hafizs_items.update(item)

        # Act - start SRS with bad rating (-1)
        start_srs(item_id=item_id, auth=test_hafiz_id, rating=-1)

        # Assert - now in SRS with 3-day interval
        item = get_hafiz_item(test_hafiz_id, item_id)
        assert item.mode_code == SRS_MODE_CODE
        assert item.next_interval == 3  # Bad rating → 3 days

    def test_fc_to_srs_on_ok_rating(self, test_hafiz_id, test_item_in_fc):
        """Ok rating in FC triggers SRS with 10-day starting interval."""
        item_id = test_item_in_fc

        # Ensure item is in FC mode
        item = get_hafiz_item(test_hafiz_id, item_id)
        item.mode_code = FULL_CYCLE_MODE_CODE
        item.memorized = True
        item.next_interval = None
        hafizs_items.update(item)

        # Act - start SRS with ok rating (0)
        start_srs(item_id=item_id, auth=test_hafiz_id, rating=0)

        # Assert - now in SRS with 10-day interval
        item = get_hafiz_item(test_hafiz_id, item_id)
        assert item.mode_code == SRS_MODE_CODE
        assert item.next_interval == 10  # Ok rating → 10 days


class TestSRSGraduation:
    """Tests for SRS → Full Cycle graduation."""

    def test_srs_stays_in_srs_below_threshold(self, test_hafiz_id, test_item_in_srs):
        """Item stays in SRS when next interval <= 99."""
        item_id = test_item_in_srs
        current_date = get_current_date(test_hafiz_id)

        # Set up item in SRS with interval below threshold
        item = get_hafiz_item(test_hafiz_id, item_id)
        item.mode_code = SRS_MODE_CODE
        item.next_interval = 29  # Well below 99
        item.last_review = add_days_to_date(current_date, -29)  # 29 days ago
        item.memorized = True
        hafizs_items.update(item)

        # Create revision with good rating
        rev_id = revisions.insert(
            hafiz_id=test_hafiz_id,
            item_id=item_id,
            mode_code=SRS_MODE_CODE,
            revision_date=current_date,
            rating=1,  # Good
        ).id
        rev = revisions[rev_id]

        # Act
        update_hafiz_item_for_srs(rev)

        # Assert - still in SRS (next interval should be 31, the next prime)
        item = get_hafiz_item(test_hafiz_id, item_id)
        assert item.mode_code == SRS_MODE_CODE
        assert item.next_interval <= SRS_END_INTERVAL

    def test_srs_to_fc_when_interval_exceeds_99(self, test_hafiz_id, test_item_in_srs):
        """Item graduates to FC when SRS interval would exceed 99."""
        item_id = test_item_in_srs
        current_date = get_current_date(test_hafiz_id)

        # Set up item in SRS with interval at 97 (next prime is 101, > 99)
        item = get_hafiz_item(test_hafiz_id, item_id)
        item.mode_code = SRS_MODE_CODE
        item.next_interval = 97
        item.last_review = add_days_to_date(current_date, -97)  # 97 days ago
        item.memorized = True
        hafizs_items.update(item)

        # Create revision with good rating (would push to 101)
        rev_id = revisions.insert(
            hafiz_id=test_hafiz_id,
            item_id=item_id,
            mode_code=SRS_MODE_CODE,
            revision_date=current_date,
            rating=1,  # Good
        ).id
        rev = revisions[rev_id]

        # Act
        update_hafiz_item_for_srs(rev)

        # Assert - graduated back to FC
        item = get_hafiz_item(test_hafiz_id, item_id)
        assert item.mode_code == FULL_CYCLE_MODE_CODE
        assert item.memorized == True
        assert item.next_interval is None
        assert item.next_review is None
