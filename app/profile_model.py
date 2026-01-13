"""Profile model - database operations and business logic for profile management."""

from constants import (
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
    SRS_MODE_CODE,
    NEW_MEMORIZATION_MODE_CODE,
    STATUS_NOT_MEMORIZED,
    STATUS_LEARNING,
    STATUS_REPS,
    STATUS_SOLID,
    STATUS_STRUGGLING,
    STATUS_DISPLAY,
)
from database import db, hafizs_items
from app.common_model import get_page_count
from app.fixed_reps import REP_MODES_CONFIG
from utils import add_days_to_date


def get_status(hafiz_item) -> str:
    """Derive status from memorized flag and mode_code."""
    if isinstance(hafiz_item, dict):
        memorized = hafiz_item.get("memorized")
        mode_code = hafiz_item.get("mode_code")
    else:
        memorized = hafiz_item.memorized
        mode_code = hafiz_item.mode_code

    if not memorized:
        return STATUS_NOT_MEMORIZED

    if mode_code == NEW_MEMORIZATION_MODE_CODE:
        return STATUS_LEARNING
    elif mode_code in (
        DAILY_REPS_MODE_CODE,
        WEEKLY_REPS_MODE_CODE,
        FORTNIGHTLY_REPS_MODE_CODE,
        MONTHLY_REPS_MODE_CODE,
    ):
        return STATUS_REPS
    elif mode_code == FULL_CYCLE_MODE_CODE:
        return STATUS_SOLID
    elif mode_code == SRS_MODE_CODE:
        return STATUS_STRUGGLING

    return STATUS_NOT_MEMORIZED


def get_status_display(status: str) -> tuple[str, str]:
    """Get (icon, label) for a status."""
    return STATUS_DISPLAY.get(status, ("❓", "Unknown"))


def get_status_counts(hafiz_id: int) -> dict:
    """Get page count for each status for dashboard stats."""
    all_items = hafizs_items(where=f"hafiz_id = {hafiz_id}")

    # Group item_ids by status
    groups = {
        STATUS_NOT_MEMORIZED: [],
        STATUS_LEARNING: [],
        STATUS_REPS: [],
        STATUS_SOLID: [],
        STATUS_STRUGGLING: [],
    }

    for hi in all_items:
        status = get_status(hi)
        if status in groups:
            groups[status].append(hi.item_id)

    # Calculate page count for each group
    return {
        STATUS_NOT_MEMORIZED: get_page_count(item_ids=groups[STATUS_NOT_MEMORIZED]),
        STATUS_LEARNING: get_page_count(item_ids=groups[STATUS_LEARNING]),
        STATUS_REPS: get_page_count(item_ids=groups[STATUS_REPS]),
        STATUS_SOLID: get_page_count(item_ids=groups[STATUS_SOLID]),
        STATUS_STRUGGLING: get_page_count(item_ids=groups[STATUS_STRUGGLING]),
        "total": get_page_count(item_ids=[hi.item_id for hi in all_items]),
    }


def apply_status_to_item(hafiz_item, status, current_date):
    """Apply status changes to a hafiz_item. Returns True if applied."""
    if status == STATUS_NOT_MEMORIZED:
        hafiz_item.memorized = False
        hafiz_item.mode_code = None
        hafiz_item.next_review = None
        hafiz_item.next_interval = None
    elif status == STATUS_LEARNING:
        hafiz_item.memorized = True
        hafiz_item.mode_code = NEW_MEMORIZATION_MODE_CODE
        hafiz_item.next_review = None
        hafiz_item.next_interval = None
    elif status == STATUS_REPS:
        hafiz_item.memorized = True
        hafiz_item.mode_code = DAILY_REPS_MODE_CODE
        config = REP_MODES_CONFIG[DAILY_REPS_MODE_CODE]
        hafiz_item.next_interval = config["interval"]
        hafiz_item.next_review = add_days_to_date(current_date, config["interval"])
    elif status == STATUS_SOLID:
        hafiz_item.memorized = True
        hafiz_item.mode_code = FULL_CYCLE_MODE_CODE
        hafiz_item.next_review = None
        hafiz_item.next_interval = None
    elif status == STATUS_STRUGGLING:
        hafiz_item.memorized = True
        hafiz_item.mode_code = SRS_MODE_CODE
        hafiz_item.next_review = None
        hafiz_item.next_interval = None
    else:
        return False
    return True


def get_profile_data(auth, status_filter=None):
    """Get profile data with optional status filter."""
    # Build filter condition
    filter_condition = ""
    if status_filter == STATUS_NOT_MEMORIZED:
        filter_condition = " AND (hafizs_items.memorized = 0 OR hafizs_items.memorized IS NULL)"
    elif status_filter == STATUS_LEARNING:
        filter_condition = f" AND hafizs_items.memorized = 1 AND hafizs_items.mode_code = '{NEW_MEMORIZATION_MODE_CODE}'"
    elif status_filter == STATUS_REPS:
        filter_condition = f" AND hafizs_items.memorized = 1 AND hafizs_items.mode_code IN ('{DAILY_REPS_MODE_CODE}', '{WEEKLY_REPS_MODE_CODE}', '{FORTNIGHTLY_REPS_MODE_CODE}', '{MONTHLY_REPS_MODE_CODE}')"
    elif status_filter == STATUS_SOLID:
        filter_condition = f" AND hafizs_items.memorized = 1 AND hafizs_items.mode_code = '{FULL_CYCLE_MODE_CODE}'"
    elif status_filter == STATUS_STRUGGLING:
        filter_condition = f" AND hafizs_items.memorized = 1 AND hafizs_items.mode_code = '{SRS_MODE_CODE}'"

    qry = f"""
        SELECT items.id as item_id, items.surah_id, pages.page_number, pages.juz_number,
               hafizs_items.id as hafiz_item_id, hafizs_items.memorized, hafizs_items.mode_code,
               hafizs_items.custom_daily_threshold, hafizs_items.custom_weekly_threshold,
               hafizs_items.custom_fortnightly_threshold, hafizs_items.custom_monthly_threshold
        FROM items
        LEFT JOIN pages ON items.page_id = pages.id
        LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
        WHERE items.active != 0 {filter_condition}
        ORDER BY pages.page_number ASC
    """
    return db.q(qry)
