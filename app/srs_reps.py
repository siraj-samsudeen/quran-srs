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

# SRS Intervals
SRS_START_INTERVAL = {
    -1: 3,  # Bad rating -> 3-day interval
    0: 10,  # Ok rating -> 10-day interval
}
SRS_END_INTERVAL = 99
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


## SRS specific utils ##
def binary_search_less_than(input_list: list[int], target: int) -> int:
    # initial values
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


# This function is only used for getting the intervals for the rating in srs mode
def get_interval_triplet(target_interval, interval_list):
    result = binary_search_less_than(input_list=interval_list, target=target_interval)
    i = result["index"]

    # If the index is None then, it only means that the current interval is less than the first element
    # in which case we assign the first element index
    if i is None:
        i = 0

    left = interval_list[i - 1] if i > 0 else interval_list[i]
    right = interval_list[i + 1] if i < len(interval_list) - 1 else interval_list[i]
    return [left, interval_list[i], right]


## END ##


def start_srs(item_id: int, auth, rating: int):
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


def get_actual_interval(item_id):
    hafiz_items_details = get_hafizs_items(item_id)
    current_date = get_current_date(hafiz_items_details.hafiz_id)

    last_review = hafiz_items_details.last_review
    if not last_review:
        return None
    return calculate_days_difference(last_review, current_date)


def update_interval_based_on_rating(actual_interval, rating):
    # Good -> 100% of the actual interval
    # Ok -> 50% of the actual interval
    # Bad -> 35% of the actual interval
    rating_multipliers = {1: 1, 0: 0.5, -1: 0.35}
    return round(actual_interval * rating_multipliers[rating])


def get_planned_next_interval(item_id):
    return get_hafizs_items(item_id).next_interval


def get_next_interval_based_on_rating(current_interval, rating):
    rating_intervals = get_interval_triplet(
        target_interval=current_interval,
        interval_list=SRS_INTERVALS,
    )
    return rating_intervals[rating + 1]


####################### SRS common function #######################


def get_next_interval(item_id, rating):
    actual_interval = get_actual_interval(item_id)
    if not actual_interval:
        return None

    actual_interval = update_interval_based_on_rating(actual_interval, rating)

    planned_interval = get_planned_next_interval(item_id)
    if not planned_interval:
        return None

    current_interval = max(planned_interval, actual_interval)

    return get_next_interval_based_on_rating(current_interval, rating)


def update_hafiz_item_for_srs(rev):
    hafiz_items_details = get_hafizs_items(rev.item_id)
    current_date = get_current_date(rev.hafiz_id)
    next_interval = get_next_interval(item_id=rev.item_id, rating=rev.rating)

    hafiz_items_details.last_interval = hafiz_items_details.next_interval
    if SRS_END_INTERVAL > next_interval:
        hafiz_items_details.next_interval = next_interval
        hafiz_items_details.next_review = add_days_to_date(current_date, next_interval)
    else:
        hafiz_items_details.mode_code = FULL_CYCLE_MODE_CODE
        hafiz_items_details.memorized = True
        hafiz_items_details.last_interval = calculate_days_difference(
            hafiz_items_details.last_review, current_date
        )
        hafiz_items_details.next_interval = None
        hafiz_items_details.next_review = None
        hafiz_items_details.srs_start_date = None

    hafizs_items.update(hafiz_items_details)

    # Update the next_interval of the revision record
    rev.next_interval = next_interval
    revisions.update(rev, rev.id)


def start_srs_for_ok_and_bad_rating(auth):
    """
    Move items to SRS mode based on today's revision ratings.

    Logic:
    - Bad rating (-1): Move to SRS with 3-day starting interval
    - Ok rating (0): Move to SRS with 10-day starting interval
    - Good rating (1): Stay in Full Cycle (no SRS entry)
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
