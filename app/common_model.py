"""Database/model helper functions extracted from common_function.py.

This module contains functions that interact with the database and models,
keeping them separate from UI/view-related code.
"""

from database import (
    db,
    hafizs,
    hafizs_items,
    items,
    plans,
    revisions,
    surahs,
    modes,
    pages,
    Hafiz_Items,
)
from constants import (
    FULL_CYCLE_MODE_CODE, 
    SRS_MODE_CODE,
    NEW_MEMORIZATION_MODE_CODE,
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    GRADUATABLE_MODES,
    STATUS_NOT_MEMORIZED,
    STATUS_LEARNING,
    STATUS_REPS,
    STATUS_SOLID,
    STATUS_STRUGGLING,
    STATUS_DISPLAY,
    DEFAULT_REP_COUNTS
)
from utils import current_time, calculate_days_difference, find_next_greater, format_number
from fasthtml.common import NotFoundError


def get_current_date(auth) -> str:
    current_hafiz = hafizs[auth]
    current_date = current_hafiz.current_date
    if current_date is None:
        current_date = hafizs.update(current_date=current_time(), id=auth).current_date
    return current_date


def get_hafizs_items(item_id) -> Hafiz_Items | None:
    """Get hafiz_items record for the given item_id, or None if not found."""
    current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")
    if current_hafiz_items:
        return current_hafiz_items[0]
    return None


def get_mode_count(item_id, mode_code, hafiz_id=None):
    where_clause = f"item_id = {item_id} AND mode_code = '{mode_code}'"
    if hafiz_id is not None:
        where_clause += f" AND hafiz_id = {hafiz_id}"
    mode_records = revisions(where=where_clause)
    return len(mode_records)


def get_actual_interval(item_id):
    hafiz_items_details = get_hafizs_items(item_id)
    if hafiz_items_details is None:
        return None
    current_date = get_current_date(hafiz_items_details.hafiz_id)

    last_review = hafiz_items_details.last_review
    if not last_review:
        return None
    return calculate_days_difference(last_review, current_date)


def get_planned_next_interval(item_id):
    hafiz_items_details = get_hafizs_items(item_id)
    if hafiz_items_details is None:
        return None
    return hafiz_items_details.next_interval


def add_revision_record(**kwargs):
    return revisions.insert(**kwargs)


def get_not_memorized_records(auth, custom_where=None):
    default = f"hafizs_items.memorized = 0 AND items.active != 0"
    if custom_where:
        default = f"{custom_where}"
    not_memorized_tb = f"""
        SELECT items.id, items.surah_id, items.surah_name,
        hafizs_items.item_id, hafizs_items.memorized, hafizs_items.hafiz_id, pages.juz_number, pages.page_number, revisions.revision_date, revisions.id AS revision_id
        FROM items 
        LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
        LEFT JOIN pages ON items.page_id = pages.id
        LEFT JOIN revisions ON items.id = revisions.item_id
        WHERE {default};
    """
    return db.q(not_memorized_tb)


def get_last_added_full_cycle_page(auth):
    current_date = get_current_date(auth)
    last_full_cycle_record = db.q(
        f"""
        SELECT hafizs_items.page_number FROM revisions
        LEFT JOIN hafizs_items ON revisions.item_id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
        WHERE revisions.revision_date < '{current_date}' AND revisions.mode_code = '{FULL_CYCLE_MODE_CODE}' AND revisions.hafiz_id = {auth}
        ORDER BY revisions.revision_date DESC, revisions.item_id DESC
        LIMIT 1
    """
    )
    if last_full_cycle_record:
        return last_full_cycle_record[0]["page_number"]


def find_next_memorized_item_id(item_id):
    memorized_and_srs_item_ids = [
        i.item_id
        for i in hafizs_items(
            where=f"memorized = 1 AND mode_code IN ('{FULL_CYCLE_MODE_CODE}', '{SRS_MODE_CODE}')"
        )
    ]
    return find_next_greater(memorized_and_srs_item_ids, item_id)


def populate_hafizs_items_stat_columns(item_id: int = None):

    def get_item_id_summary(item_id: int):
        items_rev_data = revisions(
            where=f"item_id = {item_id}", order_by="revision_date ASC"
        )
        good_streak = 0
        bad_streak = 0
        last_review = ""

        for rev in items_rev_data:
            current_rating = rev.rating

            if current_rating == -1:
                bad_streak += 1
                good_streak = 0
            elif current_rating == 1:
                good_streak += 1
                bad_streak = 0
            else:
                good_streak = 0
                bad_streak = 0

            last_review = rev.revision_date

        return {
            "good_streak": good_streak,
            "bad_streak": bad_streak,
            "last_review": last_review,
        }

    # Update the streak for a specific items if item_id is givien
    if item_id is not None:
        current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")
        if current_hafiz_items:
            current_hafiz_items_id = current_hafiz_items[0].id
            hafizs_items.update(get_item_id_summary(item_id), current_hafiz_items_id)

        return None

    # Update the streak for all the items in the hafizs_items
    for h_item in hafizs_items():
        hafizs_items.update(get_item_id_summary(h_item.item_id), h_item.id)


