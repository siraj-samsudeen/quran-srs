"""Integration tests for manual graduation feature.

Tests the manual graduation functionality in the profile mode management section.
Manual graduation allows users to advance pages through the rep mode chain
without waiting for the normal 7-review threshold.
"""

import time
import pytest
from constants import (
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
    NEW_MEMORIZATION_MODE_CODE,
    SRS_MODE_CODE,
    GRADUATABLE_MODES,
)
from app.fixed_reps import REP_MODES_CONFIG
from app.common_function import get_mode_icon, get_mode_name, can_graduate


class TestGraduatableModes:
    """Test GRADUATABLE_MODES constant configuration."""

    def test_graduatable_modes_includes_rep_modes(self):
        """GRADUATABLE_MODES includes all rep modes."""
        assert DAILY_REPS_MODE_CODE in GRADUATABLE_MODES
        assert WEEKLY_REPS_MODE_CODE in GRADUATABLE_MODES
        assert FORTNIGHTLY_REPS_MODE_CODE in GRADUATABLE_MODES
        assert MONTHLY_REPS_MODE_CODE in GRADUATABLE_MODES

    def test_graduatable_modes_excludes_non_rep_modes(self):
        """GRADUATABLE_MODES excludes FC, NM, SR modes."""
        assert FULL_CYCLE_MODE_CODE not in GRADUATABLE_MODES
        assert NEW_MEMORIZATION_MODE_CODE not in GRADUATABLE_MODES
        assert SRS_MODE_CODE not in GRADUATABLE_MODES

    def test_graduatable_modes_matches_rep_modes_config(self):
        """All modes in GRADUATABLE_MODES have REP_MODES_CONFIG entries."""
        for mode_code in GRADUATABLE_MODES:
            assert mode_code in REP_MODES_CONFIG


class TestHelperFunctions:
    """Test helper functions for mode management."""

    def test_get_mode_icon_returns_icons(self):
        """get_mode_icon returns emoji icons for all modes."""
        assert get_mode_icon(DAILY_REPS_MODE_CODE) == "☀️"
        assert get_mode_icon(WEEKLY_REPS_MODE_CODE) == "📅"
        assert get_mode_icon(FORTNIGHTLY_REPS_MODE_CODE) == "📆"
        assert get_mode_icon(MONTHLY_REPS_MODE_CODE) == "🗓️"
        assert get_mode_icon(FULL_CYCLE_MODE_CODE) == "🔄"
        assert get_mode_icon(SRS_MODE_CODE) == "🧠"
        assert get_mode_icon(NEW_MEMORIZATION_MODE_CODE) == "🆕"

    def test_get_mode_icon_unknown_mode(self):
        """get_mode_icon returns default icon for unknown modes."""
        assert get_mode_icon("UNKNOWN") == "📖"

    def test_can_graduate_rep_modes(self):
        """can_graduate returns True for rep modes."""
        assert can_graduate(DAILY_REPS_MODE_CODE) is True
        assert can_graduate(WEEKLY_REPS_MODE_CODE) is True
        assert can_graduate(FORTNIGHTLY_REPS_MODE_CODE) is True
        assert can_graduate(MONTHLY_REPS_MODE_CODE) is True

    def test_can_graduate_non_rep_modes(self):
        """can_graduate returns False for non-rep modes."""
        assert can_graduate(FULL_CYCLE_MODE_CODE) is False
        assert can_graduate(NEW_MEMORIZATION_MODE_CODE) is False
        assert can_graduate(SRS_MODE_CODE) is False


@pytest.fixture
def graduation_test_hafiz(client):
    """Create a test user and hafiz for manual graduation tests."""
    from app.users_model import create_user
    from database import users, hafizs, hafizs_items

    test_email = f"manual_grad_test_{int(time.time() * 1000)}@example.com"
    user_id = create_user(test_email, "password123", "Manual Graduation Test User")

    login_response = client.post(
        "/users/login",
        data={"email": test_email, "password": "password123"},
        follow_redirects=False,
    )
    client.cookies = login_response.cookies

    client.post(
        "/hafiz/add",
        data={"name": "Test Hafiz"},
        follow_redirects=False,
    )

    user_hafizs = hafizs(where=f"user_id={user_id}")
    hafiz_id = user_hafizs[0].id
    select_response = client.post(
        "/hafiz/selection",
        data={"current_hafiz_id": hafiz_id},
        follow_redirects=False,
    )
    client.cookies = select_response.cookies

    # Get all test items for this hafiz
    test_items = hafizs_items(where=f"hafiz_id={hafiz_id}")

    yield {
        "client": client,
        "user_id": user_id,
        "hafiz_id": hafiz_id,
        "email": test_email,
        "items": test_items,
    }

    # Cleanup
    users.delete(user_id)


