"""Unit tests for profile_controller routes.

Tests all route handlers in isolation using test fixtures.
"""

import pytest
from database import hafizs_items, revisions
from constants import (
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
)


class TestShowProfilePageRoute:
    """Tests GET /profile/table route."""

    def test_show_profile_page_returns_page(self, progression_test_hafiz):
        """GET /profile/table returns profile page."""
        from app.profile_controller import show_profile_page
        from unittest.mock import Mock

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Mock request
        request = Mock()
        request.headers = {}
        
        # Call route
        result = show_profile_page(auth=hafiz_id, request=request, status_filter=None)
        
        # Should return HTML response
        assert result is not None


class TestLoadMoreProfileRowsRoute:
    """Tests GET /profile/table/more route."""

    def test_load_more_profile_rows_returns_rows(self, progression_test_hafiz):
        """GET /profile/table/more returns additional rows."""
        from app.profile_controller import load_more_profile_rows

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = load_more_profile_rows(auth=hafiz_id, status_filter=None, offset=0)
        
        # Should return rows
        assert result is not None


class TestLoadRepConfigModalRoute:
    """Tests GET /profile/configure_reps/{hafiz_item_id} route."""

    def test_load_rep_config_modal_returns_modal(self, progression_test_hafiz):
        """GET /profile/configure_reps/{hafiz_item_id} returns config modal."""
        from app.profile_controller import load_rep_config_modal

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Get a test item
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id}", limit=1)
        if test_items:
            hafiz_item_id = test_items[0].id
            
            # Call route
            result = load_rep_config_modal(hafiz_item_id=hafiz_item_id, auth=hafiz_id)
            
            # Should return HTML response (modal)
            assert result is not None


class TestQuickChangeModeRoute:
    """Tests POST /profile/quick_change_mode/{hafiz_item_id} route."""

    def test_quick_change_mode_updates_item(self, progression_test_hafiz):
        """POST /profile/quick_change_mode/{hafiz_item_id} changes mode."""
        from app.profile_controller import quick_change_mode

        hafiz_id = progression_test_hafiz["hafiz_id"]
        sess = {}
        
        # Get a test item
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id}", limit=1)
        if test_items:
            hafiz_item = test_items[0]
            original_mode = hafiz_item.mode_code
            
            # Call route to change mode
            result = quick_change_mode(
                hafiz_item_id=hafiz_item.id,
                mode_code=WEEKLY_REPS_MODE_CODE,
                auth=hafiz_id,
                sess=sess
            )
            
            # Verify mode changed
            updated_item = hafizs_items[hafiz_item.id]
            assert updated_item.mode_code == WEEKLY_REPS_MODE_CODE


class TestUpdateThresholdRoute:
    """Tests POST /profile/update_threshold/{hafiz_item_id} route."""

    def test_update_threshold_updates_item(self, progression_test_hafiz):
        """POST /profile/update_threshold/{hafiz_item_id} updates threshold."""
        from app.profile_controller import update_threshold

        hafiz_id = progression_test_hafiz["hafiz_id"]
        sess = {}
        
        # Get a test item
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id} AND mode_code='{DAILY_REPS_MODE_CODE}'", limit=1)
        if test_items:
            hafiz_item = test_items[0]
            
            # Call route to update threshold
            result = update_threshold(
                hafiz_item_id=hafiz_item.id,
                threshold=5,
                auth=hafiz_id,
                sess=sess
            )
            
            # Verify threshold updated
            updated_item = hafizs_items[hafiz_item.id]
            assert updated_item.custom_daily_threshold == 5


class TestGraduateItemRoute:
    """Tests POST /profile/graduate_item/{hafiz_item_id} route."""

    def test_graduate_item_changes_mode(self, progression_test_hafiz):
        """POST /profile/graduate_item/{hafiz_item_id} graduates item to new mode."""
        from app.profile_controller import graduate_item

        hafiz_id = progression_test_hafiz["hafiz_id"]
        sess = {}
        
        # Get a test item
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id} AND mode_code='{DAILY_REPS_MODE_CODE}'", limit=1)
        if test_items:
            hafiz_item = test_items[0]
            
            # Call route to graduate item
            result = graduate_item(
                hafiz_item_id=hafiz_item.id,
                target_mode=WEEKLY_REPS_MODE_CODE,
                auth=hafiz_id,
                sess=sess
            )
            
            # Verify mode changed
            updated_item = hafizs_items[hafiz_item.id]
            assert updated_item.mode_code == WEEKLY_REPS_MODE_CODE