def get_current_plan_id():
    unique_seq_plan_id = [
        i.id for i in plans(where="completed <> 1", order_by="id DESC")
    ]

    if unique_seq_plan_id and not len(unique_seq_plan_id) > 1:
        return unique_seq_plan_id[0]
    return None


def get_full_review_item_ids(auth, mode_specific_hafizs_items_records, item_ids):
    """Get all eligible Full Cycle items (not yet revised in current plan + revised today)."""
    current_date = get_current_date(auth)
    plan_id = get_current_plan_id()

    if plan_id is not None:
        # Filter out items that have been revised in the current plan (but not today)
        revised_items_in_plan = revisions(
            where=f"mode_code = '{FULL_CYCLE_MODE_CODE}' AND plan_id = {plan_id} AND revision_date != '{current_date}'",
            order_by="revision_date DESC, id DESC",
        )
        # Convert to set for faster lookup
        revised_items_in_plan_set = {r.item_id for r in revised_items_in_plan}
        eligible_item_ids = [i for i in item_ids if i not in revised_items_in_plan_set]

        # Check if plan is finished (no more items to review)
        is_plan_finished = len(eligible_item_ids) == 0
    else:
        eligible_item_ids = []
        is_plan_finished = False

    # Get all item_ids revised today in full_cycle mode
    today_full_cycle_revisions = {
        r.item_id
        for r in revisions(
            where=f"revision_date = '{current_date}' AND mode_code = '{FULL_CYCLE_MODE_CODE}'"
        )
    }

    # Get items that have been revised today in full_cycle mode, but are not in eligible_item_ids
    today_revisioned_items = [
        item["item_id"]
        for item in mode_specific_hafizs_items_records
        if item["item_id"] in today_full_cycle_revisions
        and item["item_id"] not in eligible_item_ids
    ]

    # Combine and sort the item_ids
    final_item_ids = sorted(list(set(eligible_item_ids + today_revisioned_items)))
    return is_plan_finished, final_item_ids


# === Additional Database Query Functions ===


def get_juz_number_for_item(item_id: int) -> int:
    """Get juz number for an item via its page."""
    qry = f"SELECT pages.juz_number FROM pages LEFT JOIN items ON pages.id = items.page_id WHERE items.id = {item_id}"
    result = db.q(qry)
    return result[0]["juz_number"] if result else None


def get_unmemorized_items(auth: int) -> list[dict]:
    """Get all unmemorized items for a hafiz."""
    qry = f"""
        SELECT hafizs_items.item_id, hafizs_items.page_number
        FROM hafizs_items
        WHERE hafizs_items.hafiz_id = {auth}
          AND hafizs_items.memorized = 0
        ORDER BY hafizs_items.item_id ASC
    """
    return db.q(qry)


def get_mode_specific_hafizs_items(auth: int, mode_condition: str) -> list[dict]:
    """Get hafiz items filtered by mode condition with item details."""
    qry = f"""
        SELECT hafizs_items.item_id, items.surah_name, hafizs_items.next_review, 
               hafizs_items.last_review, hafizs_items.mode_code, hafizs_items.memorized, 
               hafizs_items.page_number, hafizs_items.loved 
        FROM hafizs_items
        LEFT JOIN items on hafizs_items.item_id = items.id
        WHERE {mode_condition} AND hafizs_items.hafiz_id = {auth}
        ORDER BY hafizs_items.item_id ASC
    """
    return db.q(qry)


def get_datewise_revisions(date_range: list[str], hafiz_id: int = None) -> list[dict]:
    """Get all revisions for a date range with item details."""
    if not date_range:
        return []
    
    dates_str = ", ".join(f"'{d}'" for d in date_range)
    hafiz_condition = f"AND revisions.hafiz_id = {hafiz_id}" if hafiz_id else ""
    
    qry = f"""
        SELECT revisions.id, revisions.item_id, revisions.revision_date, 
               revisions.mode_code, items.page_id
        FROM revisions
        LEFT JOIN items ON revisions.item_id = items.id
        WHERE revisions.revision_date IN ({dates_str}) {hafiz_condition}
        ORDER BY revisions.revision_date DESC, revisions.mode_code ASC
    """
    return db.q(qry)


def get_earliest_revision_date(hafiz_id: int = None) -> str | None:
    """Get the earliest revision date for a hafiz."""
    qry = "SELECT MIN(revision_date) AS earliest_date FROM revisions"
    if hafiz_id:
        qry += f" WHERE hafiz_id = {hafiz_id}"
    result = db.q(qry)
    return result[0]["earliest_date"] if result else None


