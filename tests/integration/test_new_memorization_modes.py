"""Integration tests for New Memorization tab on home page.

Tests verify that:
1. Toggle route marks/unmarks items as memorized for today
2. Bulk mark route marks multiple items at once
3. Close Date graduates NM items to Daily Reps
"""

import time
import pytest
from constants import (
    DAILY_REPS_MODE_CODE,
    NEW_MEMORIZATION_MODE_CODE,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def memorization_test_hafiz(client):
    """Create a test user and hafiz for memorization tests.

    Returns a dict with user_id, hafiz_id, and list of unmemorized item_ids.
    """
    from app.users_model import create_user
    from database import users, hafizs, hafizs_items

    test_email = f"nm_tab_test_{int(time.time() * 1000)}@example.com"
    user_id = create_user(test_email, "password123", "NM Tab Test User")

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

    # Get unmemorized items
    unmemorized = hafizs_items(where=f"hafiz_id={hafiz_id} AND memorized=0", limit=20)
    item_ids = [item.item_id for item in unmemorized]

    yield {
        "client": client,
        "user_id": user_id,
        "hafiz_id": hafiz_id,
        "email": test_email,
        "item_ids": item_ids,
    }

    users.delete(user_id)


# ============================================================================
# Test Class: NM Tab Toggle Route
# ============================================================================


class TestNMTabToggle:
    """Test the toggle route for marking items as memorized."""

    def test_toggle_marks_item_as_memorized(self, memorization_test_hafiz):
        """Toggle creates NM revision when item is not yet memorized today."""
        from database import hafizs, revisions

        client = memorization_test_hafiz["client"]
        hafiz_id = memorization_test_hafiz["hafiz_id"]
        item_id = memorization_test_hafiz["item_ids"][0]
        current_date = "2024-01-15"

        hafizs.update({"current_date": current_date}, hafiz_id)

        response = client.post(
            f"/new_memorization/toggle/{item_id}",
            data={"date": current_date},
            follow_redirects=False,
        )

        assert response.status_code == 200

        # Verify revision was created
        nm_revisions = revisions(
            where=f"item_id={item_id} AND mode_code='{NEW_MEMORIZATION_MODE_CODE}' AND revision_date='{current_date}' AND hafiz_id={hafiz_id}"
        )
        assert len(nm_revisions) == 1
        assert nm_revisions[0].rating == 1

    def test_toggle_unmarks_item(self, memorization_test_hafiz):
        """Toggle deletes NM revision when item already has one for today."""
        from database import hafizs, revisions

        client = memorization_test_hafiz["client"]
        hafiz_id = memorization_test_hafiz["hafiz_id"]
        item_id = memorization_test_hafiz["item_ids"][1]
        current_date = "2024-01-15"

        hafizs.update({"current_date": current_date}, hafiz_id)

        # First toggle - mark as memorized
        client.post(
            f"/new_memorization/toggle/{item_id}",
            data={"date": current_date},
            follow_redirects=False,
        )

        # Verify revision exists
        nm_revisions = revisions(
            where=f"item_id={item_id} AND mode_code='{NEW_MEMORIZATION_MODE_CODE}' AND revision_date='{current_date}' AND hafiz_id={hafiz_id}"
        )
        assert len(nm_revisions) == 1

        # Second toggle - unmark
        response = client.post(
            f"/new_memorization/toggle/{item_id}",
            data={"date": current_date},
            follow_redirects=False,
        )

        assert response.status_code == 200

        # Verify revision was deleted
        nm_revisions = revisions(
            where=f"item_id={item_id} AND mode_code='{NEW_MEMORIZATION_MODE_CODE}' AND revision_date='{current_date}' AND hafiz_id={hafiz_id}"
        )
        assert len(nm_revisions) == 0


# ============================================================================
# Test Class: NM Tab Bulk Mark Route
# ============================================================================


class TestNMTabBulkMark:
    """Test the bulk mark route for marking multiple items as memorized."""

    def test_bulk_mark_creates_revisions(self, memorization_test_hafiz):
        """Bulk mark creates NM revisions for all specified items."""
        from database import hafizs, revisions

        client = memorization_test_hafiz["client"]
        hafiz_id = memorization_test_hafiz["hafiz_id"]
        item_ids = memorization_test_hafiz["item_ids"][2:5]  # 3 items
        current_date = "2024-01-15"

        hafizs.update({"current_date": current_date}, hafiz_id)

        response = client.post(
            "/new_memorization/bulk_mark",
            data={"item_ids": [str(i) for i in item_ids], "date": current_date},
            follow_redirects=False,
        )

        assert response.status_code == 200

        # Verify all revisions were created
        for item_id in item_ids:
            nm_revisions = revisions(
                where=f"item_id={item_id} AND mode_code='{NEW_MEMORIZATION_MODE_CODE}' AND revision_date='{current_date}' AND hafiz_id={hafiz_id}"
            )
            assert len(nm_revisions) == 1

    def test_bulk_mark_skips_existing_revisions(self, memorization_test_hafiz):
        """Bulk mark doesn't create duplicate revisions for already marked items."""
        from database import hafizs, revisions

        client = memorization_test_hafiz["client"]
        hafiz_id = memorization_test_hafiz["hafiz_id"]
        item_ids = memorization_test_hafiz["item_ids"][5:7]  # 2 items
        current_date = "2024-01-15"

        hafizs.update({"current_date": current_date}, hafiz_id)

        # First mark item[0] individually
        client.post(
            f"/new_memorization/toggle/{item_ids[0]}",
            data={"date": current_date},
            follow_redirects=False,
        )

        # Bulk mark both items
        client.post(
            "/new_memorization/bulk_mark",
            data={"item_ids": [str(i) for i in item_ids], "date": current_date},
            follow_redirects=False,
        )

        # Verify no duplicate for item[0]
        nm_revisions = revisions(
            where=f"item_id={item_ids[0]} AND mode_code='{NEW_MEMORIZATION_MODE_CODE}' AND revision_date='{current_date}' AND hafiz_id={hafiz_id}"
        )
        assert len(nm_revisions) == 1


# ============================================================================
# Test Class: Close Date Processing for NM Items
# ============================================================================


class TestCloseDateNMGraduation:
    """Test Close Date graduates NM items to Daily Reps."""

    def test_close_date_graduates_nm_to_daily(self, memorization_test_hafiz):
        """Close Date graduates NM item to Daily Reps mode."""
        from database import hafizs, hafizs_items, revisions

        client = memorization_test_hafiz["client"]
        hafiz_id = memorization_test_hafiz["hafiz_id"]
        item_id = memorization_test_hafiz["item_ids"][8]
        current_date = "2024-01-15"

        # Set xtra filter
        revisions.xtra(hafiz_id=hafiz_id)
        hafizs_items.xtra(hafiz_id=hafiz_id)

        hafizs.update({"current_date": current_date}, hafiz_id)

        # Mark item as memorized via toggle
        client.post(
            f"/new_memorization/toggle/{item_id}",
            data={"date": current_date},
            follow_redirects=False,
        )

        # Call Close Date
        response = client.post("/close_date", follow_redirects=False)
        assert response.status_code in (302, 303)

        # Verify graduation to Daily Reps
        updated_item = hafizs_items(where=f"item_id={item_id}")[0]
        assert updated_item.mode_code == DAILY_REPS_MODE_CODE
        assert updated_item.memorized == 1
        assert updated_item.next_interval == 1
        assert updated_item.next_review == "2024-01-16"  # current_date + 1 day interval

        revisions.xtra()
        hafizs_items.xtra()

    def test_close_date_processes_multiple_nm_items(self, memorization_test_hafiz):
        """Close Date graduates multiple NM items in a single call."""
        from database import hafizs, hafizs_items, revisions

        client = memorization_test_hafiz["client"]
        hafiz_id = memorization_test_hafiz["hafiz_id"]
        item_ids = memorization_test_hafiz["item_ids"][10:13]  # 3 items
        current_date = "2024-01-15"

        revisions.xtra(hafiz_id=hafiz_id)
        hafizs_items.xtra(hafiz_id=hafiz_id)

        hafizs.update({"current_date": current_date}, hafiz_id)

        # Bulk mark items
        client.post(
            "/new_memorization/bulk_mark",
            data={"item_ids": [str(i) for i in item_ids], "date": current_date},
            follow_redirects=False,
        )

        # Call Close Date
        response = client.post("/close_date", follow_redirects=False)
        assert response.status_code in (302, 303)

        # Verify all items graduated to Daily Reps
        for item_id in item_ids:
            updated_item = hafizs_items(where=f"item_id={item_id}")[0]
            assert updated_item.mode_code == DAILY_REPS_MODE_CODE
            assert updated_item.memorized == 1

        revisions.xtra()
        hafizs_items.xtra()
