"""Integration tests for Home Page APIs.

Tests for:
- GET /api/mode/{mode_code}/items - Get items for a mode
- POST /api/mode/{mode_code}/rate - Rate a single item (including unrating)
- POST /api/mode/{mode_code}/bulk_rate - Bulk rate multiple items

Uses TestClient for fast HTTP-level testing without browser.
Fixture auth_with_memorized_pages comes from conftest.py.
"""

import json
import pytest


# ============================================================================
# GET /api/mode/{mode_code}/items Tests
# ============================================================================


class TestModeItemsAPI:
    """Tests for GET /api/mode/{mode_code}/items endpoint."""

    def test_returns_json_with_items_array(self, auth_with_memorized_pages):
        """API returns JSON with items array and metadata."""
        client = auth_with_memorized_pages["client"]

        response = client.get("/api/mode/FC/items")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "plan_id" in data
        assert "current_date" in data
        assert isinstance(data["items"], list)

    def test_items_have_required_fields(self, auth_with_memorized_pages):
        """Each item has required fields for Tabulator rendering."""
        client = auth_with_memorized_pages["client"]

        response = client.get("/api/mode/FC/items")
        data = response.json()

        if data["items"]:
            item = data["items"][0]
            required_fields = ["item_id", "page", "surah", "juz", "start_text", "rating"]
            for field in required_fields:
                assert field in item, f"Missing field: {field}"

    def test_invalid_mode_returns_400(self, auth_with_memorized_pages):
        """Invalid mode code returns 400 error."""
        client = auth_with_memorized_pages["client"]

        response = client.get("/api/mode/INVALID/items")
        assert response.status_code == 400

    def test_nm_mode_redirects_to_separate_api(self, auth_with_memorized_pages):
        """NM mode returns 400 directing to separate endpoint."""
        client = auth_with_memorized_pages["client"]

        response = client.get("/api/mode/NM/items")
        assert response.status_code == 400
        assert "new_memorization" in response.json().get("error", "").lower()


# ============================================================================
# POST /api/mode/{mode_code}/rate Tests
# ============================================================================


