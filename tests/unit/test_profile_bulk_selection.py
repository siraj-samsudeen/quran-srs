"""Unit tests for profile bulk selection functionality.

Tests bulk_set_status route handler for marking items as memorized/not memorized.
Tests tab filter counts and filtering by memorized status.
Tests Juz grouping functionality.
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
from app.profile_model import get_tab_counts, get_profile_data


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


class TestTabFilter:
    """Tests for tab filter functionality."""

    def test_get_tab_counts_returns_all_memorized_unmemorized(self, progression_test_hafiz):
        """get_tab_counts returns dict with all, memorized, unmemorized page counts."""
        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        counts = get_tab_counts(hafiz_id)
        
        assert "all" in counts
        assert "memorized" in counts
        assert "unmemorized" in counts
        # All should equal memorized + unmemorized
        all_count = float(counts["all"]) if counts["all"] else 0
        mem_count = float(counts["memorized"]) if counts["memorized"] else 0
        unmem_count = float(counts["unmemorized"]) if counts["unmemorized"] else 0
        assert all_count == mem_count + unmem_count

    def test_get_profile_data_filters_by_memorized(self, progression_test_hafiz):
        """get_profile_data with status_filter='memorized' returns only memorized items."""
        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        rows = get_profile_data(hafiz_id, status_filter="memorized")
        
        for row in rows:
            assert row["memorized"] == 1

    def test_get_profile_data_filters_by_unmemorized(self, progression_test_hafiz):
        """get_profile_data with status_filter='unmemorized' returns only unmemorized items."""
        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        rows = get_profile_data(hafiz_id, status_filter="unmemorized")
        
        for row in rows:
            assert row["memorized"] == 0 or row["memorized"] is None


class TestJuzGrouping:
    """Tests for Juz grouping functionality."""
    
    def test_get_profile_data_ordered_by_juz_number(self, progression_test_hafiz):
        """get_profile_data returns rows ordered by juz_number then page_number."""
        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        rows = get_profile_data(hafiz_id)
        
        if len(rows) < 2:
            pytest.skip("Not enough rows for ordering test")
        
        # Check that juz_number is non-decreasing
        for i in range(len(rows) - 1):
            curr_juz = rows[i]["juz_number"]
            next_juz = rows[i + 1]["juz_number"]
            
            if curr_juz == next_juz:
                # Same Juz, check page_number is non-decreasing
                assert rows[i]["page_number"] <= rows[i + 1]["page_number"], \
                    f"Pages not ordered within Juz {curr_juz}: {rows[i]['page_number']} > {rows[i + 1]['page_number']}"
            else:
                # Different Juz, juz should be non-decreasing
                assert curr_juz <= next_juz, \
                    f"Juz not ordered: {curr_juz} > {next_juz}"
    
    def test_juz_header_component_renders(self):
        """JuzHeader component renders with checkbox and label."""
        from app.components.tables import JuzHeader
        
        header = JuzHeader(1, colspan=6)
        
        # Verify it's a Tr (table row)
        assert hasattr(header, 'tag')
        assert header.tag == 'tr'
        
        # Verify it has data-juz attribute
        assert 'data-juz' in header.attrs
        assert header.attrs['data-juz'] == '1'
        
        # Verify it has juz-header class
        assert 'juz-header' in header.attrs.get('class', '')
        
        # Verify children (checkbox and label cell)
        assert len(header.children) == 2
        
        # First child should be a checkbox cell
        checkbox_cell = header.children[0]
        assert hasattr(checkbox_cell, 'tag')
        assert checkbox_cell.tag == 'td'


class TestSurahGrouping:
    """Tests for Surah grouping functionality."""
    
    def test_surah_header_component_renders(self):
        """SurahHeader component renders with checkbox and label."""
        from app.components.tables import SurahHeader
        
        header = SurahHeader(2, 1, colspan=6)
        
        # Verify it's a Tr (table row)
        assert hasattr(header, 'tag')
        assert header.tag == 'tr'
        
        # Verify it has data-juz and data-surah attributes
        assert 'data-juz' in header.attrs
        assert header.attrs['data-juz'] == '1'
        assert 'data-surah' in header.attrs
        assert header.attrs['data-surah'] == '2'
        
        # Verify it has surah-header class
        assert 'surah-header' in header.attrs.get('class', '')
        
        # Verify children (checkbox and label cell)
        assert len(header.children) == 2
        
        # First child should be a checkbox cell
        checkbox_cell = header.children[0]
        assert hasattr(checkbox_cell, 'tag')
        assert checkbox_cell.tag == 'td'
    
    def test_surah_spanning_multiple_juz(self, progression_test_hafiz):
        """get_profile_data correctly returns Surah 2 (Al-Baqarah) spanning multiple Juz."""
        hafiz_id = progression_test_hafiz["hafiz_id"]
        
        rows = get_profile_data(hafiz_id)
        
        # Find all rows for Surah 2 (Baqarah)
        surah_2_rows = [r for r in rows if r["surah_id"] == 2]
        
        if len(surah_2_rows) < 2:
            pytest.skip("Not enough rows for Surah 2 spanning test")
        
        # Collect unique Juz numbers for Surah 2
        juz_numbers = set(r["juz_number"] for r in surah_2_rows)
        
        # Surah 2 should span multiple Juz (typically Juz 1, 2, 3)
        assert len(juz_numbers) >= 2, f"Surah 2 should span multiple Juz, but only found in: {juz_numbers}"