class TestModeManagementPage:
    """Test the mode management page display."""

    def test_mode_management_page_loads(self, graduation_test_hafiz):
        """Mode management page loads successfully."""
        client = graduation_test_hafiz["client"]
        response = client.get("/profile/mode_management")
        assert response.status_code == 200
        assert "Mode Management" in response.text

    def test_mode_management_empty_state(self, graduation_test_hafiz):
        """Mode management shows empty state when no items in rep modes."""
        client = graduation_test_hafiz["client"]
        response = client.get("/profile/mode_management")
        assert response.status_code == 200
        # New hafiz has no items in rep modes (all start unmemorized)
        assert "No pages in rep modes" in response.text

    def test_mode_management_shows_mode_groups(self, graduation_test_hafiz):
        """Mode management shows groups for modes with items."""
        from database import hafizs_items

        client = graduation_test_hafiz["client"]
        test_items = graduation_test_hafiz["items"]
        hafiz_id = graduation_test_hafiz["hafiz_id"]

        # Set some items to Daily mode
        for item in test_items[:3]:
            hafizs_items.update({
                "mode_code": DAILY_REPS_MODE_CODE,
                "next_interval": 1,
                "next_review": "2024-01-15",
                "memorized": False,
            }, item.id)

        response = client.get("/profile/mode_management")
        assert response.status_code == 200
        assert "Daily Reps" in response.text
        assert "Graduate to" in response.text


class TestGraduationConfirmationModal:
    """Test the graduation confirmation modal."""

    def test_confirm_graduation_invalid_mode(self, graduation_test_hafiz):
        """Confirmation modal handles invalid mode codes."""
        client = graduation_test_hafiz["client"]
        response = client.get("/profile/mode_management/confirm/INVALID")
        assert response.status_code == 200
        assert "Invalid mode" in response.text

    def test_confirm_graduation_no_items(self, graduation_test_hafiz):
        """Confirmation modal handles mode with no items."""
        client = graduation_test_hafiz["client"]
        # Fresh hafiz has no items in Daily mode
        response = client.get(f"/profile/mode_management/confirm/{DAILY_REPS_MODE_CODE}")
        assert response.status_code == 200
        assert "No items to graduate" in response.text

    def test_confirm_graduation_shows_items(self, graduation_test_hafiz):
        """Confirmation modal shows items to be graduated."""
        from database import hafizs_items

        client = graduation_test_hafiz["client"]
        test_items = graduation_test_hafiz["items"]

        # Set item to Daily mode
        hafizs_items.update({
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_interval": 1,
            "next_review": "2024-01-15",
            "memorized": False,
        }, test_items[0].id)

        response = client.get(f"/profile/mode_management/confirm/{DAILY_REPS_MODE_CODE}")
        assert response.status_code == 200
        assert "Graduate" in response.text
        assert "Weekly" in response.text  # Next mode name


