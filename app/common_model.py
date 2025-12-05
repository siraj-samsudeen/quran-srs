"""
Common Model Module

Pure data access functions - queries and simple CRUD operations.
No UI rendering or complex business logic.
"""

from .globals import (
    db,
    hafizs,
    hafizs_items,
    items,
    modes,
    pages,
    plans,
    revisions,
    surahs,
    FULL_CYCLE_MODE_CODE,
    SRS_MODE_CODE,
)
from .utils import current_time, find_next_greater


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
