from app.common_function import *
from globals import *


def update_stats_and_interval(item_id: int, mode_code: str):
    populate_hafizs_items_stat_columns(item_id=item_id)


def get_revision_table_data(part_num: int = 1, size: int = 20):
    start = (part_num - 1) * size
    end = start + size
    return revisions(order_by="id desc")[start:end]


def get_revision_by_id(revision_id: int):
    return revisions[revision_id]


def update_revision(revision_details: Revision):
    return revisions.update(revision_details)


def delete_revision(revision_id: int):
    return revisions.delete(revision_id)


def insert_revision(revision_details: Revision):
    return revisions.insert(revision_details)


def insert_revisions_bulk(revision_list):
    return revisions.insert_all(revision_list)


def get_items_by_page_id(page_id: int, active_only: bool = True):
    where_clause = f"page_id = {page_id}"
    if active_only:
        where_clause += " AND active = 1"
    return items(where=where_clause)


def get_item_ids_by_page(page):
    return [i.id for i in get_items_by_page_id(page)]


def are_all_full_cycle_items_revised(plan_id: int) -> bool:
    memorized_items = hafizs_items(
        where=f"mode_code IN ('{SRS_MODE_CODE}', '{FULL_CYCLE_MODE_CODE}') AND memorized = 1 "
    )
    revised_records = revisions(
        where=f"mode_code = '{FULL_CYCLE_MODE_CODE}' AND plan_id = {plan_id}"
    )
    # Check if all plan_item_ids are in revised_item_ids
    return len(memorized_items) == len(revised_records)


def cycle_full_cycle_plan_if_completed():
    """Complete current plan and create new one if all pages are revised."""
    current_plan_id = get_current_plan_id()

    if current_plan_id:
        if are_all_full_cycle_items_revised(current_plan_id):
            plans.update({"completed": 1}, current_plan_id)
            plans.insert(completed=0)
