"""Unit tests for home_controller routes.

Tests all route handlers in isolation using test fixtures.
"""

import pytest
from database import revisions, hafizs, hafizs_items, items
from constants import (
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
    NEW_MEMORIZATION_MODE_CODE,
)
from utils import add_days_to_date, current_time


class TestAddRevisionRoute:
    """Tests POST /add/{item_id} route."""

    def test_add_revision_creates_record(self, progression_test_hafiz):
        """POST /add/{item_id} creates revision record and returns updated row."""
        from app.home_controller import update_status_from_index

        hafiz_id = progression_test_hafiz["hafiz_id"]
        current_date = progression_test_hafiz["current_date"]

        # Get a test item
        test_items = hafizs_items(
            where=f"hafiz_id={hafiz_id} AND memorized=1 AND mode_code='{DAILY_REPS_MODE_CODE}'"
        )
        item_id = test_items[0].item_id

        # Count revisions before
        revs_before = revisions(where=f"item_id={item_id}")

        # Call route (auth = hafiz_id)
        result = update_status_from_index(
            auth=hafiz_id,
            date=current_date,
            item_id=str(item_id),
            mode_code=DAILY_REPS_MODE_CODE,
            rating=1,
        )

        # Verify revision created
        revs_after = revisions(where=f"item_id={item_id}")
        assert len(revs_after) > len(revs_before)
        assert revs_after[-1].rating == 1


class TestEditRevisionRoute:
    """Tests PUT /edit/{rev_id} route."""

    def test_edit_revision_updates_rating(self, progression_test_hafiz):
        """PUT /edit/{rev_id} updates revision rating."""
        from app.home_controller import update_revision_rating

        hafiz_id = progression_test_hafiz["hafiz_id"]
        current_date = progression_test_hafiz["current_date"]

        # Create a revision
        test_items = hafizs_items(
            where=f"hafiz_id={hafiz_id} AND memorized=1 AND mode_code='{DAILY_REPS_MODE_CODE}'"
        )
        item_id = test_items[0].item_id

        rev = revisions.insert(
            item_id=item_id,
            hafiz_id=hafiz_id,
            mode_code=DAILY_REPS_MODE_CODE,
            revision_date=current_date,
            rating=1,
        )

        # Update rating via route
        update_revision_rating(
            auth=hafiz_id,
            rev_id=rev.id,
            date=current_date,
            mode_code=DAILY_REPS_MODE_CODE,
            item_id=item_id,
            rating="0",  # Change to 0
        )

        # Verify updated
        updated = revisions[rev.id]
        assert updated.rating == 0


class TestBulkRateRoute:
    """Tests POST /bulk_rate route."""

    def test_bulk_rate_creates_multiple_revisions(self, multi_mode_test_hafiz):
        """POST /bulk_rate creates revision for multiple items."""
        from app.home_controller import bulk_rate

        hafiz_id = multi_mode_test_hafiz["hafiz_id"]
        current_date = multi_mode_test_hafiz["current_date"]

        # Get multiple test items
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id} AND memorized=1", limit=2)
        item_ids = [str(item.item_id) for item in test_items]

        # Call route with list of items
        bulk_rate(
            sess={},
            auth=hafiz_id,
            item_ids=item_ids,
            rating=1,
            mode_code=DAILY_REPS_MODE_CODE,
            date=current_date,
        )

        # Verify revisions created for all items
        for item_id in item_ids:
            rev_records = revisions(
                where=f"item_id={item_id} AND revision_date='{current_date}'"
            )
            assert len(rev_records) > 0


class TestToggleLoveRoute:
    """Tests POST /toggle_love/{item_id} route."""

    def test_toggle_love_marks_item_as_loved(self, progression_test_hafiz):
        """POST /toggle_love/{item_id} toggles love status."""
        from app.home_controller import toggle_love

        hafiz_id = progression_test_hafiz["hafiz_id"]
        current_date = progression_test_hafiz["current_date"]

        # Get test item
        test_items = hafizs_items(
            where=f"hafiz_id={hafiz_id} AND memorized=1 AND mode_code='{DAILY_REPS_MODE_CODE}'"
        )
        item_id = test_items[0].item_id

        # Toggle love
        toggle_love(
            auth=hafiz_id,
            item_id=item_id,
            mode_code=DAILY_REPS_MODE_CODE,
            date=current_date,
        )

        # Verify loved status toggled
        hafiz_item = hafizs_items(where=f"item_id={item_id}")[0]
        assert hafiz_item.loved == 1

        # Toggle again
        toggle_love(
            auth=hafiz_id,
            item_id=item_id,
            mode_code=DAILY_REPS_MODE_CODE,
            date=current_date,
        )

        # Verify back to 0
        hafiz_item = hafizs_items(where=f"item_id={item_id}")[0]
        assert hafiz_item.loved == 0


