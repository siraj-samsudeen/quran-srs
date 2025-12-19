"""
Hafiz data model - database operations for hafiz management.

Extracted from users_model.py for better separation of concerns.
"""

from dataclasses import dataclass
from database import *
from constants import *
from app.common_function import get_page_number


# ============================================================================
# DATACLASSES & TYPES
# ============================================================================

@dataclass
class Hafiz:
    id: int | None = None
    name: str | None = None
    user_id: int | None = None
    current_date: str | None = None
    page_size: int | None = None


# ============================================================================
# HAFIZ QUERY OPERATIONS
# ============================================================================

def get_hafizs_for_user(user_id: int):
    return hafizs(where=f"user_id={user_id}")


def get_hafiz_by_name(name: str):
    """Get hafiz by name. Returns Hafiz or None. Useful for tests and admin features."""
    result = hafizs(where=f"name = '{name}'")
    return result[0] if result else None


# ============================================================================
# HAFIZ INITIALIZATION OPERATIONS
# ============================================================================

def reset_table_filters():
    """Reset xtra attributes to show data for all records"""
    revisions.xtra()


def populate_hafiz_items(hafiz_id: int):
    """
    Populate hafizs_items table with all active items for a new hafiz.

    This creates entries for all Quran items (pages/parts) that don't yet
    exist for this hafiz, setting them to Full Cycle mode by default.
    """
    # Reset xtra attributes
    hafizs_items.xtra()

    # Find all active items not yet in hafizs_items for this hafiz
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
    """
    Create a new Full Cycle plan for hafiz.

    Called when hafiz is first created or when previous plan completes.
    """
    # Reset xtra attributes
    plans.xtra()
    return plans.insert(
        hafiz_id=hafiz_id,
        completed=0,
    )
