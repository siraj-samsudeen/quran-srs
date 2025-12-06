"""
Common Model Module

Pure data access functions - queries and simple CRUD operations.
No UI rendering or complex business logic.
"""

import math
from .globals import (
    db,
    hafizs_items,
    items,
    modes,
    pages,
    plans,
    revisions,
    surahs,
    FULL_CYCLE_MODE_CODE,
    SRS_MODE_CODE,
    NEW_MEMORIZATION_MODE_CODE,
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
)
from .hafiz_model import hafizs
from .utils import current_time, find_next_greater, calculate_days_difference, format_number


def get_surah_name(page_id=None, item_id=None):
    """Get surah name for a given page or item."""
    if item_id:
        surah_id = items[item_id].surah_id
    else:
        surah_id = items(where=f"page_id = {page_id}")[0].surah_id
    surah_details = surahs[surah_id]
    return surah_details.name


def get_page_number(item_id):
    """Get page number for a given item."""
    page_id = items[item_id].page_id
    return pages[page_id].page_number


def get_current_date(auth) -> str:
    """Get current date for a hafiz, initializing if needed."""
    current_hafiz = hafizs[auth]
    current_date = current_hafiz.current_date
    if current_date is None:
        current_date = hafizs.update(current_date=current_time(), id=auth).current_date
    return current_date


def get_daily_capacity(auth):
    """Get daily capacity for a hafiz."""
    current_hafiz = hafizs[auth]
    return current_hafiz.daily_capacity


def get_last_added_full_cycle_page(auth):
    """Get the last page added to full cycle revision."""
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
    """Find the next memorized item after the given item_id."""
    memorized_and_srs_item_ids = [
        i.item_id
        for i in hafizs_items(
            where=f"memorized = 1 AND mode_code IN ('{FULL_CYCLE_MODE_CODE}', '{SRS_MODE_CODE}')"
        )
    ]
    return find_next_greater(memorized_and_srs_item_ids, item_id)


def get_hafizs_items(item_id):
    """Get hafizs_items record for a given item."""
    current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")
    if current_hafiz_items:
        return current_hafiz_items[0]
    else:
        return ValueError(f"No hafizs_items found for item_id {item_id}")


def get_mode_count(item_id, mode_code):
    """Count revisions for an item in a specific mode."""
    mode_records = revisions(where=f"item_id = {item_id} AND mode_code = '{mode_code}'")
    return len(mode_records)


def get_planned_next_interval(item_id):
    """Get planned next interval for an item."""
    return get_hafizs_items(item_id).next_interval


def add_revision_record(**kwargs):
    """Insert a new revision record."""
    return revisions.insert(**kwargs)


def get_mode_name(mode_code: str):
    """Get mode name from mode code."""
    return modes[mode_code].name


def get_last_item_id():
    """Get the last active item ID."""
    return items(where="active = 1", order_by="id DESC")[0].id


def get_juz_name(page_id=None, item_id=None):
    """Get juz number for a given page or item."""
    if item_id:
        qry = f"SELECT pages.juz_number FROM pages LEFT JOIN items ON pages.id = items.page_id WHERE items.id = {item_id}"
        juz_number = db.q(qry)[0]["juz_number"]
    else:
        juz_number = pages[page_id].juz_number
    return juz_number


def get_mode_name_and_code():
    """Get all mode codes and names."""
    all_modes = modes()
    mode_code_list = [mode.code for mode in all_modes]
    mode_name_list = [mode.name for mode in all_modes]
    return mode_code_list, mode_name_list


def get_current_plan_id():
    """Get the current active plan ID."""
    unique_seq_plan_id = [
        i.id for i in plans(where="completed <> 1", order_by="id DESC")
    ]

    if unique_seq_plan_id and not len(unique_seq_plan_id) > 1:
        return unique_seq_plan_id[0]
    return None


def get_item_page_portion(item_id: int) -> float:
    """
    Calculate the portion of a page that a single item represents.
    For example, if a page is divided into 4 items, each item represents 0.25.
    """
    page_no = items[item_id].page_id
    total_parts = items(where=f"page_id = {page_no} and active = 1")
    if not total_parts:
        return 0
    return 1 / len(total_parts)


def get_not_memorized_records(auth, custom_where=None):
    """Get records for items not yet memorized."""
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


def get_mode_condition(mode_code: str):
    """Build SQL condition for mode filtering (full cycle includes SRS)."""
    mode_code_mapping = {
        FULL_CYCLE_MODE_CODE: [f"'{FULL_CYCLE_MODE_CODE}'", f"'{SRS_MODE_CODE}'"],
    }
    retrieved_mode_codes = mode_code_mapping.get(mode_code)
    if retrieved_mode_codes is None:
        mode_condition = f"mode_code = '{mode_code}'"
    else:
        mode_condition = f"mode_code IN ({', '.join(retrieved_mode_codes)})"
    return mode_condition


