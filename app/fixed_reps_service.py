from .utils import add_days_to_date
from .common_model import get_hafizs_items, get_current_date, get_mode_count
from .globals import (
    hafizs_items,
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
)

REP_MODES_CONFIG = {
    DAILY_REPS_MODE_CODE: {
        "interval": 1,
        "threshold": 7,
        "next_mode_code": WEEKLY_REPS_MODE_CODE,
    },  # Daily -> Weekly
    WEEKLY_REPS_MODE_CODE: {
        "interval": 7,
        "threshold": 7,
        "next_mode_code": FULL_CYCLE_MODE_CODE,
    },  # Weekly -> Full Cycle
}


def set_next_review(hafiz_item, interval, current_date):
    hafiz_item.next_interval = interval
    hafiz_item.next_review = add_days_to_date(current_date, interval)


def update_rep_item(rev):
    # This function handles all rep-based modes (Daily, Weekly, etc.)
    config = REP_MODES_CONFIG.get(rev.mode_code)
    if not config:
        return  # Not a rep mode we can handle

    hafiz_item = get_hafizs_items(rev.item_id)
    current_date = get_current_date(rev.hafiz_id)

    hafiz_item.last_interval = hafiz_item.next_interval

    # Check if the item is ready to graduate
    if get_mode_count(rev.item_id, rev.mode_code) < config["threshold"]:
        # Keep in current mode, just update next review date
        set_next_review(hafiz_item, config["interval"], current_date)
    else:
        # Graduate to the next mode
        hafiz_item.mode_code = config["next_mode_code"]
        if config["next_mode_code"] == FULL_CYCLE_MODE_CODE:
            # Reset intervals for Full Cycle
            hafiz_item.memorized = True
            hafiz_item.next_interval = None
            hafiz_item.next_review = None
        else:
            # Graduate to the next rep mode (e.g., Daily -> Weekly)
            next_config = REP_MODES_CONFIG[config["next_mode_code"]]
            set_next_review(hafiz_item, next_config["interval"], current_date)

    hafizs_items.update(hafiz_item)
