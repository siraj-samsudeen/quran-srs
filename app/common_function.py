from fasthtml.common import *
import fasthtml.common as fh
from monsterui.all import *
from .utils import *
from collections import defaultdict
from .globals import *
import math

# Re-export from app_setup for backward compatibility
from .app_setup import (
    user_auth,
    user_bware,
    hafiz_auth,
    hafiz_bware,
    hyperscript_header,
    alpinejs_header,
    daisyui_css,
    style_css,
    favicon,
    create_app_with_auth,
    error_toast,
    success_toast,
    warning_toast,
)

# Re-export from common_model for backward compatibility
from .common_model import (
    get_surah_name,
    get_page_number,
    get_current_date,
    get_daily_capacity,
    get_last_added_full_cycle_page,
    find_next_memorized_item_id,
    get_hafizs_items,
    get_mode_count,
    get_planned_next_interval,
    add_revision_record,
    get_mode_name,
    get_last_item_id,
    get_juz_name,
    get_mode_name_and_code,
    get_current_plan_id,
    get_item_page_portion,
    get_not_memorized_records,
    get_mode_condition,
    get_srs_daily_limit,
    get_full_cycle_daily_limit,
    populate_hafizs_items_stat_columns,
    get_actual_interval,
    get_page_count,
    get_full_review_item_ids,
)

# Re-export from utils for backward compatibility
from .utils import group_by_type

# Re-export from common_view for backward compatibility
from .common_view import (
    main_area,
    get_page_description,
    render_rating,
    rating_dropdown,
    rating_radio,
    row_background_color,
    create_count_link,
    render_range_row,
    render_bulk_action_bar,
    render_summary_table,
    render_current_date,
)


def make_summary_table(
    mode_code: str,
    auth: str,
    total_page_count=0,
    table_only=False,
):
    current_date = get_current_date(auth)

    def is_review_due(item: dict) -> bool:
        """Check if item is due for review today or overdue."""
        return day_diff(item["next_review"], current_date) >= 0

    def is_reviewed_today(item: dict) -> bool:
        return item["last_review"] == current_date

    def has_mode_code(item: dict, mode_code: str) -> bool:
        return item["mode_code"] == mode_code

    def has_memorized(item: dict) -> bool:
        return item["memorized"]

    def has_revisions(item: dict) -> bool:
        """Check if item has revisions for current mode."""
        return bool(
            revisions(
                where=f"item_id = {item['item_id']} AND mode_code = '{item['mode_code']}'"
            )
        )

    def has_revisions_today(item: dict) -> bool:
        """Check if item has revisions for current mode today."""
        return bool(
            revisions(
                where=f"item_id = {item['item_id']} AND mode_code = '{item['mode_code']}' AND revision_date = '{current_date}'"
            )
        )

    def has_newly_memorized_for_today(item: dict) -> bool:
        newly_memorized_record = revisions(
            where=f"item_id = {item['item_id']} AND revision_date = '{current_date}' AND mode_code = '{NEW_MEMORIZATION_MODE_CODE}'"
        )
        return len(newly_memorized_record) == 1

    qry = f"""
        SELECT hafizs_items.item_id, items.surah_name, hafizs_items.next_review, hafizs_items.last_review, hafizs_items.mode_code, hafizs_items.memorized, hafizs_items.page_number FROM hafizs_items
        LEFT JOIN items on hafizs_items.item_id = items.id
        WHERE {get_mode_condition(mode_code)} AND hafizs_items.hafiz_id = {auth}
        ORDER BY hafizs_items.item_id ASC
    """
    mode_specific_hafizs_items_records = db.q(qry)

    # Route-specific condition builders
    route_conditions = {
        DAILY_REPS_MODE_CODE: lambda item: (
            (is_review_due(item) and not has_newly_memorized_for_today(item))
            or (is_reviewed_today(item) and has_mode_code(item, DAILY_REPS_MODE_CODE))
        ),
        WEEKLY_REPS_MODE_CODE: lambda item: (
            has_mode_code(item, WEEKLY_REPS_MODE_CODE)
            and (
                is_review_due(item) or (is_reviewed_today(item) and has_revisions(item))
            )
        ),
        SRS_MODE_CODE: lambda item: (is_review_due(item) or has_revisions_today(item)),
        FULL_CYCLE_MODE_CODE: lambda item: has_memorized(item),
    }

    filtered_records = [
        i for i in mode_specific_hafizs_items_records if route_conditions[mode_code](i)
    ]

    def get_unique_item_ids(records):
        return list(dict.fromkeys(record["item_id"] for record in records))

    if mode_code == SRS_MODE_CODE:
        exclude_start_page = get_last_added_full_cycle_page(auth)

        # Exclude 3 days worth of pages from SRS (upcoming pages not yet reviewed)
        if exclude_start_page is not None:
            exclude_end_page = exclude_start_page + (
                get_full_cycle_daily_limit(auth) * 3
            )

            filtered_records = [
                record
                for record in filtered_records
                if record["page_number"] < exclude_start_page
                or record["page_number"] > exclude_end_page
            ]

        item_ids = get_unique_item_ids(filtered_records)

        # On a daily basis, This will rotate the items to show (first/last) pages, to ensure that the user can focus on all the pages.
        srs_daily_limit = get_srs_daily_limit(auth)
        if get_day_from_date(current_date) % 2 == 0:
            item_ids = item_ids[:srs_daily_limit]
        else:
            item_ids = item_ids[-srs_daily_limit:]
    else:
        item_ids = get_unique_item_ids(filtered_records)

    if mode_code == FULL_CYCLE_MODE_CODE:
        is_plan_finished, item_ids = get_full_review_item_ids(
            auth=auth,
            total_page_count=total_page_count,
            mode_specific_hafizs_items_records=mode_specific_hafizs_items_records,
            item_ids=item_ids,
        )
    else:
        is_plan_finished = False

    result = render_summary_table(
        auth=auth,
        mode_code=mode_code,
        item_ids=item_ids,
        is_plan_finished=is_plan_finished,
    )
    if table_only:
        return result[1]  # Just the table element for HTMX swap
    return result