def get_srs_daily_limit(auth):
    """Calculate SRS daily limit (50% of daily capacity)."""
    return math.ceil(get_daily_capacity(auth) * 0.5)


def get_full_cycle_daily_limit(auth):
    """Calculate Full Cycle daily limit (100% of daily capacity)."""
    return get_daily_capacity(auth)


def populate_hafizs_items_stat_columns(item_id: int = None):
    """Rebuild hafizs_items statistics from revision history.

    This function replays revision history to compute:
    - good_streak, bad_streak: Consecutive rating streaks
    - last_review: Date of most recent revision
    - next_interval: Restored from last revision that has it (NOT recalculated)

    The next_interval is read from stored revision records to preserve
    historical algorithm decisions even after algorithm changes.
    """

    def get_item_id_summary(item_id: int):
        items_rev_data = revisions(
            where=f"item_id = {item_id}", order_by="revision_date ASC"
        )
        good_streak = 0
        bad_streak = 0
        last_review = ""
        last_next_interval = None  # Track from revision history

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

            # Capture next_interval from revision record (preserves historical decisions)
            if rev.next_interval is not None:
                last_next_interval = rev.next_interval

        result = {
            "good_streak": good_streak,
            "bad_streak": bad_streak,
            "last_review": last_review,
        }

        # Only include next_interval if we found one in history
        if last_next_interval is not None:
            result["next_interval"] = last_next_interval

        return result

    if item_id is not None:
        current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")
        if current_hafiz_items:
            current_hafiz_items_id = current_hafiz_items[0].id
            hafizs_items.update(get_item_id_summary(item_id), current_hafiz_items_id)
        return None

    for h_item in hafizs_items():
        hafizs_items.update(get_item_id_summary(h_item.item_id), h_item.id)


def get_actual_interval(item_id):
    """Calculate actual days since last review."""
    hafiz_items_details = get_hafizs_items(item_id)
    current_date = get_current_date(hafiz_items_details.hafiz_id)

    last_review = hafiz_items_details.last_review
    if not last_review:
        return None
    return calculate_days_difference(last_review, current_date)


def get_page_count(records: list = None, item_ids: list = None) -> float:
    """Calculate total page count from revision records or item IDs."""
    total_count = 0
    if item_ids:
        process_items = item_ids
    elif records:
        process_items = [record.item_id for record in records]
    else:
        return format_number(total_count)

    for item_id in process_items:
        total_count += get_item_page_portion(item_id)
    return format_number(total_count)


def get_full_review_item_ids(
    auth, total_page_count, mode_specific_hafizs_items_records, item_ids
):
    """Get item IDs for Full Cycle review based on plan and daily limit."""
    current_date = get_current_date(auth)
    plan_id = get_current_plan_id()

    def get_next_item_range_from_item_id(
        eligible_item_ids, start_item_id, total_page_count
    ):
        try:
            start_index = eligible_item_ids.index(start_item_id)
            item_ids_to_process = eligible_item_ids[start_index:]
        except ValueError:
            item_ids_to_process = eligible_item_ids

        final_item_ids = []
        current_page_count = 0
        for item_id in item_ids_to_process:
            if current_page_count >= total_page_count:
                break
            current_page_count += get_item_page_portion(item_id)
            final_item_ids.append(item_id)

        is_plan_finished = len(eligible_item_ids) == len(final_item_ids)

        return is_plan_finished, final_item_ids

    if plan_id is not None:
        revised_items_in_plan = revisions(
            where=f"mode_code = '{FULL_CYCLE_MODE_CODE}' AND plan_id = {plan_id} AND revision_date != '{current_date}'",
            order_by="revision_date DESC, id DESC",
        )
        revised_items_in_plan_set = {r.item_id for r in revised_items_in_plan}
        eligible_item_ids = [i for i in item_ids if i not in revised_items_in_plan_set]

        last_added_item_id = (
            revised_items_in_plan[0].item_id if revised_items_in_plan else 0
        )

        next_item_id = find_next_greater(eligible_item_ids, last_added_item_id)
    else:
        eligible_item_ids = []
        next_item_id = 0

    is_plan_finished, next_item_ids = get_next_item_range_from_item_id(
        eligible_item_ids, next_item_id, total_page_count
    )

    today_full_cycle_revisions = {
        r.item_id
        for r in revisions(
            where=f"revision_date = '{current_date}' AND mode_code = '{FULL_CYCLE_MODE_CODE}'"
        )
    }

    today_revisioned_items = [
        item["item_id"]
        for item in mode_specific_hafizs_items_records
        if item["item_id"] in today_full_cycle_revisions
        and item["item_id"] not in next_item_ids
    ]

    final_item_ids = sorted(list(set(next_item_ids + today_revisioned_items)))
    return is_plan_finished, final_item_ids
