# from globals import *
from app.common_function import *

REP_MODES_CONFIG = {
    DAILY_REPS_MODE_ID: {
        "interval": 1,
        "threshold": 7,
        "next_mode_id": WEEKLY_REPS_MODE_ID,
    },  # Daily -> Weekly
    WEEKLY_REPS_MODE_ID: {
        "interval": 7,
        "threshold": 7,
        "next_mode_id": FULL_CYCLE_MODE_ID,
    },  # Weekly -> Full Cycle
}


def get_daily_reps_table(auth):
    daily_reps_table, daily_reps_items = make_summary_table(
        mode_ids=[str(NEW_MEMORIZATION_MODE_ID), str(DAILY_REPS_MODE_ID)],
        route="daily_reps",
        auth=auth,
    )

    daily_reps_target = get_page_count(item_ids=daily_reps_items)

    return daily_reps_table, daily_reps_target


def get_weekly_reps_table(auth):
    # Include mode_id=1 as well so that graduated watch list items are included
    weekly_reps_table, weekly_reps_items = make_summary_table(
        mode_ids=[str(WEEKLY_REPS_MODE_ID), str(FULL_CYCLE_MODE_ID)],
        route="weekly_reps",
        auth=auth,
    )
    weekly_reps_target = get_page_count(item_ids=weekly_reps_items)

    return weekly_reps_table, weekly_reps_target


def update_rep_item(rev):
    # This function handles all rep-based modes (Daily, Weekly, etc.)
    config = REP_MODES_CONFIG.get(rev.mode_id)
    if not config:
        return  # Not a rep mode we can handle

    hafiz_item = get_hafizs_items(rev.item_id)
    current_date = get_current_date(rev.hafiz_id)

    # Special case: Promote from 'New Memorization' to 'Daily'
    if hafiz_item.mode_id == NEW_MEMORIZATION_MODE_ID:
        hafiz_item.mode_id = DAILY_REPS_MODE_ID

    # Check if the item is ready to graduate
    if get_mode_count(rev.item_id, rev.mode_id) < config["threshold"]:
        # Keep in current mode, just update next review date
        hafiz_item.last_interval = hafiz_item.next_interval
        hafiz_item.next_interval = config["interval"]
        hafiz_item.next_review = add_days_to_date(current_date, config["interval"])
    else:
        # Graduate to the next mode
        hafiz_item.mode_id = config["next_mode_id"]
        if config["next_mode_id"] == FULL_CYCLE_MODE_ID:  # Graduating to Full Cycle
            # Reset intervals for Full Cycle
            hafiz_item.status_id = 1
            hafiz_item.last_interval = hafiz_item.next_interval
            hafiz_item.next_interval = None
            hafiz_item.next_review = None
        else:
            # Graduate to the next rep mode (e.g., Daily -> Weekly)
            next_config = REP_MODES_CONFIG[config["next_mode_id"]]
            hafiz_item.last_interval = hafiz_item.next_interval
            hafiz_item.next_interval = next_config["interval"]
            hafiz_item.next_review = add_days_to_date(
                current_date, next_config["interval"]
            )

    hafizs_items.update(hafiz_item)
