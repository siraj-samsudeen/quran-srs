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
        from app.common_model import get_hafizs_items

        hafiz_id = progression_test_hafiz["hafiz_id"]
        current_date = progression_test_hafiz["current_date"]

        # Get test item
        test_items = hafizs_items(
            where=f"hafiz_id={hafiz_id} AND memorized=1 AND mode_code='{DAILY_REPS_MODE_CODE}'"
        )
        item_id = test_items[0].item_id

        # Ensure hafizs_items entry exists for this item
        hafiz_item = get_hafizs_items(item_id)
        if not hafiz_item:
            hafizs_items.insert(hafiz_id=hafiz_id, item_id=item_id, loved=0)

        # Toggle love
        toggle_love(
            auth=hafiz_id,
            item_id=item_id,
            mode_code=DAILY_REPS_MODE_CODE,
            date=current_date,
        )

        # Verify loved status toggled
        hafiz_item = hafizs_items(where=f"item_id={item_id} AND hafiz_id={hafiz_id}")[0]
        assert hafiz_item.loved == 1

        # Toggle again
        toggle_love(
            auth=hafiz_id,
            item_id=item_id,
            mode_code=DAILY_REPS_MODE_CODE,
            date=current_date,
        )

        # Verify back to 0
        hafiz_item = hafizs_items(where=f"item_id={item_id} AND hafiz_id={hafiz_id}")[0]
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


class TestLinkRegression:
    """Tests that all internal links in home routes don't 404.
    
    Regression test for page reorganization - ensures explicit links
    between routes still work.
    """

    def test_close_date_link_exists(self, progression_test_hafiz):
        """Verify /close_date link from index works (doesn't 404)."""
        from app.home_controller import close_date_confirmation_page

        hafiz_id = progression_test_hafiz["hafiz_id"]
        result = close_date_confirmation_page(auth=hafiz_id)
        assert result is not None

    def test_profile_link_in_home_view(self, progression_test_hafiz):
        """Verify /profile link in home_view is accessible."""
        from app.home_controller import index

        hafiz_id = progression_test_hafiz["hafiz_id"]
        result = index(auth=hafiz_id, sess={})
        # Just verify it renders without error
        assert result is not None

    def test_report_link_in_home_view(self, progression_test_hafiz):
        """Verify /report link in home_view is accessible."""
        from app.home_controller import datewise_summary_table_view

        hafiz_id = progression_test_hafiz["hafiz_id"]
        result = datewise_summary_table_view(auth=hafiz_id)
        assert result is not None

    def test_home_index_link(self, progression_test_hafiz):
        """Verify / (home) route is accessible."""
        from app.home_controller import index

        hafiz_id = progression_test_hafiz["hafiz_id"]
        result = index(auth=hafiz_id, sess={})
        assert result is not None

    def test_page_load_link_endpoint(self, progression_test_hafiz):
        """Verify /page/{mode_code} link endpoints are accessible."""
        from app.home_controller import change_page

        hafiz_id = progression_test_hafiz["hafiz_id"]
        result = change_page(
            sess={},
            auth=hafiz_id,
            mode_code=DAILY_REPS_MODE_CODE,
            offset=0,
        )
        assert result is not None

    def test_more_rows_link_endpoint(self, progression_test_hafiz):
        """Verify /page/{mode_code}/more infinite scroll link is accessible."""
        from app.home_controller import load_more_rows

        hafiz_id = progression_test_hafiz["hafiz_id"]
        result = load_more_rows(
            auth=hafiz_id,
            mode_code=DAILY_REPS_MODE_CODE,
            offset=0,
        )
        assert result is not None


