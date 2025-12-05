"""
SRS (Spaced Repetition System) Mode Logic

This module handles the adaptive spaced repetition algorithm for Quran memorization.
SRS mode is triggered when Full Cycle revisions receive Ok or Bad ratings, indicating
the page needs focused reinforcement before returning to regular rotation.

Key concepts:
- Items enter SRS from Full Cycle when they get Ok (0) or Bad (-1) ratings
- Rating affects next interval: Bad→shorter, Ok→same/capped, Good→longer
- Graduation: After consecutive Good ratings (not based on interval threshold)
"""

from globals import *
from utils import *
from fasthtml.common import *
from monsterui.all import *
from app.common_function import (
    get_hafizs_items,
    get_current_date,
    get_page_description,
    render_rating,
)
from app.srs_interval_calc import (
    SRS_START_INTERVAL,
    get_base_interval,
    calculate_next_interval,
    should_graduate,
    should_reschedule_only,
)


def start_srs(item_id: int, auth: int, rating: int) -> None:
    """Move an item from Full Cycle into SRS mode."""
    current_date = get_current_date(auth)
    next_interval = SRS_START_INTERVAL[rating]
    next_review_date = add_days_to_date(current_date, next_interval)

    current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")
    if current_hafiz_items:
        current_hafiz_items = current_hafiz_items[0]
        current_hafiz_items.mode_code = SRS_MODE_CODE
        current_hafiz_items.next_interval = next_interval
        current_hafiz_items.srs_start_date = current_date
        current_hafiz_items.next_review = next_review_date
        # Reset streaks on SRS entry
        current_hafiz_items.good_streak = 0
        current_hafiz_items.bad_streak = 1 if rating == -1 else 0
        hafizs_items.update(current_hafiz_items)


def get_actual_interval(item_id: int) -> int | None:
    """Return days since last review (may differ from planned if reviewed early/late)."""
    hafiz_items_details = get_hafizs_items(item_id)
    current_date = get_current_date(hafiz_items_details.hafiz_id)

    last_review = hafiz_items_details.last_review
    if not last_review:
        return None
    return calculate_days_difference(last_review, current_date)


def get_planned_next_interval(item_id: int) -> int | None:
    """Get the planned next interval from hafizs_items."""
    return get_hafizs_items(item_id).next_interval


def update_hafiz_item_for_srs(rev) -> None:
    """
    Process SRS revision: update streaks, schedule next review, or graduate.

    Handles:
    - Early + Good: Reschedule only (push forward without changing interval)
    - Graduation: When good_streak reaches threshold after this review
    - Normal: Calculate new interval based on rating and streaks
    """
    hafiz_item = get_hafizs_items(rev.item_id)
    current_date = get_current_date(rev.hafiz_id)
    actual = get_actual_interval(rev.item_id)
    planned = hafiz_item.next_interval

    # Save current interval as last_interval before any updates
    hafiz_item.last_interval = hafiz_item.next_interval

    # Update streaks based on rating (this affects graduation check)
    if rev.rating == 1:  # Good
        hafiz_item.good_streak = (hafiz_item.good_streak or 0) + 1
        hafiz_item.bad_streak = 0
    elif rev.rating == -1:  # Bad
        hafiz_item.bad_streak = (hafiz_item.bad_streak or 0) + 1
        hafiz_item.good_streak = 0
    else:  # Ok
        hafiz_item.good_streak = 0
        hafiz_item.bad_streak = 0

    # Check for early + Good (reschedule only)
    if actual and planned and should_reschedule_only(actual, planned, rev.rating):
        # Just push the review forward, keep the same interval
        hafiz_item.next_review = add_days_to_date(current_date, hafiz_item.next_interval)
        hafizs_items.update(hafiz_item)
        # Store None on revision to indicate reschedule-only
        rev.next_interval = hafiz_item.next_interval
        revisions.update(rev, rev.id)
        return

    # Check for graduation (consecutive Good streak)
    if should_graduate(hafiz_item.good_streak):
        # Graduate to Full Cycle
        hafiz_item.mode_code = FULL_CYCLE_MODE_CODE
        hafiz_item.memorized = True
        hafiz_item.last_interval = calculate_days_difference(
            hafiz_item.last_review, current_date
        ) if hafiz_item.last_review else None
        hafiz_item.next_interval = None
        hafiz_item.next_review = None
        hafiz_item.srs_start_date = None
        hafizs_items.update(hafiz_item)
        # Store graduation marker on revision
        rev.next_interval = None
        revisions.update(rev, rev.id)
        return

    # Normal case: calculate next interval
    base = get_base_interval(planned or 0, actual or 0, rev.rating)
    if base is None:
        base = planned or 3  # Fallback

    next_interval = calculate_next_interval(
        base,
        rev.rating,
        hafiz_item.good_streak,
        hafiz_item.bad_streak
    )

    # Update hafiz_item with new interval
    hafiz_item.next_interval = next_interval
    hafiz_item.next_review = add_days_to_date(current_date, next_interval)
    hafizs_items.update(hafiz_item)

    # Store next_interval on the revision record for history
    rev.next_interval = next_interval
    revisions.update(rev, rev.id)


def start_srs_for_ok_and_bad_rating(auth: int) -> None:
    """Called during Close Date: move today's Ok/Bad Full Cycle items into SRS."""
    current_date = get_current_date(auth)

    query_base = """
        SELECT revisions.item_id, revisions.rating
        FROM revisions
        LEFT JOIN hafizs_items
            ON revisions.item_id = hafizs_items.item_id
            AND hafizs_items.hafiz_id = revisions.hafiz_id
    """

    conditions = [
        f"revisions.revision_date = '{current_date}'",
        f"revisions.hafiz_id = {auth}",
        "revisions.rating IN (-1, 0)",
        f"revisions.mode_code = '{FULL_CYCLE_MODE_CODE}'",
        f"hafizs_items.mode_code = '{FULL_CYCLE_MODE_CODE}'",
    ]
    where_clause = "WHERE " + " AND ".join(conditions)

    query = f"{query_base} {where_clause}"

    for item in db.q(query):
        start_srs(item["item_id"], auth, rating=item["rating"])