class TestCloseDate:
    """Tests /close_date GET and POST routes."""

    def test_close_date_confirmation_page(self, progression_test_hafiz):
        """GET /close_date returns confirmation page."""
        from app.home_controller import close_date_confirmation_page

        hafiz_id = progression_test_hafiz["hafiz_id"]

        # Call route
        result = close_date_confirmation_page(auth=hafiz_id)

        # Should return HTML response (contains modal/form)
        assert result is not None

    def test_close_date_advances_date_by_one(self, progression_test_hafiz):
        """POST /close_date advances current_date by 1 day."""
        from app.home_controller import change_the_current_date

        hafiz_id = progression_test_hafiz["hafiz_id"]
        current_date = progression_test_hafiz["current_date"]

        # Add revision on current date
        test_items = hafizs_items(
            where=f"hafiz_id={hafiz_id} AND memorized=1 AND mode_code='{DAILY_REPS_MODE_CODE}'"
        )
        if test_items:
            revisions.insert(
                item_id=test_items[0].item_id,
                hafiz_id=hafiz_id,
                mode_code=DAILY_REPS_MODE_CODE,
                revision_date=current_date,
                rating=1,
            )

        # Call close_date
        change_the_current_date(auth=hafiz_id)

        # Verify date advanced
        hafiz = hafizs[hafiz_id]
        expected_date = add_days_to_date(current_date, 1)
        assert hafiz.current_date == expected_date

    def test_close_date_with_skip(self, progression_test_hafiz):
        """POST /close_date with skip_to_date sets date to specified date."""
        from app.home_controller import change_the_current_date

        hafiz_id = progression_test_hafiz["hafiz_id"]
        skip_to = "2024-01-20"

        # Call close_date with skip
        change_the_current_date(auth=hafiz_id, skip_enabled="true", skip_to_date=skip_to)

        # Verify date is set to skip_to, not +1
        hafiz = hafizs[hafiz_id]
        assert hafiz.current_date == skip_to


class TestIndexRoute:
    """Tests GET / (home page) route."""

    def test_index_returns_home_page(self, progression_test_hafiz):
        """GET / returns home page with tabs and tables."""
        from app.home_controller import index

        hafiz_id = progression_test_hafiz["hafiz_id"]

        # Call route
        result = index(auth=hafiz_id, sess={})

        # Should return HTML response with tab structure
        assert result is not None


class TestPageLoadRoutes:
    """Tests /page/{mode_code} and /page/{mode_code}/more routes."""

    def test_change_page_returns_full_table(self, progression_test_hafiz):
        """GET /page/{mode_code} returns full table."""
        from app.home_controller import change_page

        hafiz_id = progression_test_hafiz["hafiz_id"]

        # Call route
        result = change_page(
            sess={}, auth=hafiz_id, mode_code=DAILY_REPS_MODE_CODE, offset=0
        )

        # Should return table content
        assert result is not None

    def test_load_more_rows(self, progression_test_hafiz):
        """GET /page/{mode_code}/more returns additional rows."""
        from app.home_controller import load_more_rows

        hafiz_id = progression_test_hafiz["hafiz_id"]

        # Call route
        result = load_more_rows(
            auth=hafiz_id, mode_code=DAILY_REPS_MODE_CODE, offset=10
        )

        # Should return rows
        assert result is not None


class TestReportRoute:
    """Tests GET /report route."""

    def test_datewise_summary_returns_report(self, progression_test_hafiz):
        """GET /report returns datewise summary report."""
        from app.home_controller import datewise_summary_table_view

        hafiz_id = progression_test_hafiz["hafiz_id"]

        # Call route
        result = datewise_summary_table_view(auth=hafiz_id)

        # Should return report
        assert result is not None
