"""Unit tests for profile bulk selection functionality.

Tests bulk_set_status route handler for marking items as memorized/not memorized.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock
from database import hafizs_items
from constants import (
    STATUS_NOT_MEMORIZED,
    STATUS_SOLID,
    FULL_CYCLE_MODE_CODE,
)


class TestBulkSetStatus:
    """Tests POST /profile/bulk/set_status route."""

    def test_bulk_set_status_marks_items_as_memorized(self, progression_test_hafiz):
        """bulk_set_status marks selected items as memorized (SOLID status)."""
        from app.profile_controller import bulk_set_status

        hafiz_id = progression_test_hafiz["hafiz_id"]
        sess = {}

        hafizs_items.xtra()
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id} AND memorized=0", limit=2)

        if len(test_items) < 2:
            pytest.skip("Not enough unmemorized items for test")

        item_ids = [str(item.id) for item in test_items]

        request = AsyncMock()
        request.form = AsyncMock(return_value=Mock(getlist=lambda x: item_ids))

        result = asyncio.run(
            bulk_set_status(
                req=request,
                auth=hafiz_id,
                sess=sess,
                status=STATUS_SOLID,
                status_filter=None,
            )
        )

        for item_id in item_ids:
            updated_item = hafizs_items[int(item_id)]
            assert updated_item.memorized == True
            assert updated_item.mode_code == FULL_CYCLE_MODE_CODE

        assert result is not None

    def test_bulk_set_status_marks_items_as_not_memorized(self, progression_test_hafiz):
        """bulk_set_status marks selected items as not memorized."""
        from app.profile_controller import bulk_set_status

        hafiz_id = progression_test_hafiz["hafiz_id"]
        sess = {}

        hafizs_items.xtra()
        test_items = hafizs_items(where=f"hafiz_id={hafiz_id} AND memorized=1", limit=1)

        if len(test_items) < 1:
            pytest.skip("Not enough memorized items for test")

        item_ids = [str(item.id) for item in test_items]

        request = AsyncMock()
        request.form = AsyncMock(return_value=Mock(getlist=lambda x: item_ids))

        result = asyncio.run(
            bulk_set_status(
                req=request,
                auth=hafiz_id,
                sess=sess,
                status=STATUS_NOT_MEMORIZED,
                status_filter=None,
            )
        )

        for item_id in item_ids:
            updated_item = hafizs_items[int(item_id)]
            assert updated_item.memorized == False
            assert updated_item.mode_code is None

        assert result is not None

    def test_bulk_set_status_with_empty_selection_shows_error(self, progression_test_hafiz):
        """bulk_set_status with no items selected sets error in session."""
        from app.profile_controller import bulk_set_status

        hafiz_id = progression_test_hafiz["hafiz_id"]
        sess = {}

        request = AsyncMock()
        request.form = AsyncMock(return_value=Mock(getlist=lambda x: []))

        result = asyncio.run(
            bulk_set_status(
                req=request,
                auth=hafiz_id,
                sess=sess,
                status=STATUS_SOLID,
                status_filter=None,
            )
        )

        assert "toasts" in sess
        assert any("error" in toast[1] for toast in sess["toasts"])
        assert result is not None

    def test_bulk_set_status_only_affects_authenticated_hafiz_items(
        self, progression_test_hafiz, multi_mode_test_hafiz
    ):
        """bulk_set_status only changes items belonging to authenticated hafiz."""
        from app.profile_controller import bulk_set_status

        hafiz_1 = progression_test_hafiz["hafiz_id"]
        hafiz_2 = multi_mode_test_hafiz["hafiz_id"]
        sess = {}

        hafizs_items.xtra()
        hafiz_2_items = hafizs_items(where=f"hafiz_id={hafiz_2}", limit=1)

        if not hafiz_2_items:
            pytest.skip("No items for hafiz_2")

        item_ids = [str(hafiz_2_items[0].id)]
        original_memorized = hafiz_2_items[0].memorized

        request = AsyncMock()
        request.form = AsyncMock(return_value=Mock(getlist=lambda x: item_ids))

        asyncio.run(
            bulk_set_status(
                req=request,
                auth=hafiz_1,
                sess=sess,
                status=STATUS_SOLID,
                status_filter=None,
            )
        )

        unchanged_item = hafizs_items[hafiz_2_items[0].id]
        assert unchanged_item.memorized == original_memorized
