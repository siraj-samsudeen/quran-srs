"""
Hafiz Module Unit Tests

Unit tests for hafiz model and service functions.
Tests pure Python functions without HTTP or browser.

Note: Integration tests (routes, HTMX) are in tests/integration/hafiz_test.py
      E2E tests (Playwright) are in tests/e2e/hafiz_test.py
"""

import pytest
from app.hafiz_model import (
    Hafiz,
    hafizs,
    get_hafiz,
    update_hafiz,
    insert_hafiz,
    delete_hafiz,
    get_hafizs_for_user,
    populate_hafiz_items,
    create_new_plan,
)
from app.hafiz_service import setup_new_hafiz
from app.globals import hafizs_items, plans


# =============================================================================
# Unit Tests - Pure Python, no HTTP
# =============================================================================


def test_get_hafiz():
    """Unit test: get_hafiz returns Hafiz instance."""
    hafiz = get_hafiz(1)

    assert isinstance(hafiz, Hafiz)
    assert hafiz.id == 1
    assert hafiz.name is not None


def test_update_hafiz():
    """Unit test: update_hafiz modifies database."""
    # Get current hafiz
    original = get_hafiz(1)
    original_capacity = original.daily_capacity

    # Update with new capacity
    new_capacity = 99 if original_capacity != 99 else 88
    updated_data = Hafiz(
        id=1,
        name=original.name,
        daily_capacity=new_capacity,
        user_id=original.user_id,
        current_date=original.current_date,
    )
    update_hafiz(updated_data, 1)

    # Verify update
    updated = get_hafiz(1)
    assert updated.daily_capacity == new_capacity

    # Restore original
    update_hafiz(original, 1)


def test_insert_hafiz():
    """Unit test: insert_hafiz creates new record."""
    # Create new hafiz
    new_hafiz = Hafiz(
        id=None,
        name="Test Hafiz",
        daily_capacity=5,
        user_id=1,
        current_date="2025-01-01",
    )
    created = insert_hafiz(new_hafiz)

    # Verify creation
    assert created.id is not None
    assert created.name == "Test Hafiz"
    assert created.daily_capacity == 5

    # Cleanup
    delete_hafiz(created.id)


def test_delete_hafiz():
    """Unit test: delete_hafiz removes record."""
    # Create temporary hafiz
    temp_hafiz = insert_hafiz(
        Hafiz(id=None, name="Temp Hafiz", daily_capacity=3, user_id=1)
    )
    hafiz_id = temp_hafiz.id

    # Delete it
    delete_hafiz(hafiz_id)

    # Verify deletion
    with pytest.raises(Exception):
        get_hafiz(hafiz_id)


def test_get_hafizs_for_user():
    """Unit test: get_hafizs_for_user returns user's hafizs."""
    # Get hafizs for user 1
    user_hafizs = get_hafizs_for_user(1)

    # Verify results
    assert len(user_hafizs) > 0
    assert all(h.user_id == 1 for h in user_hafizs)
    assert all(isinstance(h, Hafiz) for h in user_hafizs)


def test_populate_hafiz_items():
    """Unit test: populate_hafiz_items creates hafizs_items records."""
    # Create temporary hafiz
    temp_hafiz = insert_hafiz(
        Hafiz(id=None, name="Temp Hafiz", daily_capacity=3, user_id=1)
    )
    hafiz_id = temp_hafiz.id

    # Reset xtra to query without hafiz filter
    hafizs_items.xtra()

    # Count items before
    items_before = hafizs_items(where=f"hafiz_id={hafiz_id}")
    assert len(items_before) == 0

    # Populate items
    populate_hafiz_items(hafiz_id)

    # Verify items created
    items_after = hafizs_items(where=f"hafiz_id={hafiz_id}")
    assert len(items_after) > 600  # Should have 604+ items (one per Quran page)

    # Cleanup
    delete_hafiz(hafiz_id)


def test_create_new_plan():
    """Unit test: create_new_plan creates plan record."""
    # Create temporary hafiz
    temp_hafiz = insert_hafiz(
        Hafiz(id=None, name="Temp Hafiz", daily_capacity=3, user_id=1)
    )
    hafiz_id = temp_hafiz.id

    # Reset xtra to query without filter
    plans.xtra()

    # Create plan
    plan = create_new_plan(hafiz_id)

    # Verify plan created
    assert plan.id is not None
    assert plan.hafiz_id == hafiz_id
    assert plan.completed == 0

    # Cleanup
    delete_hafiz(hafiz_id)


def test_setup_new_hafiz():
    """Unit test: setup_new_hafiz orchestrates hafiz initialization."""
    # Create temporary hafiz
    temp_hafiz = insert_hafiz(
        Hafiz(id=None, name="Temp Hafiz", daily_capacity=3, user_id=1)
    )
    hafiz_id = temp_hafiz.id

    # Reset xtra filters
    hafizs_items.xtra()
    plans.xtra()

    # Run setup
    setup_new_hafiz(hafiz_id)

    # Verify items created
    items = hafizs_items(where=f"hafiz_id={hafiz_id}")
    assert len(items) > 600

    # Verify plan created
    hafiz_plans = plans(where=f"hafiz_id={hafiz_id}")
    assert len(hafiz_plans) > 0

    # Cleanup
    delete_hafiz(hafiz_id)


def test_get_hafiz_invalid_id():
    """Error test: get_hafiz with invalid ID raises exception."""
    with pytest.raises(Exception):
        get_hafiz(999999)


def test_delete_hafiz_cascade():
    """Unit test: deleting hafiz cascades to related records."""
    # Create temporary hafiz with full setup
    temp_hafiz = insert_hafiz(
        Hafiz(id=None, name="Temp Hafiz", daily_capacity=3, user_id=1)
    )
    hafiz_id = temp_hafiz.id
    setup_new_hafiz(hafiz_id)

    # Reset xtra filters
    hafizs_items.xtra()
    plans.xtra()

    # Verify related records exist
    items_before = hafizs_items(where=f"hafiz_id={hafiz_id}")
    plans_before = plans(where=f"hafiz_id={hafiz_id}")
    assert len(items_before) > 0
    assert len(plans_before) > 0

    # Delete hafiz
    delete_hafiz(hafiz_id)

    # Verify cascade deletion
    items_after = hafizs_items(where=f"hafiz_id={hafiz_id}")
    plans_after = plans(where=f"hafiz_id={hafiz_id}")
    assert len(items_after) == 0
    assert len(plans_after) == 0


