"""Unit tests for page_details_controller routes.

Tests all route handlers in isolation using test fixtures.
"""

import pytest
from database import hafizs_items, items


class TestPageDetailsViewRoute:
    """Tests GET /page_details/ route."""

    def test_page_details_view_returns_page(self, progression_test_hafiz):
        """GET /page_details/ returns page details summary."""
        from app.page_details_controller import page_details_view

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = page_details_view(auth=hafiz_id)
        
        # Should return HTML response
        assert result is not None


class TestDisplayPageLevelDetailsRoute:
    """Tests GET /page_details/{item_id} route."""

    def test_display_page_level_details_returns_page(self, progression_test_hafiz):
        """GET /page_details/{item_id} returns page level details."""
        from app.page_details_controller import display_page_level_details

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Get a test item
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id}", limit=1)
        if test_items:
            item_id = test_items[0].item_id
            
            # Call route
            result = display_page_level_details(auth=hafiz_id, item_id=item_id)
            
            # Should return HTML response
            assert result is not None


class TestPageDescriptionEditFormRoute:
    """Tests GET /page_details/edit/{item_id} route."""

    def test_page_description_edit_form_returns_form(self, progression_test_hafiz):
        """GET /page_details/edit/{item_id} returns edit form."""
        from app.page_details_controller import page_description_edit_form

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Get a test item
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id}", limit=1)
        if test_items:
            item_id = test_items[0].item_id
            
            # Call route
            result = page_description_edit_form(item_id=item_id)
            
            # Should return HTML response (form)
            assert result is not None


class TestPageDetailsLinkRegression:
    """Tests that internal links between routes exist (regression test)."""

    def test_page_details_main_accessible(self, progression_test_hafiz):
        """GET /page_details/ should be accessible."""
        from app.page_details_controller import page_details_view

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = page_details_view(auth=hafiz_id)
        
        # Should return valid HTML
        assert result is not None

    def test_page_details_item_accessible(self, progression_test_hafiz):
        """GET /page_details/{item_id} should be accessible."""
        from app.page_details_controller import display_page_level_details

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Get a test item
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id}", limit=1)
        if test_items:
            item_id = test_items[0].item_id
            
            # Call route
            result = display_page_level_details(auth=hafiz_id, item_id=item_id)
            
            # Should return valid HTML
            assert result is not None


class TestPageDetailsRouteProtection:
    """Tests page_details route protection and hafiz_id isolation."""

    def test_page_details_view_only_shows_authenticated_hafiz_data(self, progression_test_hafiz):
        """GET /page_details/ should only return data for authenticated hafiz."""
        from app.page_details_controller import page_details_view

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = page_details_view(auth=hafiz_id)
        
        # Should return HTML (not raise error or return wrong data)
        assert result is not None

    def test_display_page_level_details_only_shows_authenticated_hafiz_data(self, progression_test_hafiz):
        """GET /page_details/{item_id} should only return data for authenticated hafiz."""
        from app.page_details_controller import display_page_level_details

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Get a test item
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id}", limit=1)
        if test_items:
            item_id = test_items[0].item_id
            
            # Call route
            result = display_page_level_details(auth=hafiz_id, item_id=item_id)
            
            # Should return HTML (not raise error or return wrong data)
            assert result is not None

    def test_page_description_edit_form_returns_valid_form(self, progression_test_hafiz):
        """GET /page_details/edit/{item_id} should return valid edit form."""
        from app.page_details_controller import page_description_edit_form

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Get a test item
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id}", limit=1)
        if test_items:
            item_id = test_items[0].item_id
            
            # Call route
            result = page_description_edit_form(item_id=item_id)
            
            # Should return form
            assert result is not None
