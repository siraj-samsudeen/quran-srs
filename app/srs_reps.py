"""
SRS (Spaced Repetition System) Mode Logic

This module handles the adaptive spaced repetition algorithm, which is fundamentally
different from fixed-interval rep modes (Daily/Weekly/Fortnightly/Monthly).

Key Differences from Fixed Reps:
- SRS uses prime number intervals that adapt based on performance ratings
- Fixed rep modes use constant intervals (1/7/14/30 days)
- SRS has no threshold-based graduation; it graduates when interval exceeds 99 days
- Fixed rep modes graduate after 7 successful repetitions

SRS Entry:
- Items enter SRS from Full Cycle when they get Ok (0) or Bad (-1) ratings
- Bad rating → 3-day starting interval
- Ok rating → 10-day starting interval

SRS Progression:
- Rating affects next interval: Bad→shorter (left in prime sequence),
  Ok→same, Good→longer (right in prime sequence)

The separation between SRS and fixed reps (fixed_reps.py) is intentional and should
be maintained - they solve fundamentally different problems.
"""

from constants import *
from database import (
    db,
    hafizs_items,
    revisions,
)
from utils import *
from fasthtml.common import *
from monsterui.all import *
from app.common_function import (
    get_hafizs_items,
    get_current_date,
    get_page_description,
    render_rating,
)

# Starting intervals when entering SRS mode
SRS_START_INTERVAL = {
    -1: 3,  # Bad rating -> 3-day interval
    0: 10,  # Ok rating -> 10-day interval
}

SRS_END_INTERVAL = 99  # Graduate back to Full Cycle when exceeded

# Prime number sequence for interval progression (Bad→left, Ok→stay, Good→right)
SRS_INTERVALS = [
    2,
    3,
    5,
    7,
    11,
    13,
    17,
    19,
    23,
    29,
    31,
    37,
    41,
    43,
    47,
    53,
    59,
    61,
    67,
    71,
    73,
    79,
    83,
    89,
    97,
    101,
]


def binary_search_less_than(input_list: list[int], target: int) -> dict:
    """Find the largest element in a sorted list that is <= target."""
    left = 0
    right = len(input_list) - 1
    possible_answer = {"index": None, "value": None}

    while left <= right:
        middle = (left + right) // 2
        middle_value = input_list[middle]

        if middle_value <= target:
            left = middle + 1
            possible_answer["index"] = middle
            possible_answer["value"] = middle_value
        else:
            right = middle - 1

    return possible_answer


def get_interval_triplet(target_interval: int, interval_list: list[int]) -> list[int]:
    """
    Return [left, current, right] intervals for rating-based progression.
    Index maps to rating+1: Bad(-1)→0, Ok(0)→1, Good(1)→2.
    """
    result = binary_search_less_than(input_list=interval_list, target=target_interval)
    i = result["index"]

    # If no match found (target < first element), start at index 0
    if i is None:
        i = 0

    # Build triplet with bounds checking
    left = interval_list[i - 1] if i > 0 else interval_list[i]
    right = interval_list[i + 1] if i < len(interval_list) - 1 else interval_list[i]
    return [left, interval_list[i], right]


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
        hafizs_items.update(current_hafiz_items)


def get_actual_interval(item_id: int) -> int | None:
    """Return days since last review (may differ from planned if reviewed early/late)."""
    hafiz_items_details = get_hafizs_items(item_id)
    if hafiz_items_details is None:
        return None
    current_date = get_current_date(hafiz_items_details.hafiz_id)

    last_review = hafiz_items_details.last_review
    if not last_review:
        return None
    return calculate_days_difference(last_review, current_date)


def apply_rating_penalty(actual_interval: int, rating: int) -> int:
    """Apply rating penalty: Good=100%, Ok=50%, Bad=35% of actual interval."""
    rating_multipliers = {1: 1, 0: 0.5, -1: 0.35}
    return round(actual_interval * rating_multipliers[rating])


