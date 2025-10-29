from app.common_function import *
from globals import *
from app.srs_reps import recalculate_intervals_on_srs_records


# Model functions for revision data operations
def update_stats_and_interval(item_id: int, mode_id: int, current_date: str):
    """Update statistics and intervals for revision items"""
    populate_hafizs_items_stat_columns(item_id=item_id)
    if mode_id == SRS_MODE_ID:
        recalculate_intervals_on_srs_records(item_id=item_id, current_date=current_date)


def get_revision_table_data(part_num: int = 1, size: int = 20):
    """Get paginated revision data for table display"""
    start = (part_num - 1) * size
    end = start + size
    data = revisions(order_by="id desc")[start:end]
    return data


def get_revision_by_id(revision_id: int):
    """Get revision record by ID"""
    return revisions[revision_id]


def update_revision(revision_details: Revision):
    """Update revision record"""
    return revisions.update(revision_details)


def delete_revision(revision_id: int):
    """Delete revision record"""
    return revisions.delete(revision_id)


def insert_revision(revision_details: Revision):
    """Insert new revision record"""
    return revisions.insert(revision_details)


def insert_revisions_bulk(revision_list):
    """Insert multiple revision records"""
    return revisions.insert_all(revision_list)


def get_revisions_by_item_and_mode(item_id: int, mode_id: int):
    """Get revisions for specific item and mode"""
    return revisions(where=f"item_id = {item_id} AND mode_id = {mode_id}")


def update_revision_rating_only(revision_id: int, rating: int):
    """Update only the rating for a revision"""
    return revisions.update({"rating": rating}, revision_id)


def update_revision_next_interval(revision_id: int, next_interval: int):
    """Update next interval for a revision"""
    return revisions.update({"next_interval": next_interval}, revision_id)


def get_items_by_page_id(page_id: int, active_only: bool = True):
    """Get items for a specific page"""
    where_clause = f"page_id = {page_id}"
    if active_only:
        where_clause += " AND active = 1"
    return items(where=where_clause)


def get_item_ids_by_page(page):
    return [i.id for i in get_items_by_page_id(page)]


def get_hafiz_item_by_item_id(item_id: int):
    """Get hafiz item record by item ID"""
    return hafizs_items(where=f"item_id = {item_id}")[0]


def update_hafiz_item_status(hafiz_item_id: int, status_id: int):
    """Update hafiz item status"""
    return hafizs_items.update({"status_id": status_id}, hafiz_item_id)


def update_hafiz_item(hafiz_item: Hafiz_Items):
    """Update hafiz item record"""
    return hafizs_items.update(hafiz_item)
