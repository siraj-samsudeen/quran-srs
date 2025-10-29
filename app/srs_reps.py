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
SRS_START_INTERVAL = 7
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


def start_srs(item_id: int, auth):
    current_date = get_current_date(auth)
    next_interval = SRS_START_INTERVAL
    next_review_date = add_days_to_date(current_date, next_interval)

    current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")
    if current_hafiz_items:
        current_hafiz_items = current_hafiz_items[0]
        current_hafiz_items.mode_id = SRS_MODE_ID
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


def recalculate_intervals_on_srs_records(item_id: int, current_date: str):
    """
    Recalculates SRS (Spaced Repetition System) intervals for a specific item based on its revision history.
        - Handles initial state when no revision records are found
        - Calculates intervals based on previous revision dates and ratings
        - Updates item's next review interval and date dynamically
    """
    hafiz_item_details = get_hafizs_items(item_id)
    srs_start_date = hafiz_item_details.srs_start_date

    items_rev_data = revisions(
        where=f"item_id = {item_id} AND mode_id = {SRS_MODE_ID} AND revision_date >= '{srs_start_date}'",
        order_by="revision_date ASC",
    )

    # If no records, reset to initial state (Either deleted all records or not even started)
    if not items_rev_data:
        hafiz_item_details.next_interval = SRS_START_INTERVAL
        hafiz_item_details.next_review = add_days_to_date(
            srs_start_date, SRS_START_INTERVAL
        )
        hafiz_item_details.last_interval = None
        hafiz_item_details.current_interval = calculate_days_difference(
            srs_start_date, current_date
        )
        hafizs_items.update(hafiz_item_details)
        return None

    previous_date = srs_start_date
    # Here we are starting the recalculation from the first records last_interval
    # as the SRS_START_INTERVAL may change in future
    current_interval_position = items_rev_data[0].last_interval

    for rev in items_rev_data:
        current_revision_date = rev.revision_date
        current_interval = calculate_days_difference(
            previous_date, current_revision_date
        )
        last_interval = current_interval_position

        # "good": move forward in sequence
        # "ok": stay at same position
        # "bad": move backward in sequence
        rating_intervals = get_interval_triplet(
            target_interval=last_interval, interval_list=SRS_INTERVALS
        )
        calculated_next_interval = rating_intervals[rev.rating + 1]

        if calculated_next_interval > SRS_END_INTERVAL:
            # Graduation logic
            next_interval = None

            data_to_update = {
                "last_interval": last_interval,
                "current_interval": current_interval,
                "next_interval": next_interval,
            }
            revisions.update(data_to_update, rev.id)

            final_data = {
                "last_review": current_revision_date,
                "last_interval": last_interval,
                "current_interval": calculate_days_difference(
                    current_revision_date, current_date
                ),
                "next_interval": next_interval,
                "next_review": None,
            }
            hafizs_items.update(final_data, hafiz_item_details.id)
            break  # Exit - no more processing needed
        else:
            # Normal progression
            next_interval = calculated_next_interval

            data_to_update = {
                "last_interval": last_interval,
                "current_interval": current_interval,
                "next_interval": next_interval,
            }
            revisions.update(data_to_update, rev.id)

            # Handle final revision if this is the last one
            if rev.id == items_rev_data[-1].id:
                final_data = {
                    "last_review": current_revision_date,
                    "last_interval": last_interval,
                    "current_interval": calculate_days_difference(
                        current_revision_date, current_date
                    ),
                    "next_interval": next_interval,
                    "next_review": add_days_to_date(
                        current_revision_date, next_interval
                    ),
                }
                hafizs_items.update(final_data, hafiz_item_details.id)
                break

        # Prepare for the next iteration
        previous_date = current_revision_date
        current_interval_position = next_interval


def update_hafiz_item_for_srs(rev):
    hafiz_items_details = get_hafizs_items(rev.item_id)
    current_date = get_current_date(rev.hafiz_id)
    next_interval = get_next_interval(item_id=rev.item_id, rating=rev.rating)

    hafiz_items_details.last_interval = hafiz_items_details.next_interval
    if SRS_END_INTERVAL > next_interval:
        hafiz_items_details.next_interval = next_interval
        hafiz_items_details.next_review = add_days_to_date(current_date, next_interval)
    else:
        hafiz_items_details.mode_id = FULL_CYCLE_MODE_ID
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


def start_srs_for_bad_streak_items(auth):
    current_date = get_current_date(auth)
    # Get the full-cycle today revised pages which have 1 or more bad streak
    qry = f"""
        SELECT revisions.item_id FROM revisions
        LEFT JOIN hafizs_items ON revisions.item_id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
        WHERE hafizs_items.bad_streak >= 1 AND revisions.mode_id = {FULL_CYCLE_MODE_ID} AND revisions.hafiz_id = {auth} AND revisions.revision_date = '{current_date}'
    """
    for items in db.q(qry):
        start_srs(items["item_id"], auth)


def display_srs_pages_recorded_today(auth):
    current_date = get_current_date(auth)

    # List all the records that are recorded today with the interval details as a table
    srs_records = db.q(
        f"""
    SELECT revisions.item_id, hafizs_items.next_interval as previous_interval, revisions.rating FROM revisions 
    LEFT JOIN hafizs_items ON hafizs_items.item_id = revisions.item_id AND hafizs_items.hafiz_id = revisions.hafiz_id
    WHERE revisions.revision_date = '{current_date}' AND revisions.mode_id = {SRS_MODE_ID} AND revisions.hafiz_id = {auth}
    """
    )

    def render_srs_records(srs_record):
        next_interval = get_next_interval(srs_record["item_id"], srs_record["rating"])
        if next_interval > SRS_END_INTERVAL:
            next_interval = "Graduation"
        return Tr(
            Td(get_page_description(srs_record["item_id"])),
            Td(srs_record["previous_interval"]),
            Td(get_actual_interval(srs_record["item_id"])),
            Td(next_interval),
            Td(render_rating(srs_record["rating"])),
        )

    srs_records_table = Table(
        Thead(
            Tr(
                Th("Item Id"),
                Th("Last Interval"),
                Th("Actual Interval"),
                Th("Next Interval"),
                Th("Rating"),
            )
        ),
        Tbody(*map(render_srs_records, srs_records)),
    )

    # Confirmation and cancel buttons
    action_buttons = DivLAligned(
        Button(
            "Confirm",
            hx_post="close_date",
            hx_target="body",
            hx_push_url="true",
            hx_disabled_elt="this",
            cls=(ButtonT.primary, "p-2"),
        ),
        Button(
            "Cancel",
            onclick="history.back()",
            cls=(ButtonT.default, "p-2"),
        ),
    )

    return Div(
        H2("SRS Records"),
        srs_records_table,
        action_buttons,
        cls="uk-overflow-auto space-y-2",
    )