def get_unrevised_memorized_items(auth: int, plan_id: int, start_page: int, length: int) -> list[int]:
    """Get unrevised memorized item IDs for full cycle starting from a page."""
    qry = f"""
        SELECT hafizs_items.item_id, hafizs_items.page_number
        FROM hafizs_items
        LEFT JOIN revisions ON revisions.item_id = hafizs_items.item_id 
            AND revisions.plan_id = {plan_id} AND revisions.hafiz_id = {auth}
        WHERE hafizs_items.memorized = 1 
            AND hafizs_items.mode_code IN ('{FULL_CYCLE_MODE_CODE}', '{SRS_MODE_CODE}') 
            AND hafizs_items.hafiz_id = {auth} 
            AND revisions.item_id IS NULL 
            AND hafizs_items.page_number >= {start_page}
        ORDER BY hafizs_items.page_number ASC
        LIMIT {length};
    """
    rows = db.q(qry)
    return [row["item_id"] for row in rows]


def get_prev_next_item_ids(auth: int, current_item_id: int) -> tuple[int | None, int | None]:
    """Get previous and next item IDs for navigation."""
    def build_nav_query(operator, sort_order):
        return f"""
            SELECT items.id, pages.page_number FROM revisions
            LEFT JOIN items ON revisions.item_id = items.id
            LEFT JOIN pages ON items.page_id = pages.id
            WHERE revisions.hafiz_id = {auth} AND items.active != 0 
                AND items.id {operator} {current_item_id}
            ORDER BY items.id {sort_order} LIMIT 1;
        """

    prev_result = db.q(build_nav_query("<", "DESC"))
    next_result = db.q(build_nav_query(">", "ASC"))
    prev_id = prev_result[0]["id"] if prev_result else None
    next_id = next_result[0]["id"] if next_result else None
    return prev_id, next_id


def get_item_page_portion(item_id: int) -> float:
    """
    Calculates the portion of a page that a single item represents.
    For example, if a page is divided into 4 items, each item represents 0.25 of the page.
    """
    page_no = items[item_id].page_id
    total_parts = items(where=f"page_id = {page_no} and active = 1")
    if not total_parts:
        return 0
    return 1 / len(total_parts)


def get_page_count(records: list = None, item_ids: list = None) -> float:
    total_count = 0
    if item_ids:
        process_items = item_ids
    elif records:
        process_items = [record.item_id for record in records]
    else:
        return format_number(total_count)

    # Calculate page count
    for item_id in process_items:
        total_count += get_item_page_portion(item_id)
    return format_number(total_count)


def get_surah_name(page_id=None, item_id=None):
    if item_id:
        surah_id = items[item_id].surah_id
    else:
        surah_id = items(where=f"page_id = {page_id}")[0].surah_id
    surah_details = surahs[surah_id]
    return surah_details.name

def get_page_number(item_id):
    page_id = items[item_id].page_id
    return pages[page_id].page_number

def get_mode_name(mode_code: str):
    try:
        return modes[mode_code].name
    except NotFoundError:
        return mode_code

def get_mode_icon(mode_code: str) -> str:
    """Returns emoji icon for each mode."""
    icons = {
        NEW_MEMORIZATION_MODE_CODE: "🆕",
        DAILY_REPS_MODE_CODE: "☀️",
        WEEKLY_REPS_MODE_CODE: "📅",
        FORTNIGHTLY_REPS_MODE_CODE: "📆",
        MONTHLY_REPS_MODE_CODE: "🗓️",
        FULL_CYCLE_MODE_CODE: "🔄",
        SRS_MODE_CODE: "🧠",
    }
    return icons.get(mode_code, "📖")

def can_graduate(mode_code: str) -> bool:
    """Returns True if mode can be manually graduated (DR, WR, FR, MR)."""
    return mode_code in GRADUATABLE_MODES

def get_last_item_id():
    result = items(where="active = 1", order_by="id DESC")
    return result[0].id if result else 0

def get_juz_name(page_id=None, item_id=None):
    if item_id:
        qry = f"SELECT pages.juz_number FROM pages LEFT JOIN items ON pages.id = items.page_id WHERE items.id = {item_id}"
        juz_number = db.q(qry)[0]["juz_number"]
    else:
        juz_number = pages[page_id].juz_number
    return juz_number

def get_mode_name_and_code():
    all_modes = modes()
    mode_code_list = [mode.code for mode in all_modes]
    mode_name_list = [mode.name for mode in all_modes]
    return mode_code_list, mode_name_list

def get_page_part_info(item_id: int) -> tuple[int, int] | None:
    """
    Returns (part_number, total_parts) if item is part of a split page, None otherwise.
    """
    page_no = items[item_id].page_id
    page_items = items(where=f"page_id = {page_no} and active = 1", order_by="id ASC")
    total_parts = len(page_items)
    if total_parts <= 1:
        return None
    # Find position of this item in the list
    for idx, item in enumerate(page_items):
        if item.id == item_id:
            return (idx + 1, total_parts)
    return None

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
