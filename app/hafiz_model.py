"""
Hafiz Model Module

Schema definition and data access for hafiz operations.

This module follows the MVC+S pattern:
- Model (this file): Dataclass + table linking + CRUD operations
- View (hafiz_view.py): UI rendering functions
- Controller (hafiz_controller.py): Route handlers
- Service (hafiz_service.py): Business logic and workflows

Pattern Guidelines:
-----------------

1. **Accessing Hafiz Records**
   Prefer get_hafiz(auth) over direct table access hafizs[auth]:
   - Provides consistent API across codebase
   - Easier to add error handling/logging later
   - Makes code more testable

   Example:
   ```python
   # ✅ Preferred
   current_hafiz = get_hafiz(auth)

   # ⚠️ Works but less consistent
   current_hafiz = hafizs[auth]
   ```

2. **Self-Contained Models**
   Each model imports only from globals, not other models:
   - Avoids circular imports
   - Keeps dependencies clear
   - Makes models independently testable

   Example:
   ```python
   from .globals import db, hafizs_items, plans
   # ❌ Don't import from other models
   ```

3. **CRUD vs Business Logic**
   This model contains only CRUD operations:
   - get_hafiz(), update_hafiz(), insert_hafiz(), delete_hafiz()
   - populate_hafiz_items() and create_new_plan() are here for now
     but orchestration logic lives in hafiz_service.py

   For complex workflows, use hafiz_service.py:
   ```python
   from hafiz_service import setup_new_hafiz
   setup_new_hafiz(hafiz_id)  # Handles both populate + create_new_plan
   ```
"""

from dataclasses import dataclass
from .globals import db, hafizs_items, plans, FULL_CYCLE_MODE_CODE
from .utils import get_page_number

__all__ = [
    "Hafiz",
    "hafizs",
    "get_hafiz",
    "update_hafiz",
    "insert_hafiz",
    "delete_hafiz",
    "get_hafizs_for_user",
    "populate_hafiz_items",
    "create_new_plan",
]


@dataclass
class Hafiz:
    """Hafiz profile belonging to a user."""

    id: int
    name: str | None = None
    daily_capacity: int | None = None
    user_id: int | None = None
    current_date: str | None = None  # Virtual date for this hafiz


# Get table reference and link schema
hafizs = db.t.hafizs
hafizs.cls = Hafiz


# =============================================================================
# CRUD Operations
# =============================================================================


def get_hafiz(hafiz_id: int) -> Hafiz:
    """Get hafiz record by ID."""
    return hafizs[hafiz_id]


def update_hafiz(hafiz_data: Hafiz, hafiz_id: int) -> None:
    """Update hafiz record."""
    hafizs.update(hafiz_data, hafiz_id)


def insert_hafiz(hafiz: Hafiz) -> Hafiz:
    """Insert new hafiz record."""
    return hafizs.insert(hafiz)


def delete_hafiz(hafiz_id: int) -> None:
    """Delete hafiz record (cascade will handle related records)."""
    hafizs.delete(hafiz_id)


def get_hafizs_for_user(user_id: int) -> list[Hafiz]:
    """Get all hafizs associated with a user."""
    return hafizs(where=f"user_id={user_id}")


# =============================================================================
# Hafiz Setup Operations
# =============================================================================


def populate_hafiz_items(hafiz_id: int) -> None:
    """Populate hafizs_items for a new or existing hafiz with missing items."""
    # Reset xtra attributes
    hafizs_items.xtra()
    # This query will return all the missing items for that hafiz or all items for new hafiz
    # and we will add the items in to the hafizs_items table
    qry = f"""
    SELECT items.id from items
    LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {hafiz_id}
    WHERE items.active <> 0 AND hafizs_items.item_id IS Null;
    """
    ct = db.q(qry)
    missing_item_ids = [r["id"] for r in ct]

    if missing_item_ids:
        for missing_item_id in missing_item_ids:
            hafizs_items.insert(
                hafiz_id=hafiz_id,
                item_id=missing_item_id,
                page_number=get_page_number(missing_item_id),
                mode_code=FULL_CYCLE_MODE_CODE,
            )


def create_new_plan(hafiz_id: int):
    """Create initial revision plan for a new hafiz.

    Returns:
        Plan: The newly created plan record
    """
    # Reset xtra attributes
    plans.xtra()
    return plans.insert(
        hafiz_id=hafiz_id,
        completed=0,
    )
