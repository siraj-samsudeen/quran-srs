from constants import *
from app.common_function import get_hafizs_items, add_days_to_date, create_app_with_auth
from app.fixed_reps import REP_MODES_CONFIG, MODE_TO_THRESHOLD_COLUMN
from database import hafizs_items


new_memorization_app, rt = create_app_with_auth()


def update_hafiz_item_for_new_memorization(rev, mode_code=None, rep_count=None, current_date=None):
    """
    Update hafiz_item after new memorization revision (called by Close Date).

    Args:
        rev: The revision record
        mode_code: Target rep mode (defaults to DAILY_REPS_MODE_CODE)
        rep_count: Custom repetition threshold (defaults to mode's default)
        current_date: Current date for scheduling (optional)
    """
    hafiz_item_details = get_hafizs_items(rev.item_id)
    if hafiz_item_details is None:
        return  # Skip if no hafiz_items record exists

    target_mode = mode_code or DAILY_REPS_MODE_CODE
    hafiz_item_details.mode_code = target_mode
    hafiz_item_details.memorized = True

    # Set custom threshold if provided
    if rep_count is not None and target_mode in MODE_TO_THRESHOLD_COLUMN:
        column = MODE_TO_THRESHOLD_COLUMN[target_mode]
        setattr(hafiz_item_details, column, int(rep_count))

    # Set next_review and next_interval based on mode
    if target_mode in REP_MODES_CONFIG and current_date:
        config = REP_MODES_CONFIG[target_mode]
        hafiz_item_details.next_interval = config["interval"]
        hafiz_item_details.next_review = add_days_to_date(current_date, config["interval"])
    elif target_mode == FULL_CYCLE_MODE_CODE:
        hafiz_item_details.next_interval = None
        hafiz_item_details.next_review = None

    hafizs_items.update(hafiz_item_details)


# Old HTMX routes removed - now using JSON APIs in main.py:
# - POST /api/new_memorization/toggle
# - POST /api/new_memorization/bulk_mark
