"""
Fixed Repetition Modes Module

This module handles the four fixed-interval repetition modes:
- Daily Reps (DR): 1-day interval, 7 repetitions → graduates to Weekly
- Weekly Reps (WR): 7-day interval, 7 repetitions → graduates to Fortnightly
- Fortnightly Reps (FR): 14-day interval, 7 repetitions → graduates to Monthly
- Monthly Reps (MR): 30-day interval, 7 repetitions → graduates to Full Cycle

All modes share the same graduation logic, differing only in interval duration.
The REP_MODES_CONFIG dictionary provides a data-driven approach to handle all modes uniformly.

Related modules:
- common_function.py: MODE_PREDICATES for filtering items in summary tables
- srs_reps.py: SRS mode uses adaptive intervals (fundamentally different)
"""
from app.common_function import *
from constants import DEFAULT_REP_COUNTS

# Maps mode code to the corresponding custom threshold column name in hafizs_items
MODE_TO_THRESHOLD_COLUMN = {
    DAILY_REPS_MODE_CODE: "custom_daily_threshold",
    WEEKLY_REPS_MODE_CODE: "custom_weekly_threshold",
    FORTNIGHTLY_REPS_MODE_CODE: "custom_fortnightly_threshold",
    MONTHLY_REPS_MODE_CODE: "custom_monthly_threshold",
}

REP_MODES_CONFIG = {
    DAILY_REPS_MODE_CODE: {
        "interval": 1,
        "threshold": 7,
        "next_mode_code": WEEKLY_REPS_MODE_CODE,
    },  # Daily -> Weekly
    WEEKLY_REPS_MODE_CODE: {
        "interval": 7,
        "threshold": 7,
        "next_mode_code": FORTNIGHTLY_REPS_MODE_CODE,
    },  # Weekly -> Fortnightly
    FORTNIGHTLY_REPS_MODE_CODE: {
        "interval": 14,
        "threshold": 7,
        "next_mode_code": MONTHLY_REPS_MODE_CODE,
    },  # Fortnightly -> Monthly
    MONTHLY_REPS_MODE_CODE: {
        "interval": 30,
        "threshold": 7,
        "next_mode_code": FULL_CYCLE_MODE_CODE,
    },  # Monthly -> Full Cycle
}


def get_threshold_for_mode(hafiz_item, mode_code):
    """
    Get the repetition threshold for a given mode, using custom threshold if set.

    Priority: custom threshold > DEFAULT_REP_COUNTS > REP_MODES_CONFIG default
    """
    column_name = MODE_TO_THRESHOLD_COLUMN.get(mode_code)
    if column_name:
        custom_threshold = getattr(hafiz_item, column_name, None)
        if custom_threshold is not None:
            return custom_threshold
    return DEFAULT_REP_COUNTS.get(mode_code, REP_MODES_CONFIG[mode_code]["threshold"])


def set_next_review(hafiz_item, interval, current_date):
    hafiz_item.next_interval = interval
    hafiz_item.next_review = add_days_to_date(current_date, interval)


def update_rep_item(rev):
    """
    Process a revision in any rep mode (Daily/Weekly/Fortnightly/Monthly).

    Logic:
    1. Check if item has completed threshold repetitions in current mode
    2. If not complete: schedule next review with same interval
    3. If complete: graduate to next mode with its interval (or Full Cycle)

    This single function handles all rep modes uniformly using REP_MODES_CONFIG.
    """
    config = REP_MODES_CONFIG.get(rev.mode_code)
    if not config:
        return

    hafiz_item = get_hafizs_items(rev.item_id)
    if hafiz_item is None:
        return
    current_date = get_current_date(rev.hafiz_id)

    # Preserve current interval before updating (for history tracking)
    hafiz_item.last_interval = hafiz_item.next_interval

    threshold = get_threshold_for_mode(hafiz_item, rev.mode_code)
    if get_mode_count(rev.item_id, rev.mode_code) < threshold:
        # Not yet at threshold: stay in current mode, schedule next review
        set_next_review(hafiz_item, config["interval"], current_date)
    else:
        # Reached threshold: graduate to next mode
        hafiz_item.mode_code = config["next_mode_code"]
        if config["next_mode_code"] == FULL_CYCLE_MODE_CODE:
            # Final graduation: clear scheduling fields for Full Cycle
            hafiz_item.memorized = True
            hafiz_item.next_interval = None
            hafiz_item.next_review = None
        else:
            # Graduate to next rep mode: use that mode's interval
            next_config = REP_MODES_CONFIG[config["next_mode_code"]]
            set_next_review(hafiz_item, next_config["interval"], current_date)

    hafizs_items.update(hafiz_item)
