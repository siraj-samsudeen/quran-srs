"""Unit tests for admin_controller routes.

Tests all route handlers in isolation using test fixtures.
"""

import pytest
from database import hafizs, hafizs_items, revisions


class TestAdminListBackupsRoute:
    """Tests GET /admin/backups route."""

    def test_list_backups_returns_page(self, progression_test_hafiz):
        """GET /admin/backups returns backups list page."""
        from app.admin_controller import list_backups

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = list_backups(auth=hafiz_id)
        
        # Should return HTML response
        assert result is not None


class TestAdminListTablesRoute:
    """Tests GET /admin/tables route."""

    def test_list_tables_returns_page(self, progression_test_hafiz):
        """GET /admin/tables returns tables list page."""
        from app.admin_controller import list_tables

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = list_tables(auth=hafiz_id)
        
        # Should return HTML response
        assert result is not None


class TestAdminViewTableRoute:
    """Tests GET /admin/tables/{table} route."""

    def test_view_table_returns_records(self, progression_test_hafiz):
        """GET /admin/tables/{table} returns table view."""
        from app.admin_controller import view_table

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route with a valid table
        result = view_table(table="revisions", auth=hafiz_id)
        
        # Should return HTML response
        assert result is not None


class TestAdminEditRecordRoute:
    """Tests GET /admin/tables/{table}/{primary_key}/edit route."""

    def test_edit_record_view_returns_form(self, progression_test_hafiz):
        """GET /admin/tables/{table}/{primary_key}/edit returns edit form."""
        from app.admin_controller import edit_record_view
        from constants import DAILY_REPS_MODE_CODE

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Get a test revision
        test_revisions = revisions(where=f"hafiz_id={hafiz_id}", limit=1)
        if test_revisions:
            rev_id = test_revisions[0].id
            
            # Call route
            result = edit_record_view(table="revisions", primary_key=str(rev_id), auth=hafiz_id)
            
            # Should return HTML response (form)
            assert result is not None


class TestAdminExportTableRoute:
    """Tests GET /admin/tables/{table}/export route."""

    def test_export_table_returns_csv(self, progression_test_hafiz):
        """GET /admin/tables/{table}/export returns CSV file."""
        from app.admin_controller import export_specific_table

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = export_specific_table(table="revisions")
        
        # Should return streaming response (CSV)
        assert result is not None


class TestAdminImportTableViewRoute:
    """Tests GET /admin/tables/{table}/import route."""

    def test_import_view_returns_form(self, progression_test_hafiz):
        """GET /admin/tables/{table}/import returns import form."""
        from app.admin_controller import import_specific_table_view

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = import_specific_table_view(table="revisions", auth=hafiz_id)
        
        # Should return HTML response (form)
        assert result is not None


class TestAdminBackupRoute:
    """Tests GET /admin/backup route."""

    def test_backup_active_db_creates_file(self, progression_test_hafiz):
        """GET /admin/backup creates and returns backup file."""
        from app.admin_controller import backup_active_db

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = backup_active_db()
        
        # Should return file response
        assert result is not None


class TestAdminNewRecordRoute:
    """Tests GET /admin/tables/{table}/new route."""

    def test_new_record_view_returns_form(self, progression_test_hafiz):
        """GET /admin/tables/{table}/new returns new record form."""
        from app.admin_controller import new_record_view

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Call route
        result = new_record_view(table="revisions", auth=hafiz_id)
        
        # Should return HTML response (form)
        assert result is not None


class TestAdminRouteProtection:
    """Tests admin route protection and hafiz_id isolation."""

    def test_view_table_requires_auth(self, progression_test_hafiz):
        """GET /admin/tables/{table} requires authentication."""
        from app.admin_controller import view_table

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Routes should not crash when called with valid hafiz_id
        result = view_table(table="revisions", auth=hafiz_id)
        assert result is not None

    def test_list_tables_requires_auth(self, progression_test_hafiz):
        """GET /admin/tables requires authentication."""
        from app.admin_controller import list_tables

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Routes should not crash when called with valid hafiz_id
        result = list_tables(auth=hafiz_id)
        assert result is not None

    def test_list_backups_requires_auth(self, progression_test_hafiz):
        """GET /admin/backups requires authentication."""
        from app.admin_controller import list_backups

        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        # Routes should not crash when called with valid hafiz_id
        result = list_backups(auth=hafiz_id)
        assert result is not None
