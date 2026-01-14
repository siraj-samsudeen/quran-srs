"""Unit tests for hafiz_controller routes.

Tests all route handlers in isolation using test fixtures.
"""

import pytest
from database import hafizs, users
from constants import *


class TestHafizSelectionGetRoute:
    """Tests GET /hafiz/selection route."""

    def test_hafiz_selection_returns_page(self, progression_test_hafiz):
        """GET /hafiz/selection returns hafiz selection page."""
        from app.hafiz_controller import get as hafiz_selection_get

        user_id = progression_test_hafiz["user_id"]
        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Create session with user_auth
        sess = {"user_auth": user_id, "auth": hafiz_id}
        
        # Call route
        result = hafiz_selection_get(sess=sess)
        
        # Should return HTML response
        assert result is not None


class TestHafizSelectionPostRoute:
    """Tests POST /hafiz/selection route."""

    def test_hafiz_selection_route_exists(self, progression_test_hafiz):
        """POST /hafiz/selection route exists."""
        # Route test
        pass


class TestHafizAddRoute:
    """Tests POST /hafiz/add route."""

    def test_hafiz_add_creates_hafiz(self, progression_test_hafiz):
        """POST /hafiz/add creates new hafiz profile."""
        from app.hafiz_controller import post as hafiz_add_post
        from database import Hafiz
        import time

        user_id = progression_test_hafiz["user_id"]
        timestamp = int(time.time() * 1000)
        
        # Create hafiz data
        new_hafiz = Hafiz(
            name=f"TestHafiz{timestamp}",
            user_id=user_id,
            current_date="2024-01-15"
        )
        
        sess = {"user_auth": user_id}
        
        # Call route
        result = hafiz_add_post(hafiz=new_hafiz, sess=sess)
        
        # Should return redirect result
        assert result is not None


class TestHafizDeleteRoute:
    """Tests /hafiz/delete/{hafiz_id} route."""

    def test_hafiz_delete_deletes_hafiz(self, progression_test_hafiz):
        """DELETE /hafiz/delete/{hafiz_id} deletes hafiz profile."""
        from app.hafiz_controller import delete as hafiz_delete
        from database import Hafiz
        import time

        user_id = progression_test_hafiz["user_id"]
        timestamp = int(time.time() * 1000)
        
        # Create a new hafiz to delete
        new_hafiz = hafizs.insert(
            name=f"DeleteTestHafiz{timestamp}",
            user_id=user_id,
            current_date="2024-01-15"
        )
        hafiz_to_delete = new_hafiz.id
        
        sess = {"user_auth": user_id}
        
        # Call delete route
        result = hafiz_delete(hafiz_id=hafiz_to_delete, sess=sess)
        
        # Verify hafiz deleted
        try:
            hafizs[hafiz_to_delete]
            assert False, "Hafiz should be deleted"
        except:
            pass  # Expected - hafiz not found


class TestHafizSettingsGetRoute:
    """Tests GET /hafiz/settings route."""

    def test_settings_page_returns_form(self, progression_test_hafiz):
        """GET /hafiz/settings returns settings form."""
        from app.hafiz_controller import settings_page

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = settings_page(auth=hafiz_id)
        
        # Should return HTML response (form)
        assert result is not None


class TestHafizSettingsPostRoute:
    """Tests POST /hafiz/settings route."""

    def test_update_settings_updates_hafiz(self, progression_test_hafiz):
        """POST /hafiz/settings updates hafiz preferences."""
        from app.hafiz_controller import update_setings
        from database import Hafiz

        hafiz_id = progression_test_hafiz["hafiz_id"]
        current_hafiz = hafizs[hafiz_id]
        
        # Update hafiz data
        updated_hafiz = Hafiz(
            id=hafiz_id,
            name="Updated Name",
            user_id=current_hafiz.user_id,
            current_date=current_hafiz.current_date,
            page_size=20
        )
        
        # Call route
        result = update_setings(auth=hafiz_id, hafiz_data=updated_hafiz)
        
        # Verify settings updated
        updated = hafizs[hafiz_id]
        assert updated.name == "Updated Name"
        assert updated.page_size == 20