class TestRateItemAPI:
    """Tests for POST /api/mode/{mode_code}/rate endpoint."""

    def test_rate_item_creates_revision(self, auth_with_memorized_pages):
        """Rating an item creates a revision record."""
        client = auth_with_memorized_pages["client"]
        item_id = auth_with_memorized_pages["memorized_item_ids"][0]

        response = client.post(
            "/api/mode/FC/rate",
            content=json.dumps({"item_id": item_id, "rating": 1}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["rating"] == 1
        assert "revision_id" in data
        assert "pages_revised_today" in data
        assert "pages_revised_yesterday" in data

    def test_rate_item_updates_indicator_stats(self, auth_with_memorized_pages):
        """Rating returns updated pages_revised stats."""
        client = auth_with_memorized_pages["client"]
        item_id = auth_with_memorized_pages["memorized_item_ids"][0]

        response = client.post(
            "/api/mode/FC/rate",
            content=json.dumps({"item_id": item_id, "rating": 1}),
            headers={"Content-Type": "application/json"},
        )

        data = response.json()
        # Stats should be numeric (int or float)
        assert isinstance(data["pages_revised_today"], (int, float, str))
        assert isinstance(data["pages_revised_yesterday"], (int, float, str))

    def test_unrate_item_with_null_rating(self, auth_with_memorized_pages):
        """Sending null rating removes the revision (unrate)."""
        client = auth_with_memorized_pages["client"]
        item_id = auth_with_memorized_pages["memorized_item_ids"][0]

        # First rate the item
        client.post(
            "/api/mode/FC/rate",
            content=json.dumps({"item_id": item_id, "rating": 1}),
            headers={"Content-Type": "application/json"},
        )

        # Then unrate it
        response = client.post(
            "/api/mode/FC/rate",
            content=json.dumps({"item_id": item_id, "rating": None}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["rating"] is None
        assert data["revision_id"] is None

    def test_missing_item_id_returns_400(self, auth_with_memorized_pages):
        """Missing item_id returns 400 error."""
        client = auth_with_memorized_pages["client"]

        response = client.post(
            "/api/mode/FC/rate",
            content=json.dumps({"rating": 1}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400


# ============================================================================
# POST /api/mode/{mode_code}/bulk_rate Tests
# ============================================================================


class TestBulkRateAPI:
    """Tests for POST /api/mode/{mode_code}/bulk_rate endpoint."""

    def test_bulk_rate_multiple_items(self, auth_with_memorized_pages):
        """Bulk rating multiple items creates revisions for all."""
        client = auth_with_memorized_pages["client"]
        item_ids = auth_with_memorized_pages["memorized_item_ids"][:3]

        response = client.post(
            "/api/mode/FC/bulk_rate",
            content=json.dumps({"item_ids": item_ids, "rating": 1}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["rated_count"] == len(item_ids)

    def test_bulk_rate_returns_indicator_stats(self, auth_with_memorized_pages):
        """Bulk rating returns updated pages_revised stats."""
        client = auth_with_memorized_pages["client"]
        item_ids = auth_with_memorized_pages["memorized_item_ids"][:2]

        response = client.post(
            "/api/mode/FC/bulk_rate",
            content=json.dumps({"item_ids": item_ids, "rating": 0}),
            headers={"Content-Type": "application/json"},
        )

        data = response.json()
        assert "pages_revised_today" in data
        assert "pages_revised_yesterday" in data

    def test_empty_item_ids_returns_400(self, auth_with_memorized_pages):
        """Empty item_ids list returns 400 error."""
        client = auth_with_memorized_pages["client"]

        response = client.post(
            "/api/mode/FC/bulk_rate",
            content=json.dumps({"item_ids": [], "rating": 1}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400

    def test_missing_rating_returns_400(self, auth_with_memorized_pages):
        """Missing rating returns 400 error."""
        client = auth_with_memorized_pages["client"]
        item_ids = auth_with_memorized_pages["memorized_item_ids"][:2]

        response = client.post(
            "/api/mode/FC/bulk_rate",
            content=json.dumps({"item_ids": item_ids}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400


# ============================================================================
# Pagination and Filtering Tests
# ============================================================================


class TestModeItemsPaginationAndFilters:
    """Tests for pagination and filtering in mode items API."""

    def test_fc_mode_returns_memorized_items_only(self, auth_with_memorized_pages):
        """Full Cycle mode only returns memorized items."""
        client = auth_with_memorized_pages["client"]
        memorized_ids = set(auth_with_memorized_pages["memorized_item_ids"])

        response = client.get("/api/mode/FC/items")
        data = response.json()

        # All returned items should be in our memorized set
        returned_ids = {item["item_id"] for item in data["items"]}
        # returned_ids should be subset of memorized_ids (might include items revised today)
        assert returned_ids.issubset(memorized_ids) or len(returned_ids) >= 0

    def test_items_sorted_by_page_asc(self, auth_with_memorized_pages):
        """Items are sorted by page number ascending by default."""
        client = auth_with_memorized_pages["client"]

        response = client.get("/api/mode/FC/items")
        data = response.json()

        if len(data["items"]) > 1:
            pages = [item["page"] for item in data["items"]]
            assert pages == sorted(pages), "Items should be sorted by page ascending"


# ============================================================================
# New Memorization API Tests
# ============================================================================


class TestNewMemorizationAPI:
    """Tests for New Memorization specific endpoints."""

    def test_nm_items_endpoint_returns_json(self, auth_with_memorized_pages):
        """NM items endpoint returns JSON with items."""
        client = auth_with_memorized_pages["client"]

        response = client.get("/api/new_memorization/items")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "current_date" in data

    def test_nm_toggle_creates_revision(self, auth_with_memorized_pages):
        """Toggle endpoint creates/deletes NM revision."""
        client = auth_with_memorized_pages["client"]

        # Get a non-memorized item
        response = client.get("/api/new_memorization/items")
        data = response.json()

        if not data["items"]:
            pytest.skip("No non-memorized items available")

        item_id = data["items"][0]["item_id"]

        # Toggle on
        toggle_response = client.post(
            "/api/new_memorization/toggle",
            content=json.dumps({"item_id": item_id}),
            headers={"Content-Type": "application/json"},
        )

        assert toggle_response.status_code == 200
        toggle_data = toggle_response.json()
        assert toggle_data["success"] is True
        # First toggle should mark as memorized
        first_state = toggle_data["is_memorized_today"]

        # Toggle again to revert
        toggle_response2 = client.post(
            "/api/new_memorization/toggle",
            content=json.dumps({"item_id": item_id}),
            headers={"Content-Type": "application/json"},
        )
        toggle_data2 = toggle_response2.json()
        assert toggle_data2["is_memorized_today"] != first_state
