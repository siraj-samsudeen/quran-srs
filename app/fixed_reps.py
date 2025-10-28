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


def set_next_review(hafiz_item, interval, current_date):
    """Set next interval and review date for a hafiz item."""
    hafiz_item.next_interval = interval
    hafiz_item.next_review = add_days_to_date(current_date, interval)


def get_reps_table_with_target(mode_ids, route, auth):
    """Helper to get table and target count for rep modes."""
    table, items = make_summary_table(
        mode_ids=[str(mid) for mid in mode_ids],
        route=route,
        auth=auth,
    )
    target = get_page_count(item_ids=items)
    return table, target


def get_daily_reps_table(auth):
    return get_reps_table_with_target(
        [NEW_MEMORIZATION_MODE_ID, DAILY_REPS_MODE_ID], "daily_reps", auth
    )


def get_weekly_reps_table(auth):
    # Include mode_id=1 as well so that graduated watch list items are included
    return get_reps_table_with_target(
        [WEEKLY_REPS_MODE_ID, FULL_CYCLE_MODE_ID], "weekly_reps", auth
    )


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

    hafiz_item.last_interval = hafiz_item.next_interval

    # Check if the item is ready to graduate
    if get_mode_count(rev.item_id, rev.mode_id) < config["threshold"]:
        # Keep in current mode, just update next review date
        set_next_review(hafiz_item, config["interval"], current_date)
    else:
        # Graduate to the next mode
        hafiz_item.mode_id = config["next_mode_id"]
        if config["next_mode_id"] == FULL_CYCLE_MODE_ID:
            # Reset intervals for Full Cycle
            hafiz_item.status_id = STATUS_MEMORIZED_ID
            hafiz_item.next_interval = None
            hafiz_item.next_review = None
        else:
            # Graduate to the next rep mode (e.g., Daily -> Weekly)
            next_config = REP_MODES_CONFIG[config["next_mode_id"]]
            set_next_review(hafiz_item, next_config["interval"], current_date)

    hafizs_items.update(hafiz_item)