def get_planned_next_interval(item_id: int) -> int | None:
    hafiz_items_details = get_hafizs_items(item_id)
    if hafiz_items_details is None:
        return None
    return hafiz_items_details.next_interval


def get_next_interval_based_on_rating(current_interval: int, rating: int) -> int:
    rating_intervals = get_interval_triplet(
        target_interval=current_interval,
        interval_list=SRS_INTERVALS,
    )
    # Convert rating (-1, 0, 1) to index (0, 1, 2)
    return rating_intervals[rating + 1]


def get_next_interval(item_id: int, rating: int) -> int | None:
    """
    Calculate next SRS interval using max(planned, adjusted_actual) as base,
    then look up next interval from prime sequence based on rating.
    """
    actual_interval = get_actual_interval(item_id)
    if not actual_interval:
        return None

    # Apply rating-based penalty to actual interval
    adjusted_actual = apply_rating_penalty(actual_interval, rating)

    planned_interval = get_planned_next_interval(item_id)
    if not planned_interval:
        return None

    # Use whichever interval is larger as the base for progression
    current_interval = max(planned_interval, adjusted_actual)

    return get_next_interval_based_on_rating(current_interval, rating)


def update_hafiz_item_for_srs(rev) -> None:
    """Process SRS revision: schedule next review or graduate to Full Cycle if interval > 99."""
    hafiz_items_details = get_hafizs_items(rev.item_id)
    if hafiz_items_details is None:
        return  # Skip if no hafiz_items record exists
    current_date = get_current_date(rev.hafiz_id)
    next_interval = get_next_interval(item_id=rev.item_id, rating=rev.rating)

    # Save current interval as last_interval before updating
    hafiz_items_details.last_interval = hafiz_items_details.next_interval

    if next_interval <= SRS_END_INTERVAL:
        # Stay in SRS: schedule next review
        hafiz_items_details.next_interval = next_interval
        hafiz_items_details.next_review = add_days_to_date(current_date, next_interval)
    else:
        # Graduate to Full Cycle: clear SRS fields
        hafiz_items_details.mode_code = FULL_CYCLE_MODE_CODE
        hafiz_items_details.memorized = True
        hafiz_items_details.last_interval = calculate_days_difference(
            hafiz_items_details.last_review, current_date
        )
        hafiz_items_details.next_interval = None
        hafiz_items_details.next_review = None
        hafiz_items_details.srs_start_date = None

    hafizs_items.update(hafiz_items_details)

    # Also store next_interval on the revision record for history
    rev.next_interval = next_interval
    revisions.update(rev, rev.id)


def start_srs_for_ok_and_bad_rating(auth: int) -> None:
    """Called during Close Date: move today's Ok/Bad Full Cycle items into SRS."""
    current_date = get_current_date(auth)

    # Build query in readable stages
    query_base = """
        SELECT revisions.item_id, revisions.rating
        FROM revisions
        LEFT JOIN hafizs_items
            ON revisions.item_id = hafizs_items.item_id
            AND hafizs_items.hafiz_id = revisions.hafiz_id
    """

    # Build WHERE conditions
    conditions = [
        # Only process today's revisions (during Close Date)
        f"revisions.revision_date = '{current_date}'",
        # Filter to current hafiz
        f"revisions.hafiz_id = {auth}",
        # Only Ok (0) or Bad (-1) ratings trigger SRS entry
        "revisions.rating IN (-1, 0)",
        # The revision was performed in Full Cycle mode
        f"revisions.mode_code = '{FULL_CYCLE_MODE_CODE}'",
        # The item is currently still in Full Cycle mode (prevents re-processing items already in SRS)
        f"hafizs_items.mode_code = '{FULL_CYCLE_MODE_CODE}'",
    ]
    where_clause = "WHERE " + " AND ".join(conditions)

    # Assemble final query
    query = f"{query_base} {where_clause}"

    # Execute and process results
    for item in db.q(query):
        start_srs(item["item_id"], auth, rating=item["rating"])