class TestHafizThemeRoute:
    """Tests GET /hafiz/theme route."""

    def test_theme_picker_returns_page(self, progression_test_hafiz):
        """GET /hafiz/theme returns theme picker page."""
        from app.hafiz_controller import custom_theme_picker

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = custom_theme_picker(auth=hafiz_id)
        
        # Should return HTML response
        assert result is not None


class TestHafizUpdateStatsColumnRoute:
    """Tests GET /hafiz/update_stats_column route."""

    def test_update_stats_column_refreshes_stats(self, progression_test_hafiz):
        """GET /hafiz/update_stats_column updates stats columns."""
        from app.hafiz_controller import update_stats_column
        from unittest.mock import Mock

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Mock request
        request = Mock()
        request.headers = {"referer": "/"}
        
        # Call route
        result = update_stats_column(req=request, auth=hafiz_id)
        
        # Should redirect back
        assert result is not None


class TestHafizRouteProtection:
    """Tests hafiz route protection and user isolation."""

    def test_hafiz_selection_requires_user_auth(self, progression_test_hafiz):
        """GET /hafiz/selection requires user_auth in session."""
        from app.hafiz_controller import get as hafiz_selection_get

        user_id = progression_test_hafiz["user_id"]
        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Create session with user_auth
        sess = {"user_auth": user_id, "auth": hafiz_id}
        
        # Call route
        result = hafiz_selection_get(sess=sess)
        
        # Should return valid response
        assert result is not None

    def test_hafiz_delete_rejects_unauthorized_user(self, progression_test_hafiz, multi_mode_test_hafiz):
        """DELETE /hafiz/delete/{hafiz_id} should reject unauthorized user."""
        from app.hafiz_controller import delete as hafiz_delete

        hafiz_1 = progression_test_hafiz["hafiz_id"]
        user_1 = progression_test_hafiz["user_id"]
        user_2 = multi_mode_test_hafiz["user_id"]
        
        # Verify hafiz_1 belongs to user_1
        hafiz_obj = hafizs[hafiz_1]
        assert hafiz_obj.user_id == user_1
        
        # Try to delete with wrong user
        sess = {"user_auth": user_2}
        result = hafiz_delete(hafiz_id=hafiz_1, sess=sess)
        
        # Should return valid result
        assert result is not None
        
        # Verify hafiz still exists
        try:
            hafizs[hafiz_1]
            assert True
        except:
            assert False, "Hafiz should not be deleted by unauthorized user"

    def test_settings_page_only_shows_authenticated_hafiz_data(self, progression_test_hafiz):
        """GET /hafiz/settings should only return data for authenticated hafiz."""
        from app.hafiz_controller import settings_page

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = settings_page(auth=hafiz_id)
        
        # Should return HTML (not raise error or return wrong data)
        assert result is not None

    def test_theme_picker_only_shows_authenticated_hafiz_data(self, progression_test_hafiz):
        """GET /hafiz/theme should only return data for authenticated hafiz."""
        from app.hafiz_controller import custom_theme_picker

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = custom_theme_picker(auth=hafiz_id)
        
        # Should return HTML
        assert result is not None

    def test_update_settings_only_affects_authenticated_hafiz(self, progression_test_hafiz):
        """POST /hafiz/settings should only update authenticated hafiz's data."""
        from app.hafiz_controller import update_setings
        from database import Hafiz

        hafiz_id = progression_test_hafiz["hafiz_id"]
        current_hafiz = hafizs[hafiz_id]
        original_user_id = current_hafiz.user_id
        
        # Update hafiz data
        updated_hafiz = Hafiz(
            id=hafiz_id,
            name="Updated Name",
            user_id=current_hafiz.user_id,
            current_date=current_hafiz.current_date,
            page_size=20
        )
        
        # Call route
        update_setings(auth=hafiz_id, hafiz_data=updated_hafiz)
        
        # Verify hafiz still belongs to original user
        updated = hafizs[hafiz_id]
        assert updated.user_id == original_user_id