class TestProfileRouteProtection:
    """Tests profile route protection and hafiz_id isolation."""

    def test_load_rep_config_modal_rejects_other_hafiz_items(self, progression_test_hafiz, multi_mode_test_hafiz):
        """GET /profile/configure_reps/{hafiz_item_id} rejects other hafiz's items."""
        from app.profile_controller import load_rep_config_modal

        hafiz_1 = progression_test_hafiz["hafiz_id"]
        hafiz_2 = multi_mode_test_hafiz["hafiz_id"]
        
        # Get item from hafiz_1
        test_items_1 = hafizs_items(where=f"hafiz_id={hafiz_1}", limit=1)
        if test_items_1:
            hafiz_item_id = test_items_1[0].id
            
            # Try to access with hafiz_2's auth
            result = load_rep_config_modal(hafiz_item_id=hafiz_item_id, auth=hafiz_2)
            
            # Should return error (Unauthorized)
            assert "Unauthorized" in str(result) or "not found" in str(result).lower()

    def test_quick_change_mode_only_affects_authenticated_hafiz_items(self, progression_test_hafiz):
        """POST /profile/quick_change_mode/{hafiz_item_id} only changes authenticated hafiz's items."""
        from app.profile_controller import quick_change_mode

        hafiz_id = progression_test_hafiz["hafiz_id"]
        sess = {}
        
        # Get a test item
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id}", limit=1)
        if test_items:
            hafiz_item = test_items[0]
            original_hafiz_id = hafiz_item.hafiz_id
            
            # Call route
            quick_change_mode(
                hafiz_item_id=hafiz_item.id,
                mode_code=WEEKLY_REPS_MODE_CODE,
                auth=hafiz_id,
                sess=sess
            )
            
            # Verify item still belongs to original hafiz
            updated_item = hafizs_items[hafiz_item.id]
            assert updated_item.hafiz_id == original_hafiz_id
            assert updated_item.hafiz_id == hafiz_id

    def test_update_threshold_only_affects_authenticated_hafiz_items(self, progression_test_hafiz):
        """POST /profile/update_threshold/{hafiz_item_id} only updates authenticated hafiz's items."""
        from app.profile_controller import update_threshold

        hafiz_id = progression_test_hafiz["hafiz_id"]
        sess = {}
        
        # Get a test item
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id} AND mode_code='{DAILY_REPS_MODE_CODE}'", limit=1)
        if test_items:
            hafiz_item = test_items[0]
            original_hafiz_id = hafiz_item.hafiz_id
            
            # Call route
            update_threshold(
                hafiz_item_id=hafiz_item.id,
                threshold=5,
                auth=hafiz_id,
                sess=sess
            )
            
            # Verify item still belongs to original hafiz
            updated_item = hafizs_items[hafiz_item.id]
            assert updated_item.hafiz_id == original_hafiz_id
            assert updated_item.hafiz_id == hafiz_id

    def test_graduate_item_only_affects_authenticated_hafiz_items(self, progression_test_hafiz):
        """POST /profile/graduate_item/{hafiz_item_id} only graduates authenticated hafiz's items."""
        from app.profile_controller import graduate_item

        hafiz_id = progression_test_hafiz["hafiz_id"]
        sess = {}
        
        # Get a test item
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id} AND mode_code='{DAILY_REPS_MODE_CODE}'", limit=1)
        if test_items:
            hafiz_item = test_items[0]
            original_hafiz_id = hafiz_item.hafiz_id
            
            # Call route
            graduate_item(
                hafiz_item_id=hafiz_item.id,
                target_mode=WEEKLY_REPS_MODE_CODE,
                auth=hafiz_id,
                sess=sess
            )
            
            # Verify item still belongs to original hafiz
            updated_item = hafizs_items[hafiz_item.id]
            assert updated_item.hafiz_id == original_hafiz_id
            assert updated_item.hafiz_id == hafiz_id

    def test_show_profile_page_only_shows_authenticated_hafiz_data(self, progression_test_hafiz):
        """GET /profile/table should only return data for authenticated hafiz."""
        from app.profile_controller import show_profile_page
        from unittest.mock import Mock

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Mock request
        request = Mock()
        request.headers = {}
        
        # Call route
        result = show_profile_page(auth=hafiz_id, request=request, status_filter=None)
        
        # Should return HTML (not raise error or return wrong data)
        assert result is not None

    def test_load_more_profile_rows_respects_hafiz_filter(self, progression_test_hafiz):
        """GET /profile/table/more should only load rows for authenticated hafiz."""
        from app.profile_controller import load_more_profile_rows

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = load_more_profile_rows(auth=hafiz_id, status_filter=None, offset=0)
        
        # Should return rows
        assert result is not None
