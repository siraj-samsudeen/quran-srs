"""
SRS (Spaced Repetition System) Mode Logic

This module handles the adaptive spaced repetition algorithm for Quran memorization.
SRS mode is triggered when Full Cycle revisions receive Ok or Bad ratings, indicating
the page needs focused reinforcement before returning to regular rotation.

Key concepts:
- Items enter SRS from Full Cycle when they get Ok (0) or Bad (-1) ratings
- Bad ratings start with 3-day interval, Ok ratings with 10-day interval
- Progression uses prime number intervals: [2, 3, 5, 7, 11, ..., 97, 101]
- Rating affects next interval: Bad→shorter, Ok→same, Good→longer
- Items graduate back to Full Cycle when next_interval exceeds 99 days
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

# =============================================================================
# CONSTANTS
# =============================================================================

# Starting intervals when entering SRS mode (based on the rating that triggered entry)
SRS_START_INTERVAL = {
    -1: 3,  # Bad rating -> 3-day interval
    0: 10,  # Ok rating -> 10-day interval
}

# Threshold for graduating back to Full Cycle (when next_interval exceeds this)
SRS_END_INTERVAL = 99

# Prime number sequence for interval progression
# Rating determines movement: Bad→left, Ok→stay, Good→right
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


# =============================================================================
# INTERVAL CALCULATION HELPERS
# =============================================================================


def binary_search_less_than(input_list: list[int], target: int) -> dict:
    """
    Find the largest element in a sorted list that is <= target.

    Uses binary search for O(log n) performance.

    Args:
        input_list: Sorted list of integers (ascending)
        target: Value to search for

    Returns:
        Dict with 'index' and 'value' of the largest element <= target,
        or {'index': None, 'value': None} if no such element exists.
    """
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
    Get the interval options for the next review based on current interval.

    Finds where the target_interval sits in the interval_list and returns
    a triplet [left, current, right] representing the three possible next
    intervals based on rating:
        - Index 0 (left): Used for Bad rating (-1)
        - Index 1 (current): Used for Ok rating (0)
        - Index 2 (right): Used for Good rating (1)

    Args:
        target_interval: Current interval to find in the list
        interval_list: Sorted list of valid intervals (prime numbers)

    Returns:
        List of 3 intervals: [shorter, same, longer]
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


# =============================================================================
# SRS ENTRY (From Full Cycle)
# =============================================================================


def start_srs(item_id: int, auth: int, rating: int) -> None:
    """
    Move an item from Full Cycle into SRS mode.

    Called when a Full Cycle revision receives an Ok or Bad rating,
    indicating the item needs focused reinforcement.

    Args:
        item_id: The item to move to SRS
        auth: The hafiz_id
        rating: The rating that triggered SRS entry (-1=Bad, 0=Ok)
    """
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


# =============================================================================
# SRS PROGRESSION (Next Interval Calculation)
# =============================================================================


def get_actual_interval(item_id: int) -> int | None:
    """
    Calculate the actual number of days since the last review.

    This may differ from the planned interval if the user reviewed
    early or late.

    Args:
        item_id: The item to check

    Returns:
        Number of days since last review, or None if no last_review exists
    """
    hafiz_items_details = get_hafizs_items(item_id)
    current_date = get_current_date(hafiz_items_details.hafiz_id)

    last_review = hafiz_items_details.last_review
    if not last_review:
        return None
    return calculate_days_difference(last_review, current_date)


def apply_rating_penalty(actual_interval: int, rating: int) -> int:
    """
    Apply a penalty to the actual interval based on rating.

    Reduces the effective interval for Ok/Bad ratings to account for
    the struggle, even if the user waited the full interval.

    Multipliers:
        - Good (1): 100% - full credit for waiting
        - Ok (0): 50% - partial credit
        - Bad (-1): 35% - minimal credit

    Args:
        actual_interval: Days since last review
        rating: Review rating (-1, 0, or 1)

    Returns:
        Adjusted interval after applying rating penalty
    """
    rating_multipliers = {1: 1, 0: 0.5, -1: 0.35}
    return round(actual_interval * rating_multipliers[rating])


def get_planned_next_interval(item_id: int) -> int | None:
    """Get the planned next_interval from hafizs_items."""
    return get_hafizs_items(item_id).next_interval


def get_next_interval_based_on_rating(current_interval: int, rating: int) -> int:
    """
    Look up the next interval from the prime sequence based on rating.

    Args:
        current_interval: Current position in the interval sequence
        rating: Review rating (-1=Bad, 0=Ok, 1=Good)

    Returns:
        Next interval from the prime sequence
    """
    rating_intervals = get_interval_triplet(
        target_interval=current_interval,
        interval_list=SRS_INTERVALS,
    )
    # Convert rating (-1, 0, 1) to index (0, 1, 2)
    return rating_intervals[rating + 1]


def get_next_interval(item_id: int, rating: int) -> int | None:
    """
    Calculate the next SRS interval for an item based on its rating.

    This is the main interval calculation that considers both:
    1. Actual interval (days since last review) with rating penalty applied
    2. Planned interval (what was scheduled)

    The larger of these two becomes the "current interval", which is then
    used to look up the next interval from the prime sequence based on rating.

    Args:
        item_id: The item being reviewed
        rating: Review rating (-1=Bad, 0=Ok, 1=Good)

    Returns:
        Next interval in days, or None if calculation fails
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


# =============================================================================
# SRS UPDATE & GRADUATION (Called on Close Date)
# =============================================================================


def update_hafiz_item_for_srs(rev) -> None:
    """
    Update hafizs_items after an SRS revision, potentially graduating to Full Cycle.

    Called during Close Date processing for each SRS revision. Calculates the next
    interval based on rating, then either:
    1. Schedules the next SRS review (if next_interval <= 99)
    2. Graduates the item back to Full Cycle (if next_interval > 99)

    Args:
        rev: The revision record being processed
    """
    hafiz_items_details = get_hafizs_items(rev.item_id)
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
    """
    Move items to SRS mode based on today's Full Cycle revision ratings.

    Called during Close Date processing. Scans today's Full Cycle revisions
    and moves items with Ok or Bad ratings into SRS mode.

    Rating-based starting intervals:
        - Bad (-1): 3-day starting interval
        - Ok (0): 10-day starting interval
        - Good (1): Stays in Full Cycle (no SRS entry)

    Args:
        auth: The hafiz_id to process
    """
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