class TestManualGraduationBackend:
    """Test the backend graduation logic."""

    def test_graduate_daily_to_weekly(self, graduation_test_hafiz):
        """Manual graduation from Daily to Weekly sets correct values."""
        from database import hafizs, hafizs_items

        client = graduation_test_hafiz["client"]
        test_items = graduation_test_hafiz["items"]
        hafiz_id = graduation_test_hafiz["hafiz_id"]

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Set item to Daily mode
        hafizs_items.update({
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_interval": 1,
            "next_review": "2024-01-15",
            "memorized": False,
        }, test_items[0].id)

        # Perform graduation
        response = client.post(
            "/profile/mode_management/graduate",
            data={
                "mode_code": DAILY_REPS_MODE_CODE,
                "item_ids": str(test_items[0].id),
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Verify graduation
        updated_item = hafizs_items[test_items[0].id]
        assert updated_item.mode_code == WEEKLY_REPS_MODE_CODE
        assert updated_item.next_interval == 7
        assert updated_item.next_review == "2024-01-22"

    def test_graduate_weekly_to_fortnightly(self, graduation_test_hafiz):
        """Manual graduation from Weekly to Fortnightly sets correct values."""
        from database import hafizs, hafizs_items

        client = graduation_test_hafiz["client"]
        test_items = graduation_test_hafiz["items"]
        hafiz_id = graduation_test_hafiz["hafiz_id"]

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Set item to Weekly mode
        hafizs_items.update({
            "mode_code": WEEKLY_REPS_MODE_CODE,
            "next_interval": 7,
            "next_review": "2024-01-15",
            "memorized": False,
        }, test_items[1].id)

        # Perform graduation
        response = client.post(
            "/profile/mode_management/graduate",
            data={
                "mode_code": WEEKLY_REPS_MODE_CODE,
                "item_ids": str(test_items[1].id),
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Verify graduation
        updated_item = hafizs_items[test_items[1].id]
        assert updated_item.mode_code == FORTNIGHTLY_REPS_MODE_CODE
        assert updated_item.next_interval == 14
        assert updated_item.next_review == "2024-01-29"

    def test_graduate_fortnightly_to_monthly(self, graduation_test_hafiz):
        """Manual graduation from Fortnightly to Monthly sets correct values."""
        from database import hafizs, hafizs_items

        client = graduation_test_hafiz["client"]
        test_items = graduation_test_hafiz["items"]
        hafiz_id = graduation_test_hafiz["hafiz_id"]

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Set item to Fortnightly mode
        hafizs_items.update({
            "mode_code": FORTNIGHTLY_REPS_MODE_CODE,
            "next_interval": 14,
            "next_review": "2024-01-15",
            "memorized": False,
        }, test_items[2].id)

        # Perform graduation
        response = client.post(
            "/profile/mode_management/graduate",
            data={
                "mode_code": FORTNIGHTLY_REPS_MODE_CODE,
                "item_ids": str(test_items[2].id),
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Verify graduation
        updated_item = hafizs_items[test_items[2].id]
        assert updated_item.mode_code == MONTHLY_REPS_MODE_CODE
        assert updated_item.next_interval == 30
        assert updated_item.next_review == "2024-02-14"

    def test_graduate_monthly_to_full_cycle(self, graduation_test_hafiz):
        """Manual graduation from Monthly to Full Cycle clears scheduling fields."""
        from database import hafizs, hafizs_items

        client = graduation_test_hafiz["client"]
        test_items = graduation_test_hafiz["items"]
        hafiz_id = graduation_test_hafiz["hafiz_id"]

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Set item to Monthly mode
        hafizs_items.update({
            "mode_code": MONTHLY_REPS_MODE_CODE,
            "next_interval": 30,
            "next_review": "2024-01-15",
            "memorized": False,
        }, test_items[3].id)

        # Perform graduation
        response = client.post(
            "/profile/mode_management/graduate",
            data={
                "mode_code": MONTHLY_REPS_MODE_CODE,
                "item_ids": str(test_items[3].id),
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Verify graduation to Full Cycle
        updated_item = hafizs_items[test_items[3].id]
        assert updated_item.mode_code == FULL_CYCLE_MODE_CODE
        assert updated_item.next_interval is None
        assert updated_item.next_review is None
        assert updated_item.memorized == 1

    def test_graduate_no_items_selected(self, graduation_test_hafiz):
        """Graduation with no items selected shows error."""
        client = graduation_test_hafiz["client"]

        response = client.post(
            "/profile/mode_management/graduate",
            data={"mode_code": DAILY_REPS_MODE_CODE},
            follow_redirects=False,
        )
        # Should redirect back
        assert response.status_code == 303

    def test_graduate_invalid_mode(self, graduation_test_hafiz):
        """Graduation with invalid mode shows error."""
        client = graduation_test_hafiz["client"]

        response = client.post(
            "/profile/mode_management/graduate",
            data={
                "mode_code": "INVALID",
                "item_ids": "1",
            },
            follow_redirects=False,
        )
        # Should redirect back
        assert response.status_code == 303

    def test_graduate_bulk_items(self, graduation_test_hafiz):
        """Bulk graduation works for multiple items at once."""
        from database import hafizs, hafizs_items

        client = graduation_test_hafiz["client"]
        test_items = graduation_test_hafiz["items"]
        hafiz_id = graduation_test_hafiz["hafiz_id"]

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Set multiple items to Daily mode
        items_to_graduate = test_items[10:15]
        for item in items_to_graduate:
            hafizs_items.update({
                "mode_code": DAILY_REPS_MODE_CODE,
                "next_interval": 1,
                "next_review": "2024-01-15",
                "memorized": False,
            }, item.id)

        # Build form data with multiple item_ids values
        form_data = {"mode_code": DAILY_REPS_MODE_CODE}
        # Multiple values for same key - using dict with list value
        item_ids_list = [str(item.id) for item in items_to_graduate]

        # Perform bulk graduation - pass multiple item_ids as separate params
        response = client.post(
            "/profile/mode_management/graduate",
            data={"mode_code": DAILY_REPS_MODE_CODE, "item_ids": item_ids_list},
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Verify all items graduated
        for item in items_to_graduate:
            updated_item = hafizs_items[item.id]
            assert updated_item.mode_code == WEEKLY_REPS_MODE_CODE

    def test_graduate_selective_items(self, graduation_test_hafiz):
        """Selective graduation only graduates checked items."""
        from database import hafizs, hafizs_items

        client = graduation_test_hafiz["client"]
        test_items = graduation_test_hafiz["items"]
        hafiz_id = graduation_test_hafiz["hafiz_id"]

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Set multiple items to Daily mode
        items_to_graduate = test_items[20:22]
        items_to_keep = test_items[22:24]
        all_items = items_to_graduate + items_to_keep

        for item in all_items:
            hafizs_items.update({
                "mode_code": DAILY_REPS_MODE_CODE,
                "next_interval": 1,
                "next_review": "2024-01-15",
                "memorized": False,
            }, item.id)

        # Graduate only selected items
        item_ids_list = [str(item.id) for item in items_to_graduate]
        response = client.post(
            "/profile/mode_management/graduate",
            data={"mode_code": DAILY_REPS_MODE_CODE, "item_ids": item_ids_list},
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Verify only selected items graduated
        for item in items_to_graduate:
            updated_item = hafizs_items[item.id]
            assert updated_item.mode_code == WEEKLY_REPS_MODE_CODE

        # Verify unselected items stayed in Daily mode
        for item in items_to_keep:
            updated_item = hafizs_items[item.id]
            assert updated_item.mode_code == DAILY_REPS_MODE_CODE

    def test_graduate_wrong_hafiz_items_ignored(self, graduation_test_hafiz):
        """Graduation ignores items that don't belong to current hafiz."""
        from database import hafizs, hafizs_items

        client = graduation_test_hafiz["client"]
        test_items = graduation_test_hafiz["items"]
        hafiz_id = graduation_test_hafiz["hafiz_id"]

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Set item to Daily mode
        hafizs_items.update({
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_interval": 1,
            "next_review": "2024-01-15",
            "memorized": False,
        }, test_items[30].id)

        # Try to graduate with a non-existent item ID
        response = client.post(
            "/profile/mode_management/graduate",
            data={
                "mode_code": DAILY_REPS_MODE_CODE,
                "item_ids": "999999",  # Non-existent ID
            },
            follow_redirects=False,
        )
        # Should redirect back (no items graduated)
        assert response.status_code == 303

    def test_graduate_wrong_mode_items_ignored(self, graduation_test_hafiz):
        """Graduation ignores items not in the specified mode."""
        from database import hafizs, hafizs_items

        client = graduation_test_hafiz["client"]
        test_items = graduation_test_hafiz["items"]
        hafiz_id = graduation_test_hafiz["hafiz_id"]

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Set item to Weekly mode (not Daily)
        hafizs_items.update({
            "mode_code": WEEKLY_REPS_MODE_CODE,
            "next_interval": 7,
            "next_review": "2024-01-15",
            "memorized": False,
        }, test_items[31].id)

        # Try to graduate as if it were Daily mode
        response = client.post(
            "/profile/mode_management/graduate",
            data={
                "mode_code": DAILY_REPS_MODE_CODE,
                "item_ids": str(test_items[31].id),
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Item should still be in Weekly mode (not changed)
        updated_item = hafizs_items[test_items[31].id]
        assert updated_item.mode_code == WEEKLY_REPS_MODE_CODE