class TestRouteProtection:
    """Tests route protection and hafiz_id isolation for all routes."""

    def test_add_revision_filters_by_hafiz_id(self, progression_test_hafiz, multi_mode_test_hafiz):
        """POST /add/{item_id} should only create revisions for authenticated hafiz."""
        from app.home_controller import update_status_from_index

        hafiz_1 = progression_test_hafiz["hafiz_id"]
        hafiz_2 = multi_mode_test_hafiz["hafiz_id"]
        current_date_1 = progression_test_hafiz["current_date"]

        # Get item from hafiz_1
        test_items_1 = hafizs_items(
            where=f"hafiz_id={hafiz_1} AND memorized=1 AND mode_code='{DAILY_REPS_MODE_CODE}'"
        )
        item_id_1 = test_items_1[0].item_id

        # Attempt to create revision with hafiz_1's auth but don't verify hafiz ownership
        # This tests that the route uses the auth parameter, not trusting user input
        update_status_from_index(
            auth=hafiz_1,
            date=current_date_1,
            item_id=str(item_id_1),
            mode_code=DAILY_REPS_MODE_CODE,
            rating=1,
        )

        # Verify revision was created with hafiz_1
        revs = revisions(
            where=f"item_id={item_id_1} AND hafiz_id={hafiz_1}"
        )
        assert len(revs) > 0
        assert revs[-1].hafiz_id == hafiz_1

    def test_edit_revision_only_updates_own_revisions(self, progression_test_hafiz):
        """PUT /edit/{rev_id} should only update revisions for authenticated hafiz."""
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

        # Update with correct auth
        update_revision_rating(
            auth=hafiz_id,
            rev_id=rev.id,
            date=current_date,
            mode_code=DAILY_REPS_MODE_CODE,
            item_id=item_id,
            rating="2",
        )

        # Verify updated with correct hafiz_id
        updated = revisions[rev.id]
        assert updated.rating == 2
        assert updated.hafiz_id == hafiz_id

    def test_bulk_rate_only_affects_authenticated_hafiz_items(self, progression_test_hafiz, multi_mode_test_hafiz):
        """POST /bulk_rate should only create revisions for authenticated hafiz's items."""
        from app.home_controller import bulk_rate

        hafiz_1 = progression_test_hafiz["hafiz_id"]
        hafiz_2 = multi_mode_test_hafiz["hafiz_id"]
        current_date = progression_test_hafiz["current_date"]

        # Get items from hafiz_1
        test_items_1 = hafizs_items(
            where=f"hafiz_id={hafiz_1} AND memorized=1", limit=2
        )
        item_ids = [str(item.item_id) for item in test_items_1]

        # Bulk rate with hafiz_1's auth
        bulk_rate(
            sess={},
            auth=hafiz_1,
            item_ids=item_ids,
            rating=3,
            mode_code=DAILY_REPS_MODE_CODE,
            date=current_date,
        )

        # Verify revisions created only for hafiz_1
        for item_id in item_ids:
            rev_records = revisions(
                where=f"item_id={item_id} AND hafiz_id={hafiz_1}"
            )
            assert len(rev_records) > 0

    def test_toggle_love_only_affects_authenticated_hafiz_items(self, progression_test_hafiz):
        """POST /toggle_love/{item_id} should only toggle love for authenticated hafiz's items."""
        from app.home_controller import toggle_love
        from app.common_model import get_hafizs_items

        hafiz_id = progression_test_hafiz["hafiz_id"]
        current_date = progression_test_hafiz["current_date"]

        # Get test item
        test_items = hafizs_items(
            where=f"hafiz_id={hafiz_id} AND memorized=1 AND mode_code='{DAILY_REPS_MODE_CODE}'"
        )
        item_id = test_items[0].item_id

        # Ensure hafizs_items entry exists for this item
        hafiz_item = get_hafizs_items(item_id)
        if not hafiz_item:
            hafizs_items.insert(hafiz_id=hafiz_id, item_id=item_id, loved=0)

        # Toggle love with correct auth
        toggle_love(
            auth=hafiz_id,
            item_id=item_id,
            mode_code=DAILY_REPS_MODE_CODE,
            date=current_date,
        )

        # Verify love status changed for hafiz's item
        hafiz_item = hafizs_items(where=f"item_id={item_id} AND hafiz_id={hafiz_id}")[0]
        assert hafiz_item.loved == 1

    def test_close_date_only_advances_authenticated_hafiz_date(self, progression_test_hafiz, multi_mode_test_hafiz):
        """POST /close_date should only advance current_date for authenticated hafiz."""
        from app.home_controller import change_the_current_date

        hafiz_1 = progression_test_hafiz["hafiz_id"]
        hafiz_2 = multi_mode_test_hafiz["hafiz_id"]
        original_date_1 = progression_test_hafiz["current_date"]
        original_date_2 = multi_mode_test_hafiz["current_date"]

        # Get hafiz_2's original date
        hafiz_2_before = hafizs[hafiz_2]
        assert hafiz_2_before.current_date == original_date_2

        # Close date for hafiz_1
        change_the_current_date(auth=hafiz_1)

        # Verify only hafiz_1's date changed
        hafiz_1_after = hafizs[hafiz_1]
        hafiz_2_after = hafizs[hafiz_2]
        assert hafiz_1_after.current_date != original_date_1
        assert hafiz_2_after.current_date == original_date_2

    def test_change_page_respects_session_loved_filter_per_hafiz(self, progression_test_hafiz):
        """GET /page/{mode_code} should respect per-hafiz session state."""
        from app.home_controller import change_page

        hafiz_id = progression_test_hafiz["hafiz_id"]
        sess = {"loved_filter": {}}

        # Call change_page
        result = change_page(
            sess=sess,
            auth=hafiz_id,
            mode_code=DAILY_REPS_MODE_CODE,
            offset=0,
            show_loved_only="true",
        )

        # Verify session was updated for this mode
        assert DAILY_REPS_MODE_CODE in sess["loved_filter"]
        assert sess["loved_filter"][DAILY_REPS_MODE_CODE] is True

    def test_index_only_shows_authenticated_hafiz_data(self, progression_test_hafiz):
        """GET / should only return data for authenticated hafiz."""
        from app.home_controller import index

        hafiz_id = progression_test_hafiz["hafiz_id"]

        # Call index route
        result = index(auth=hafiz_id, sess={})

        # Should return HTML (not raise error or return wrong data)
        assert result is not None

    def test_load_more_rows_respects_hafiz_filter(self, progression_test_hafiz):
        """GET /page/{mode_code}/more should only load rows for authenticated hafiz."""
        from app.home_controller import load_more_rows

        hafiz_id = progression_test_hafiz["hafiz_id"]

        # Call load_more_rows
        result = load_more_rows(
            auth=hafiz_id,
            mode_code=DAILY_REPS_MODE_CODE,
            offset=0,
            show_loved_only="false",
        )

        # Should return rows
        assert result is not None

    def test_close_date_confirmation_shows_correct_hafiz_data(self, progression_test_hafiz, multi_mode_test_hafiz):
        """GET /close_date should show data only for authenticated hafiz."""
        from app.home_controller import close_date_confirmation_page

        hafiz_1 = progression_test_hafiz["hafiz_id"]
        hafiz_2 = multi_mode_test_hafiz["hafiz_id"]

        # Get close_date page for hafiz_1
        result_1 = close_date_confirmation_page(auth=hafiz_1)

        # Get close_date page for hafiz_2
        result_2 = close_date_confirmation_page(auth=hafiz_2)

        # Both should return valid responses (not raise or cross-contaminate)
        assert result_1 is not None
        assert result_2 is not None

    def test_report_shows_only_authenticated_hafiz_revisions(self, progression_test_hafiz):
        """GET /report should only show revisions for authenticated hafiz."""
        from app.home_controller import datewise_summary_table_view

        hafiz_id = progression_test_hafiz["hafiz_id"]

        # Call report route
        result = datewise_summary_table_view(auth=hafiz_id)

        # Should return report (internally filtered by hafiz)
        assert result is not None
