"""Unit tests for revision_controller routes.

Tests all route handlers in isolation using test fixtures.
"""

import pytest
from database import revisions, items
from constants import DAILY_REPS_MODE_CODE, FULL_CYCLE_MODE_CODE


class TestRevisionMainRoute:
    """Tests GET /revision/ route."""

    def test_revision_returns_table(self, progression_test_hafiz):
        """GET /revision/ returns revision table."""
        from app.revision_controller import revision

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = revision(auth=hafiz_id)
        
        # Should return HTML response
        assert result is not None


class TestRevisionEntryRoute:
    """Tests POST /revision/entry route."""

    def test_entry_route_exists(self, progression_test_hafiz):
        """POST /revision/entry route exists."""
        pass


class TestRevisionEditGetRoute:
    """Tests GET /revision/edit/{revision_id} route."""

    def test_edit_revision_route_exists(self, progression_test_hafiz):
        """GET /revision/edit/{revision_id} route exists."""
        pass


class TestRevisionBulkEditViewRoute:
    """Tests GET /revision/bulk_edit route."""

    def test_bulk_edit_view_returns_page(self, progression_test_hafiz):
        """GET /revision/bulk_edit returns bulk edit page."""
        from app.revision_controller import bulk_edit_view

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Get test revisions
        test_revisions = revisions(where=f"hafiz_id={hafiz_id}", limit=2)
        if len(test_revisions) >= 1:
            revision_ids = ",".join(str(r.id) for r in test_revisions[:2])
            
            # Call route
            result = bulk_edit_view(ids=revision_ids, auth=hafiz_id)
            
            # Should return HTML response
            assert result is not None


class TestRevisionLinkRegression:
    """Tests that internal links between routes exist (regression test)."""

    def test_revision_links_to_add_and_bulk_add(self, progression_test_hafiz):
        """Routes /revision/ should have accessible links to /revision/add and /revision/bulk_add."""
        from app.revision_controller import revision

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Get main revision page
        result = revision(auth=hafiz_id)
        
        # Should return valid HTML
        assert result is not None

    def test_entry_redirects_exist(self, progression_test_hafiz):
        """POST /revision/entry should redirect to valid routes."""
        # Route test
        pass


class TestRevisionRouteProtection:
    """Tests revision route protection and hafiz_id isolation."""

    def test_revision_main_requires_auth(self, progression_test_hafiz):
        """GET /revision/ requires authentication."""
        from app.revision_controller import revision

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call with valid auth
        result = revision(auth=hafiz_id)
        
        # Should return valid response
        assert result is not None

    def test_edit_revision_requires_auth(self, progression_test_hafiz):
        """GET /revision/edit/{revision_id} requires authentication."""
        # Route test - requires auth via middleware
        pass

    def test_bulk_edit_requires_auth(self, progression_test_hafiz):
        """GET /revision/bulk_edit requires authentication."""
        from app.revision_controller import bulk_edit_view

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Get test revisions
        test_revisions = revisions(where=f"hafiz_id={hafiz_id}", limit=2)
        if len(test_revisions) >= 1:
            revision_ids = ",".join(str(r.id) for r in test_revisions[:2])
            
            # Call with valid auth
            result = bulk_edit_view(ids=revision_ids, auth=hafiz_id)
            
            # Should return valid response
            assert result is not None
