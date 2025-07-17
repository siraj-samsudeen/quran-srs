from fasthtml.common import *
import fasthtml.common as fh
from monsterui.all import *
from utils import *
import pandas as pd
from io import BytesIO
from collections import defaultdict
import time
from datetime import datetime

RATING_MAP = {"1": "✅ Good", "0": "😄 Ok", "-1": "❌ Bad"}
OPTION_MAP = {
    "role": ["hafiz", "parent", "teacher", "parent_hafiz"],
    "age_group": ["child", "teen", "adult"],
    "relationship": ["self", "parent", "teacher", "sibling"],
}
STATUS_OPTIONS = ["Memorized", "Newly Memorized", "Not Memorized"]
DEFAULT_RATINGS = {
    "new_memorization": 1,
}
DB_PATH = "data/quran_v9.db"

# This function will handle table creation and migration using fastmigrate
create_and_migrate_db(DB_PATH)

db = database(DB_PATH)
tables = db.t
(
    revisions,
    hafizs,
    users,
    hafizs_users,
    plans,
    modes,
    pages,
    surahs,
    items,
    mushafs,
    hafizs_items,
    srs_booster_pack,
) = (
    tables.revisions,
    tables.hafizs,
    tables.users,
    tables.hafizs_users,
    tables.plans,
    tables.modes,
    tables.pages,
    tables.surahs,
    tables.items,
    tables.mushafs,
    tables.hafizs_items,
    tables.srs_booster_pack,
)
(
    Revision,
    Hafiz,
    User,
    Hafiz_Users,
    Plan,
    Mode,
    Page,
    Item,
    Surah,
    Mushaf,
    Hafiz_Items,
    Srs_Booster_Pack,
) = (
    revisions.dataclass(),
    hafizs.dataclass(),
    users.dataclass(),
    hafizs_users.dataclass(),
    plans.dataclass(),
    modes.dataclass(),
    pages.dataclass(),
    items.dataclass(),
    surahs.dataclass(),
    mushafs.dataclass(),
    hafizs_items.dataclass(),
    srs_booster_pack.dataclass(),
)


hyperscript_header = Script(src="https://unpkg.com/hyperscript.org@0.9.14")
alpinejs_header = Script(
    src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js", defer=True
)


def before(req, sess):
    user_auth = req.scope["user_auth"] = sess.get("user_auth", None)
    if not user_auth:
        return RedirectResponse("/login", status_code=303)
    auth = req.scope["auth"] = sess.get("auth", None)
    if not auth:
        return RedirectResponse("/hafiz_selection", status_code=303)
    revisions.xtra(hafiz_id=auth)
    hafizs_items.xtra(hafiz_id=auth)


bware = Beforeware(before, skip=["/hafiz_selection", "/login", "/logout", "/add_hafiz"])

app, rt = fast_app(
    before=bware,
    hdrs=(Theme.blue.headers(), hyperscript_header, alpinejs_header),
    bodykw={"hx-boost": "true"},
)


def recalculate_intervals_on_srs_records(item_id: int, current_date: str):
    """
    Recalculates SRS (Spaced Repetition System) intervals for a specific item based on its revision history.

    Args:
        item_id (int): The unique identifier of the item being processed.
        current_date (str): The current date used for interval calculations.

    Returns:
        None: Updates the item's SRS intervals in the database, or returns None if no revision records exist.

    Notes:
        - Handles initial state when no revision records are found
        - Calculates intervals based on previous revision dates and ratings
        - Updates item's next review interval and date dynamically
    """
    hafiz_item_details = get_hafizs_items(item_id)
    srs_start_date = hafiz_item_details.srs_start_date

    # Here we are taking the start_interval
    # as we want the start_interval as the starting point, when looping through all the records
    booster_id = hafiz_item_details.srs_booster_pack_id
    srs_pack_details = srs_booster_pack[booster_id]
    start_interval = srs_pack_details.start_interval
    end_interval = srs_pack_details.end_interval

    items_rev_data = revisions(
        where=f"item_id = {item_id} AND mode_id = 5 AND revision_date >= '{srs_start_date}'",
        order_by="revision_date ASC",
    )

    # If no records, reset to initial state (Either deleted all records or not even started)
    if not items_rev_data:
        hafiz_item_details.next_interval = start_interval
        hafiz_item_details.next_review = add_days_to_date(
            srs_start_date, start_interval
        )
        hafiz_item_details.last_interval = None
        hafiz_item_details.current_interval = calculate_days_difference(
            srs_start_date, current_date
        )
        hafizs_items.update(hafiz_item_details)
        return None

    intervals = get_srs_interval_list(item_id)
    previous_date = srs_start_date
    current_interval_position = start_interval

    for rev in items_rev_data:
        current_revision_date = rev.revision_date
        current_interval = calculate_days_difference(
            previous_date, current_revision_date
        )
        last_interval = current_interval_position

        # This is get the previous and next interval based in the `last_interval` -> [1,2,3] the middle one is the `last_interval`
        # "good": move forward in sequence
        # "ok": stay at same position
        # "bad": move backward in sequence
        rating_intervals = get_interval_triplet(
            current_interval=last_interval, interval_list=intervals
        )
        calculated_next_interval = rating_intervals[rev.rating + 1]

        if calculated_next_interval > end_interval:
            # This revision caused graduation
            next_interval = None

            data_to_update = {
                "last_interval": last_interval,
                "current_interval": current_interval,
                "next_interval": next_interval,
            }
            revisions.update(data_to_update, rev.id)

            # Update hafizs_items for graduation
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
        current_interval_position = next_interval  # (for next iteration)


def populate_hafizs_items_stat_columns(
    item_id: int = None,
    # current_date: str,
    # update_srs: bool = True,
):
    """
    Populate or update statistics columns for Hafiz items in the memorization tracking system.

    This function calculates and updates various review-related statistics for memorization items,
    including good/bad review streaks, review counts, and overall review score. It can update
    statistics for a specific item or all items in the hafizs_items table.

    Args:
        current_date (str): The current date used for interval calculations.
        item_id (int, optional): Specific item ID to update. If None, updates all items.
        update_srs (bool, optional): Whether to recalculate SRS intervals. Defaults to True.

    Returns:
        None: Updates hafizs_items table directly with calculated statistics.

    The function performs the following key operations:
    - Computes consecutive good and bad review streaks
    - Tracks total good and bad review counts
    - Calculates cumulative review score
    - Optionally updates Spaced Repetition System (SRS) intervals
    """

    def get_item_id_summary(item_id: int):
        items_rev_data = revisions(
            where=f"item_id = {item_id}", order_by="revision_date ASC"
        )
        good_streak = 0
        bad_streak = 0
        last_review = ""
        good_count = 0
        bad_count = 0
        score = 0
        count = 0

        for rev in items_rev_data:
            current_rating = rev.rating

            if current_rating == -1:
                bad_count += 1
                # Update the streak
                bad_streak += 1
                good_streak = 0
            elif current_rating == 1:
                good_count += 1
                # Update the streak
                good_streak += 1
                bad_streak = 0
            else:
                good_streak = 0
                bad_streak = 0

            score += current_rating
            count += 1
            last_review = rev.revision_date

        return {
            "good_streak": good_streak,
            "bad_streak": bad_streak,
            "last_review": last_review,
            "good_count": good_count,
            "bad_count": bad_count,
            "score": score,
            "count": count,
        }

    # Update the streak for a specific items if item_id is givien
    if item_id is not None:
        current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")
        if current_hafiz_items:
            current_hafiz_items_id = current_hafiz_items[0].id
            hafizs_items.update(get_item_id_summary(item_id), current_hafiz_items_id)

        return None

    # Update the streak for all the items in the hafizs_items
    for h_item in hafizs_items():
        hafizs_items.update(get_item_id_summary(h_item.item_id), h_item.id)


# This function is responsible for updating the hafizs_items stats column and interval column(if needed)
def update_stats_and_interval(item_id: int, mode_id: int, current_date: str):
    populate_hafizs_items_stat_columns(item_id=item_id)
    if mode_id == 5:
        recalculate_intervals_on_srs_records(item_id=item_id, current_date=current_date)


def get_item_id(page_number: int, not_memorized_only: bool = False):
    """
    This function will lookup the page_number in the `hafizs_items` table
    if there is no record for that page and then create new records for that page
    by looking up the `items` table

    Each page may contain more than one record (including the page_part)

    Then filter out the in_active hafizs_items and return the item_id

    Returns:
    list of item_id
    """

    qry = f"page_number = {page_number}"
    hafiz_data = hafizs_items(where=qry)

    if not hafiz_data:
        page_items = items(where=f"page_id = {page_number} AND active = 1")
        for item in page_items:
            hafizs_items.insert(
                Hafiz_Items(
                    item_id=item.id,
                    page_number=item.page_id,
                    mode_id=1,
                )
            )
    hafiz_data = (
        hafizs_items(
            where=f"{qry} AND status IS NULL"
        )  # Filter out memorized, as of now status is NULL
        if not_memorized_only
        else hafizs_items(where=qry)
    )
    item_ids = [
        hafiz_item.item_id
        for hafiz_item in hafiz_data
        if items[hafiz_item.item_id].active
    ]
    return sorted(item_ids)


def get_hafizs_items(item_id):
    current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")
    if current_hafiz_items:
        return current_hafiz_items[0]
    else:
        return ValueError(f"No hafizs_items found for item_id {item_id}")


def get_current_date(auth) -> str:
    current_hafiz = hafizs[auth]
    current_date = current_hafiz.current_date
    if current_date is None:
        current_date = hafizs.update(current_date=current_time(), id=auth).current_date
    return current_date


def get_display_count(auth):
    """It will return the display_count for the current hafiz"""
    current_hafiz = hafizs[auth]
    return current_hafiz.display_count


def get_column_headers(table):
    data_class = tables[table].dataclass()
    columns = [k for k in data_class.__dict__.keys() if not k.startswith("_")]
    return columns


def get_mode_name(mode_id: int):
    return modes[mode_id].name


def get_juz_name(page_id=None, item_id=None):
    if item_id:
        qry = f"SELECT pages.juz_number FROM pages LEFT JOIN items ON pages.id = items.page_id WHERE items.id = {item_id}"
        juz_number = db.q(qry)[0]["juz_number"]
    else:
        juz_number = pages[page_id].juz_number
    return juz_number


def get_surah_name(page_id=None, item_id=None):
    if item_id:
        surah_id = items[item_id].surah_id
    else:
        surah_id = items(where=f"page_id = {page_id}")[0].surah_id
    surah_details = surahs[surah_id]
    return surah_details.name


def get_start_text(item_id):
    try:
        return items[item_id].start_text
    except:
        return "-"


def get_page_number(item_id):
    page_id = items[item_id].page_id
    return pages[page_id].page_number


def get_page_description(
    item_id,
    link: str = None,
    is_link: bool = True,
    is_bold: bool = True,
    custom_text="",
):
    item_description = items[item_id].description
    if not item_description:
        item_description = (
            Span(get_page_number(item_id), cls=TextPresets.bold_sm if is_bold else ""),
            Span(" - ", get_surah_name(item_id=item_id)),
            Span(custom_text) if custom_text else "",
        )

    if not is_link:
        return Span(item_description)
    return A(
        Span(item_description),
        href=(f"/page_details/{item_id}" if not link else link),
        cls=AT.classic,
    )


def get_last_item_id():
    return items(where="active = 1", order_by="id DESC")[0].id


def find_next_item_id(item_id):
    item_ids = [item.id for item in items(where="active = 1")]
    return find_next_greater(item_ids, item_id)


def get_mode_count(item_id, mode_id):
    mode_records = revisions(where=f"item_id = {item_id} AND mode_id = {mode_id}")
    return len(mode_records)


def get_page_count(records: list[Revision] = None, item_ids: list = None) -> float:
    total_count = 0
    # Get items to process
    if item_ids:
        process_items = item_ids
    elif records:
        process_items = [record.item_id for record in records]
    else:
        return format_number(total_count)
    # Calculate page count
    for item_id in process_items:
        page_no = items[item_id].page_id
        total_parts = items(where=f"page_id = {page_no} and active = 1")
        total_count += 1 / len(total_parts)
    return format_number(total_count)


def get_unique_page_count(recent_review_items):
    return len(set(map(get_page_number, recent_review_items)))


def get_revision_data(mode_id: str, revision_date: str):
    """Returns the revision count and revision ID for a specific date and mode ID."""
    records = revisions(
        where=f"mode_id = '{mode_id}' AND revision_date = '{revision_date}'"
    )
    rev_ids = ",".join(str(r.id) for r in records)
    count = get_page_count(records)
    return count, rev_ids


def create_count_link(count: int, rev_ids: str):
    if not rev_ids:
        return count
    return A(
        count,
        href=f"/revision/bulk_edit?ids={rev_ids}",
        cls=AT.classic,
    )


def render_progress_display(current_count: int, target_count: int, rev_ids: str = ""):
    target_count = format_number(target_count)
    current_count = format_number(current_count)
    base_link = create_count_link(current_count, rev_ids)
    if current_count == 0 and target_count == 0:
        return "-"
    elif current_count == target_count:
        return (base_link, " ✔️")
    elif current_count > target_count:
        return (base_link, f" / {target_count}", " ✔️")
    else:
        return (base_link, f" / {target_count}")


def render_rating(rating: int):
    return RATING_MAP.get(str(rating))


def render_date(date: str):
    if date:
        date = date_to_human_readable(date)
    return date


def render_type_description(list, _type=""):
    first_description = list[0]
    last_description = list[-1]

    if _type == "Surah":
        _type = ""
        first_description = surahs[first_description].name
        last_description = surahs[last_description].name

    if len(list) == 1:
        return f"{_type} {first_description}"
    return (
        f"{_type}{"" if _type == "" else "s"} {first_description} – {last_description}"
    )


def mode_dropdown(default_mode=1, **kwargs):
    def mk_options(mode):
        id, name = mode.id, mode.name
        is_selected = lambda m: m == default_mode
        return Option(name, value=id, selected=is_selected(id))

    return LabelSelect(
        map(mk_options, modes()),
        label="Mode Id",
        name="mode_id",
        select_kwargs={"name": "mode_id"},
        **kwargs,
    )


def rating_radio(
    default_rating: int = 1,
    direction: str = "vertical",
    is_label: bool = True,
    id: str = "rating",
    cls: str = None,
):

    def render_radio(o):
        value, label = o
        is_checked = True if int(value) == default_rating else False
        return Div(
            FormLabel(
                Radio(id=id, value=value, checked=is_checked, cls=cls),
                Span(label),
                cls="space-x-2 p-1 border border-transparent has-[:checked]:border-blue-500",
            ),
            cls=f"{"inline-block" if direction == "horizontal" else None}",
        )

    options = map(render_radio, RATING_MAP.items())

    if direction == "horizontal":
        outer_cls = (FlexT.block, FlexT.row, FlexT.wrap, "gap-x-6 gap-y-4")
    elif direction == "vertical":
        outer_cls = "space-y-2 leading-8 sm:leading-6"

    if is_label:
        label = FormLabel("Rating")
    else:
        label = None

    return Div(label, *options, cls=outer_cls)


def rating_dropdown(
    default_mode="1", is_label=True, rating_dict=RATING_MAP, name="rating", **kwargs
):
    def mk_options(o):
        id, name = o
        is_selected = lambda m: m == default_mode
        return fh.Option(name, value=id, selected=is_selected(id))

    return Div(
        fh.Select(
            map(mk_options, rating_dict.items()),
            label=("Rating" if is_label else None),
            name=name,
            select_kwargs={"name": name},
            cls="[&>div]:h-8 uk-form-sm w-28",
            **kwargs,
        ),
        cls="max-w-28 outline outline-gray-200 outline-1 rounded-sm",
    )


def status_dropdown(current_status):
    def render_options(status):
        return fh.Option(
            status,
            value=standardize_column(status),
            selected=(status == current_status),
        )

    return fh.Select(
        map(render_options, STATUS_OPTIONS),
        name="selected_status",
        style="margin: 0px 12px 12px 0px !important;",
    )


def custom_select(name: str, vals: list[str], default_val: str, **kwargs):
    def render_options(val):
        return fh.Option(
            val,
            value=standardize_column(val),
            selected=(standardize_column(val) == standardize_column(default_val)),
        )

    return fh.Select(
        map(render_options, vals),
        name=name,
        **kwargs,
    )


def action_buttons():
    # Enable and Disable the button based on the checkbox selection
    dynamic_enable_button_hyperscript = "on checkboxChanged if first <input[type=checkbox]:checked/> remove @disabled else add @disabled"
    import_export_buttons = DivLAligned(
        Button(
            "Bulk Edit",
            hx_post="/revision/bulk_edit",
            hx_push_url="true",
            hx_include="closest form",
            hx_target="body",
            cls="toggle_btn",  # To disable and enable the button based on the checkboxes (Don't change, it is referenced in hyperscript)
            disabled=True,
            _=dynamic_enable_button_hyperscript,
        ),
        Button(
            "Bulk Delete",
            hx_delete="/revision",
            hx_confirm="Are you sure you want to delete these revisions?",
            hx_target="body",
            cls=("toggle_btn", ButtonT.destructive),
            disabled=True,
            _=dynamic_enable_button_hyperscript,
        ),
        A(
            Button("Export", type="button"),
            href="tables/revisions/export",
            hx_boost="false",
        ),
    )
    return DivFullySpaced(
        Div(),
        import_export_buttons,
        cls="flex-wrap gap-4 mb-3",
    )


def split_page_range(page_range: str):
    start_id, end_id = (
        page_range.split("-") if "-" in page_range else [page_range, None]
    )
    start_id = int(start_id)
    end_id = int(end_id) if end_id else None
    return start_id, end_id


# This is used to dynamically sort them by mode name which contains the sort order
# eg: sorted(mode_ids, key=lambda id: extract_mode_sort_number(id))
def extract_mode_sort_number(mode_id):
    """Extract the number from mode name like '1. full Cycle' -> 1"""
    mode_name = modes[mode_id].name
    return int(mode_name.split(". ")[0])


####################### Recent_review and Watch_list common function #######################


def update_hafizs_items_table(item_id: int, data_to_update: dict):
    current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")

    if current_hafiz_items:
        hafizs_items.update(data_to_update, current_hafiz_items[0].id)


def get_lastest_date(item_id: int, mode_id: int):
    if mode_id == 3:
        mode_ids = ("2", "3")
    elif mode_id == 4:
        mode_ids = ("3", "4")
    elif mode_id == 5:
        mode_ids = "5"
    else:
        return None

    last_reviewed = revisions(
        where=f"item_id = {item_id} AND mode_id IN ({", ".join(mode_ids)})",
        order_by="revision_date DESC",
        limit=1,
    )

    if last_reviewed:
        return last_reviewed[0].revision_date
    return None


def update_review_dates(item_id: int, mode_id: int):
    if mode_id == 3:
        increment_day = 1
    elif mode_id == 4:
        increment_day = 7
    else:
        return None

    latest_revision_date = get_lastest_date(item_id, mode_id)

    current_hafiz_item = hafizs_items(where=f"item_id = {item_id}")
    if current_hafiz_item:
        current_hafiz_item = current_hafiz_item[0]
        # To update the status of hafizs_items table if it is newly memorized
        if current_hafiz_item.mode_id == 2:
            current_hafiz_item.mode_id = 3
        current_hafiz_item.last_review = latest_revision_date
        current_hafiz_item.next_review = add_days_to_date(
            latest_revision_date, increment_day
        )
        hafizs_items.update(current_hafiz_item)


def get_srs_interval_list(item_id: int):
    current_hafiz_item = get_hafizs_items(item_id)
    booster_pack_details = srs_booster_pack[current_hafiz_item.srs_booster_pack_id]
    end_interval = booster_pack_details.end_interval

    booster_pack_intervals = booster_pack_details.interval_days.split(",")
    booster_pack_intervals = list(map(int, booster_pack_intervals))

    # Filter numbers less than end_interval
    interval_list = [
        interval for interval in booster_pack_intervals if interval < end_interval
    ]
    # Add the first interval >= end_interval for graduation logic
    first_greater = next(
        (interval for interval in booster_pack_intervals if interval >= end_interval),
        None,
    )
    if first_greater is not None:
        interval_list.append(first_greater)

    return interval_list


def get_interval_based_on_rating(
    item_id: int, rating: int, is_edit: bool = False, is_dropdown: bool = False
):
    """
    Calculate the next interval for an SRS (Spaced Repetition System) item based on user rating.

    Args:
        item_id (int): The unique identifier of the memorization item.
        rating (int): The user's rating of the item's recall difficulty.
        is_edit (bool, optional): Flag to indicate if the interval is being calculated during an edit. Defaults to False.
        is_dropdown (bool, optional): Flag to determine if the interval is for dropdown display. Defaults to False.

    Returns:
        int or str: The calculated next interval in days, or "Finished" if the item has been fully learned.

    Notes:
        - Uses the current item's SRS booster pack to determine interval progression
        - Handles different scenarios like editing and dropdown display
        - Considers the current interval and user's rating to calculate the next interval
    """

    current_hafiz_item = get_hafizs_items(item_id)
    # TODO: Later need to retrive the current_interval from the hafizs_items table as `last_interval`
    if is_edit:
        # last_reviewed = revisions(
        #     where=f"item_id = {item_id} AND mode_id = 5",
        #     order_by="revision_date DESC",
        #     limit=1,
        # )
        # current_interval = last_reviewed[0].last_interval
        current_interval = current_hafiz_item.last_interval
    else:
        current_interval = current_hafiz_item.next_interval

    intervals = get_srs_interval_list(item_id)
    rating_intervals = get_interval_triplet(
        current_interval=current_interval, interval_list=intervals
    )
    current_rating_interval = rating_intervals[rating + 1]

    # This logic is to show the user that the item is finished after this record
    if is_dropdown:
        end_interval = srs_booster_pack[
            current_hafiz_item.srs_booster_pack_id
        ].end_interval
        if current_rating_interval > end_interval:
            return "Finished"
    return current_rating_interval


# This function is responsible for creating and deleting records on the srs
def update_hafiz_items_for_srs(
    item_id: int, mode_id: int, current_date: str, rating: int, is_checked: bool
):
    if is_checked:
        latest_revision_date = get_lastest_date(item_id, mode_id)
        current_hafiz_item = get_hafizs_items(item_id)
        end_interval = srs_booster_pack[
            current_hafiz_item.srs_booster_pack_id
        ].end_interval
        # TODO: the current_interval is difference between last_review and current_date instead of the last_interval
        next_interval = get_interval_based_on_rating(item_id, rating)
        current_hafiz_item.last_interval = current_hafiz_item.next_interval
        current_hafiz_item.current_interval = calculate_days_difference(
            current_hafiz_item.last_review, current_date
        )
        current_hafiz_item.last_review = latest_revision_date

        if end_interval > next_interval:
            current_hafiz_item.next_interval = next_interval
            current_hafiz_item.next_review = add_days_to_date(
                latest_revision_date, next_interval
            )
        else:
            current_hafiz_item.next_interval = None
            current_hafiz_item.next_review = None

        hafizs_items.update(current_hafiz_item)
    else:
        recalculate_intervals_on_srs_records(item_id=item_id, current_date=current_date)


def checkbox_update_logic(mode_id, rating, item_id, date, is_checked, plan_id=None):
    conditions = [
        f"revision_date = '{date}'",
        f"item_id = {item_id}",
        f"mode_id = {mode_id}",
    ]

    if plan_id is not None:
        conditions.append(f"plan_id = {plan_id}")

    qry = " AND ".join(conditions)
    revisions_data = revisions(where=qry)

    if not revisions_data and is_checked:
        # Create new revision
        revision_data = {
            "revision_date": date,
            "item_id": item_id,
            "mode_id": mode_id,
            "rating": rating,
        }
        if plan_id is not None:
            revision_data["plan_id"] = plan_id

        if mode_id == 5:
            # Update the additional three columns if it is srs mode
            hafiz_items_data = get_hafizs_items(item_id)
            end_interval = srs_booster_pack[
                hafiz_items_data.srs_booster_pack_id
            ].end_interval
            revision_data["last_interval"] = hafiz_items_data.next_interval
            revision_data["current_interval"] = calculate_days_difference(
                hafiz_items_data.last_review, date
            )
            next_interval = get_interval_based_on_rating(item_id, rating)
            if end_interval > next_interval:
                revision_data["next_interval"] = next_interval

        revisions.insert(Revision(**revision_data))

    elif revisions_data and not is_checked:
        # Delete existing revision
        revisions.delete(revisions_data[0].id)

    if mode_id == 5:
        update_hafiz_items_for_srs(
            item_id=item_id,
            mode_id=mode_id,
            current_date=date,
            rating=rating,
            is_checked=is_checked,
        )
    elif mode_id == 2:
        hafiz_items_data = get_hafizs_items(item_id)
        if is_checked:
            hafizs_items.update(
                {"status": "newly_memorized", "mode_id": 2}, hafiz_items_data.id
            )
        else:
            hafizs_items.update({"status": None, "mode_id": 1}, hafiz_items_data.id)
    else:
        # Update the review dates based on the mode -> RR should increment by one and WL should increment by 7
        update_review_dates(item_id, mode_id)

    # After the operation populate the stats columns
    populate_hafizs_items_stat_columns(item_id=item_id)


def graduate_the_item_id(item_id: int, mode_id: int, auth: int, checked: bool = True):
    last_review_date = get_lastest_date(item_id, mode_id)
    recent_review = {
        "mode_id": 3,
        "last_review": last_review_date,
        "next_review": add_days_to_date(last_review_date, 1),
    }
    watch_list = {
        "status": "newly_memorized",
        "mode_id": 4,
        "last_review": last_review_date,
        "next_review": add_days_to_date(last_review_date, 7),
        "watch_list_graduation_date": None,
    }
    memorized = {
        "status": "memorized",
        "mode_id": 1,
        "last_review": None,
        "next_review": None,
        "watch_list_graduation_date": get_current_date(auth),
    }
    srs = {
        "status": "memorized",
        "mode_id": 1,
        "last_review": last_review_date,
        "next_review": None,
        "last_interval": None,
        "current_interval": None,
        "next_interval": None,
        "srs_booster_pack_id": None,
        "srs_start_date": None,
    }

    if mode_id == 3:
        data_to_update = watch_list if checked else recent_review
    elif mode_id == 4:
        data_to_update = memorized if checked else watch_list
    elif mode_id == 5:
        data_to_update = srs
    else:
        return None

    update_hafizs_items_table(item_id, data_to_update)


####################### END #######################


def datewise_summary_table(show=None, hafiz_id=None):
    qry = f"SELECT MIN(revision_date) AS earliest_date FROM {revisions}"
    qry = (qry + f" WHERE hafiz_id = {hafiz_id}") if hafiz_id else qry
    result = db.q(qry)
    earliest_date = result[0]["earliest_date"]
    current_date = get_current_date(hafiz_id)

    date_range = pd.date_range(
        start=(earliest_date or current_date), end=current_date, freq="D"
    )
    date_range = [date.strftime("%Y-%m-%d") for date in date_range][::-1]
    date_range = date_range[:show] if show else date_range

    def _render_datewise_row(date):
        # Get the unique modes for that particular date
        rev_condition = f"WHERE revisions.revision_date = '{date}'" + (
            f" AND revisions.hafiz_id = {hafiz_id}" if hafiz_id else ""
        )
        unique_modes = db.q(f"SELECT DISTINCT mode_id FROM {revisions} {rev_condition}")
        unique_modes = [m["mode_id"] for m in unique_modes]
        unique_modes = sorted(unique_modes, key=lambda id: extract_mode_sort_number(id))

        mode_with_ids_and_pages = []
        for mode_id in unique_modes:
            # Joining the revisions and items table to get these columns
            # rev_id(Ids are needed for bulk_edit),
            # items_id(To correctly render the surah name if its starts from part),
            # page_id(To group pages into range)
            rev_query = f"SELECT revisions.id, revisions.item_id, items.page_id FROM {revisions} LEFT JOIN {items} ON revisions.item_id = items.id {rev_condition} AND mode_id = {mode_id}"
            current_date_and_mode_revisions = db.q(rev_query)
            mode_with_ids_and_pages.append(
                {
                    "mode_id": mode_id,
                    "revision_data": current_date_and_mode_revisions,
                }
            )

        def _render_pages_range(revisions_data: list):
            page_ranges = compact_format(sorted([r["page_id"] for r in revisions_data]))

            # get the surah name using the item_id for the corresponding page
            def _render_page(page):
                item_id = [
                    r["item_id"] for r in revisions_data if r["page_id"] == page
                ][0]
                return get_page_description(item_id=item_id, is_link=False)

            # This function will return the list of rev_id based on max and min page for bulk_edit url
            def get_ids_for_page_range(data, min_page, max_page=None):
                result = []
                # Filter based on page_id values
                for item in data:
                    page_id = item["page_id"]
                    if max_page is None:
                        if page_id == min_page:
                            result.append(item["id"])
                    else:
                        if min_page <= page_id <= max_page:
                            result.append(item["id"])
                # Sort the result and convert them into str
                return list(map(str, sorted(result)))

            ctn = []
            for page_range in page_ranges.split(","):
                start_page, end_page = split_page_range(page_range)
                if end_page:
                    range_desc = (
                        _render_page(start_page),
                        Span(" -> "),
                        _render_page(end_page),
                    )
                else:
                    range_desc = _render_page(start_page)

                ctn.append(
                    Span(
                        A(
                            *range_desc,
                            hx_get=f"/revision/bulk_edit?ids={','.join(get_ids_for_page_range(revisions_data, start_page, end_page))}",
                            hx_push_url="true",
                            hx_target="body",
                            cls=(AT.classic),
                        ),
                        cls="block",
                    )
                )

            return P(
                *ctn,
                cls="space-y-3",
            )

        # To handle if the date has no entry
        if not mode_with_ids_and_pages:
            return [
                Tr(
                    Td(date_to_human_readable(date)),
                    Td("-"),
                    Td("-"),
                    Td("-"),
                    Td("-"),
                )
            ]

        rows = [
            Tr(
                *(
                    # Only add the date and total_count for the first row and use rowspan to expand them for the modes breakdown
                    (
                        Td(
                            date_to_human_readable(date),
                            rowspan=f"{len(mode_with_ids_and_pages)}",
                        ),
                        Td(
                            sum(
                                [
                                    len(i["revision_data"])
                                    for i in mode_with_ids_and_pages
                                ]
                            ),
                            rowspan=f"{len(mode_with_ids_and_pages)}",
                        ),
                    )
                    if mode_with_ids_and_pages[0]["mode_id"] == o["mode_id"]
                    else ()
                ),
                Td(modes[o["mode_id"]].name),
                Td(len(o["revision_data"])),
                Td(_render_pages_range(o["revision_data"])),
            )
            for o in mode_with_ids_and_pages
        ]
        return rows

    datewise_table = Div(
        Table(
            Thead(
                Tr(
                    Th("Date"),
                    Th("Total Count", cls="uk-table-shrink"),
                    Th("Mode"),
                    Th("Count"),
                    Th("Range"),
                )
            ),
            Tbody(*flatten_list(map(_render_datewise_row, date_range))),
        ),
        cls="uk-overflow-auto",
    )
    return datewise_table


def render_hafiz_card(hafizs_user, auth):
    is_current_hafizs_user = auth != hafizs_user.hafiz_id
    return Card(
        header=DivFullySpaced(H3(hafizs[hafizs_user.hafiz_id].name)),
        footer=Button(
            "Switch hafiz" if is_current_hafizs_user else "Go to home",
            name="current_hafiz_id",
            value=hafizs_user.hafiz_id,
            hx_post="/hafiz_selection",
            hx_target="body",
            hx_replace_url="true",
            id=f"btn-{hafizs[hafizs_user.hafiz_id].name}",
            cls=(ButtonT.primary if is_current_hafizs_user else ButtonT.secondary),
        ),
        cls="min-w-[300px] max-w-[400px]",
    )


def render_options(option):
    return Option(
        option.capitalize(),
        value=option,
    )


login_redir = RedirectResponse("/login", status_code=303)


@app.get("/login")
def login():
    form = Form(
        LabelInput(label="Email", name="email", type="email"),
        LabelInput(label="Password", name="password", type="password"),
        Button("Login"),
        action="/login",
        method="post",
    )
    return Titled("Login", form)


@dataclass
class Login:
    email: str
    password: str


@app.post("/login")
def login_post(login: Login, sess):
    if not login.email or not login.password:
        return login_redir
    try:
        u = users(where="email = '{}'".format(login.email))[0]
    except IndexError:
        # u = users.insert(login)
        return login_redir
    if not compare_digest(u.password.encode("utf-8"), login.password.encode("utf-8")):
        return login_redir
    sess["user_auth"] = u.id
    hafizs_users.xtra(id=u.id)
    return RedirectResponse("/", status_code=303)


@app.get("/logout")
def logout(sess):
    user_auth = sess.get("user_auth", None)
    if user_auth is not None:
        del sess["user_auth"]
    auth = sess.get("auth", None)
    if auth is not None:
        del sess["auth"]
    return RedirectResponse("/login", status_code=303)


@app.post("/add_hafiz")
def add_hafiz_and_relations(hafiz: Hafiz, relationship: str, sess):
    hafiz_id = hafizs.insert(hafiz)
    hafizs_users.insert(
        hafiz_id=hafiz_id.id,
        user_id=sess["user_auth"],
        relationship=relationship,
        granted_by_user_id=sess["user_auth"],
        granted_at=datetime.now().strftime("%d-%m-%y %H:%M:%S"),
    )
    return RedirectResponse("/hafiz_selection", status_code=303)


@app.get("/hafiz_selection")
def hafiz_selection(sess):
    # In beforeware we are adding the hafiz_id filter using xtra
    # we have to reset that xtra attribute in order to show revisions for all hafiz
    revisions.xtra()
    hafizs_users.xtra()
    auth = sess.get("auth", None)
    user_auth = sess.get("user_auth", None)
    if user_auth is None:
        return login_redir

    cards = [
        render_hafiz_card(h, auth) for h in hafizs_users() if h.user_id == user_auth
    ]
    hafiz_form = Card(
        Titled(
            "Add Hafiz",
            Form(
                LabelInput(label="Hafiz Name", name="name", required=True),
                LabelSelect(
                    *map(render_options, OPTION_MAP["age_group"]),
                    label="Age Group",
                    name="age_group",
                ),
                LabelInput(
                    label="Daily Capacity",
                    name="daily_capacity",
                    type="number",
                    min="1",
                    value="1",
                    required=True,
                ),
                LabelSelect(
                    *map(render_options, OPTION_MAP["relationship"]),
                    label="Relationship",
                    name="relationship",
                ),
                Button("Add Hafiz"),
                action="/add_hafiz",
                method="post",
                cls="space-y-3",
            ),
        ),
        cls="w-[300px]",
    )
    return main_area(
        Div(
            H5("Select Hafiz"),
            Div(*cards, cls=(FlexT.block, FlexT.wrap, "gap-4")),
            Div(hafiz_form),
            cls="space-y-4",
        ),
        auth=auth,
    )


@app.post("/hafiz_selection")
def change_hafiz(current_hafiz_id: int, sess):
    sess["auth"] = current_hafiz_id
    return RedirectResponse("/", status_code=303)


def main_area(*args, active=None, auth=None):
    is_active = lambda x: AT.primary if x == active else None
    title = A("Quran SRS", href=index)
    hafiz_name = A(
        f"{hafizs[auth].name if auth is not None else "Select hafiz"}",
        href="/hafiz_selection",
        method="GET",
    )
    return Title("Quran SRS"), Container(
        Div(
            NavBar(
                A("Home", href=index, cls=is_active("Home")),
                A(
                    "Profile",
                    href="/profile/surah",
                    cls=is_active("Memorization Status"),
                ),
                A(
                    "Page Details",
                    href="/page_details",
                    cls=is_active("Page Details"),
                ),
                A("Revision", href=revision, cls=is_active("Revision")),
                A("Tables", href="/tables", cls=is_active("Tables")),
                A("Report", href="/report", cls=is_active("Report")),
                A(
                    "SRS",
                    href="/srs",
                    cls=is_active("SRS"),
                ),
                A("Settings", href="/settings", cls=is_active("Settings")),
                # A(
                #     "New Memorization",
                #     href="/new_memorization/juz",
                #     cls=is_active("New Memorization"),
                # ),
                # A(
                #     "Recent Review",
                #     href="/recent_review",
                #     cls=is_active("Recent Review"),
                # ),
                # A(
                #     "Watch List",
                #     href="/watch_list",
                #     cls=is_active("Watch List"),
                # ),
                A("logout", href="/logout"),
                # A("User", href=user, cls=is_active("User")), # The user nav is temporarily disabled
                brand=H3(title, Span(" - "), hafiz_name),
            ),
            DividerLine(y_space=0),
            cls="bg-white sticky top-0 z-50",
            hx_boost="false",
        ),
        Main(*args, cls="p-4", id="main") if args else None,
        cls=ContainerT.xl,
    )


def tables_main_area(*args, active_table=None, auth=None):
    is_active = lambda x: "uk-active" if x == active_table else None

    tables_list = [
        t for t in str(tables).split(", ") if not t.startswith(("sqlite", "_"))
    ]
    table_links = [
        Li(A(t.capitalize(), href=f"/tables/{t}"), cls=is_active(t))
        for t in tables_list
    ]

    side_nav = NavContainer(
        NavParentLi(
            H4("Tables", cls="pl-4"),
            NavContainer(*table_links, parent=False),
        )
    )

    return main_area(
        Div(
            Div(side_nav, cls="flex-1 p-2"),
            (
                Div(*args, cls="flex-[4] border-l-2 p-4", id="table_view")
                if args
                else None
            ),
            cls=(FlexT.block, FlexT.wrap),
        ),
        active="Tables",
        auth=auth,
    )


def render_stats_summary_table(auth, target_counts):
    current_date = get_current_date(auth)
    today = current_date
    yesterday = sub_days_to_date(today, 1)
    today_completed_count = get_page_count(
        revisions(where=f"revision_date = '{today}'")
    )
    yesterday_completed_count = get_page_count(
        revisions(where=f"revision_date = '{yesterday}'")
    )
    current_date_description = P(
        Span("System Date: ", cls=TextPresets.bold_lg),
        Span(date_to_human_readable(current_date), id="current_date_description"),
    )
    mode_ids = [mode.id for mode in modes()]
    sorted_mode_ids = sorted(mode_ids, key=lambda x: extract_mode_sort_number(x))

    def render_count(mode_id, revision_date, is_link=True, show_dash_for_zero=False):
        count, item_ids = get_revision_data(mode_id, revision_date)

        if count == 0:
            if show_dash_for_zero:
                return "-", ""
            else:
                return 0, ""

        if is_link:
            return create_count_link(count, item_ids)
        else:
            return count, item_ids

    def render_stat_rows(current_mode_id):
        today_count, today_item_ids = render_count(
            current_mode_id, today, is_link=False
        )
        # Try to get today's target count for particular mode_id
        # If mode_id doesn't exist in target_counts dict, return 0
        today_target = (
            target_counts[current_mode_id]
            if current_mode_id in target_counts.keys()
            else 0
        )
        progress_display = render_progress_display(
            today_count, today_target, today_item_ids
        )
        yesterday_display = render_count(
            current_mode_id, yesterday, is_link=True, show_dash_for_zero=True
        )
        return Tr(
            Td(f"{modes[current_mode_id].name}"),
            Td(progress_display),
            Td(yesterday_display),
            id=f"stat-row-{current_mode_id}",
        )

    overall_target_count = sum(target_counts.values())
    return Div(
        DivLAligned(
            current_date_description,
            Button(
                "Close Date",
                hx_get="/close_date",
                target_id="current_date_description",
                cls=(ButtonT.default, "px-2 py-3 h-0"),
            ),
        ),
        Table(
            Thead(
                Tr(
                    Th("Modes"),
                    Th("Today"),
                    Th("Yesterday"),
                )
            ),
            Tbody(
                *map(render_stat_rows, sorted_mode_ids),
            ),
            Tfoot(
                Tr(
                    Td("Total"),
                    Td(
                        render_progress_display(
                            today_completed_count, overall_target_count
                        )
                    ),
                    Td(yesterday_completed_count),
                    cls="[&>*]:font-bold",
                    id="total_row",
                ),
            ),
        ),
    )


#################### start ## Custom Single and Bulk Entry ################################
# This route is used to redirect to the appropriate revision entry form
@rt("/revision/entry")
def post(type: str, page: str, plan_id: int):
    print(plan_id)
    if type == "bulk":
        return Redirect(f"/revision/bulk_add?page={page}&plan_id={plan_id}")
    elif type == "single":
        return Redirect(f"/revision/add?page={page}&plan_id={plan_id}")


def custom_entry_inputs(plan_id):
    """
    This function is used to retain the input values in the form and display the custom entry inputs
    """
    revision_data = revisions(where="mode_id = 1")
    last_added_item_id = revision_data[-1].item_id if revision_data else None

    if last_added_item_id:
        item_details = items[last_added_item_id]
        last_added_page = item_details.page_id

        if item_details.item_type == "page-part":
            # fill the page input with parts based on the last added record
            # to start from the next part
            if "1" in item_details.part:
                last_added_page = last_added_page + 0.2
            elif (
                len(items(where=f"page_id = {last_added_page} AND active != 0")) > 2
                and "2" in item_details.part
            ):
                last_added_page = last_added_page + 0.3
    else:
        last_added_page = None

    # if it is greater than 604, we are reseting the last added page to None
    if isinstance(last_added_page, int) and last_added_page >= 604:
        last_added_page = None
    if not last_added_page:
        last_added_page = 1
    if isinstance(last_added_page, int):
        last_added_page += 1
    entry_buttons = Form(
        P(
            "Custom Page Entry",
            cls=TextPresets.muted_sm,
        ),
        DivLAligned(
            Input(
                type="text",
                placeholder="page",
                cls="w-20",
                id="page",
                value=last_added_page,
                autocomplete="off",
                # pattern=r"^\d+(\.\d+)?(-\d+)?$",
                pattern=r"^(?!0+(?:\.0*)?$)0*\d{1,3}(?:\.\d+)?(?:-\d+)?$",
                title="Enter format like 604, 604.2, or 604.2-3",
                required=True,
            ),
            Hidden(id="plan_id", value=plan_id),
            Button("Bulk", name="type", value="bulk", cls=ButtonT.link),
            Button("Single", name="type", value="single", cls=ButtonT.link),
            cls=("gap-3", FlexT.wrap),
        ),
        action="/revision/entry",
        method="POST",
    )
    return Div(
        entry_buttons, cls="flex-wrap gap-4 min-w-72 m-4", id="custom_entry_link"
    )


############################ END # Custom Single and Bulk Entry ################################


@rt
def index(auth, sess, full_cycle_display_count: int = None):
    current_date = get_current_date(auth)
    ################### Overall summary ###################
    # Sequential revision table
    seq_id = "1"

    unique_seq_plan_id = [
        i.id for i in plans(where="completed <> 1", order_by="id DESC")
    ]

    if unique_seq_plan_id and not len(unique_seq_plan_id) > 1:
        plan_id = unique_seq_plan_id[0]
    else:
        plan_id = None

    if plan_id is None:
        items_gaps_with_limit = []
    else:
        current_plan_item_ids = sorted(
            [
                r.item_id
                for r in revisions(
                    where=f"mode_id = '{seq_id}' AND plan_id = '{unique_seq_plan_id[0]}'"
                )
            ]
        )
        item_ids = [i.id for i in items(where="active = 1")]
        # this will return the gap of the current_plan_item_ids based on the master(items_id)
        items_gaps_with_limit = find_gaps(current_plan_item_ids, item_ids)

    def render_overall_row(o: tuple):
        last_added_item_id, upper_limit = o
        # If there are items after the last_added_item_id then it will come as `None`
        # So we are handling them here by setting the upper limit based on the items
        upper_limit = get_last_item_id() if upper_limit is None else upper_limit

        next_item_id = find_next_item_id(last_added_item_id)

        if next_item_id is None:
            next_page = "No further page"
            action_buttons = None
        else:
            next_page = get_page_description(next_item_id)
            action_buttons = DivLAligned(
                Button(
                    "Bulk",
                    hx_get=f"revision/bulk_add?item_id={next_item_id}&plan_id={plan_id}&max_item_id={get_last_item_id() if upper_limit is None else upper_limit}",
                    hx_target="body",
                    hx_push_url="true",
                    cls=(ButtonT.default, "p-2"),
                ),
                Button(
                    "Single",
                    hx_get=f"revision/add?item_id={next_item_id}&plan_id={plan_id}",
                    hx_target="body",
                    hx_push_url="true",
                    cls=(ButtonT.default, "p-2"),
                ),
                cls=("gap-3", FlexT.wrap),
            )

        return Tr(
            Td(next_page),
            Td(action_buttons),
        )

    if plan_id:
        current_plans_revision_date = revisions(
            where=f"plan_id = {plan_id} AND mode_id = {seq_id}",
            order_by="revision_date ASC",
        )

        if current_plans_revision_date:
            unique_pages = list(
                set([get_page_number(i.item_id) for i in current_plans_revision_date])
            )
            total_pages = len(unique_pages)

            first_date = current_plans_revision_date[0].revision_date
            total_days = calculate_days_difference(first_date, current_date)

            average_pages = total_pages / total_days
            average_pages = (
                int(average_pages)
                if average_pages.is_integer()
                else round(average_pages, 1)
            )

            description = P(
                f"{total_pages} pages in {total_days} days => ",
                Span(average_pages, cls=TextT.bold),
                " pages per day",
                cls=TextPresets.muted_sm,
            )

        else:
            description = None
    else:
        description = None
    ############################ Monthly Cycle ################################

    def get_monthly_target_and_progress():
        """This function will return the monthly target and the progress of the monthly review"""
        current_date = get_current_date(auth)
        memorized_len = len(
            hafizs_items(where=f"hafiz_id = {auth} and status = 'memorized'")
        )
        monthly_review_target = round(memorized_len / 30)
        monthly_reviews_completed_today = get_page_count(
            revisions(where=f"mode_id = '1' and revision_date='{current_date}'")
        )
        return monthly_review_target, monthly_reviews_completed_today

    def get_extra_page_display_count(sess, auth, current_date):
        """Get extra no_of_page display count for current user and date"""
        sess_data = sess.get("full_cycle_display_count_details", {})
        # Check if session data is valid for current user and date
        if (
            sess_data.get("auth") == auth
            and sess_data.get("current_date") == current_date
        ):
            return sess_data.get("extra_no_of_pages", 0)
        # Return 0 for new user/date
        return 0

    def update_extra_page_display_count():
        """Update extra page count in session and return new_extra count"""
        current_extra = get_extra_page_display_count(sess, auth, current_date)
        new_extra = current_extra + (full_cycle_display_count or 0)

        sess["full_cycle_display_count_details"] = {
            "auth": auth,
            "extra_no_of_pages": new_extra,
            "current_date": current_date,
        }
        return new_extra

    def create_count_button(count):
        return Button(
            f"+{count}",
            hx_get=f"/?full_cycle_display_count={count}",
            hx_select="#monthly_cycle_summary_table",
            hx_target="#monthly_cycle_summary_table",
            hx_swap="outerHTML",
        )

    total_display_count = get_display_count(auth) + update_extra_page_display_count()

    monthly_cycle_table, monthly_cycle_items = make_summary_table(
        mode_ids=["1"],
        route="monthly_cycle",
        auth=auth,
        total_display_count=total_display_count,
        plan_id=plan_id,
    )
    # Fetch monthly cycle progress
    monthly_review_target, monthly_reviews_completed_today = (
        get_monthly_target_and_progress()
    )
    monthly_progress_display = render_progress_display(
        monthly_reviews_completed_today, monthly_review_target
    )
    # Display Monthly cycle accordion with its data
    overall_table = AccordionItem(
        Span(
            f"{modes[1].name} - ",
            monthly_progress_display,
            id=f"monthly_cycle-header",
        ),
        monthly_cycle_table,
        DivHStacked(
            *[create_count_button(count) for count in [1, 2, 3, 5]],
            cls=(FlexT.center, "gap-2"),
        ),
        Div(
            description,
            (
                Table(
                    Thead(
                        Tr(
                            Th("Next"),
                            Th("Entry"),
                        )
                    ),
                    Tbody(*map(render_overall_row, items_gaps_with_limit)),
                    id="monthly_cycle_link_table",
                )
                if len(items_gaps_with_limit) > 1
                else Div(id="monthly_cycle_link_table")
            ),
            custom_entry_inputs(plan_id),
        ),
        open=True,
    )
    ############################# END ################################

    recent_review_table, recent_review_items = make_summary_table(
        mode_ids=["2", "3"], route="recent_review", auth=auth
    )

    recent_review_target = get_page_count(item_ids=recent_review_items)

    watch_list_table, watch_list_items = make_summary_table(
        mode_ids=["4"], route="watch_list", auth=auth
    )
    watch_list_target = get_page_count(item_ids=watch_list_items)

    new_memorization_table, new_memorization_items = (
        make_new_memorization_summary_table(
            mode_ids=["2"], route="new_memorization", auth=auth
        )
    )
    new_memorization_target = get_page_count(item_ids=new_memorization_items)

    srs_table, srs_items = make_summary_table(mode_ids=["5"], route="srs", auth=auth)

    srs_target = get_page_count(item_ids=srs_items)

    modal = ModalContainer(
        ModalDialog(
            ModalHeader(
                ModalTitle(id="modal-title"),
                P(cls=TextPresets.muted_sm, id="modal-description"),
                ModalCloseButton(),
                cls="space-y-3",
            ),
            ModalBody(
                Div(id="modal-body"),
                data_uk_overflow_auto=True,
            ),
            ModalFooter(),
            cls="uk-margin-auto-vertical",
        ),
        id="modal",
    )

    tables_dict = {
        modes[1].name: overall_table if items_gaps_with_limit else None,
        modes[2].name: new_memorization_table,
        modes[3].name: recent_review_table,
        modes[4].name: watch_list_table,
        modes[5].name: srs_table,
        # datewise_summary_table(hafiz_id=auth),
    }

    # Sort the tables based on the key
    tables_dict = dict(
        sorted(tables_dict.items(), key=lambda x: int(x[0].split(". ")[0]))
    )

    tables = tables_dict.values()
    # if the table is none then exclude them from the tables list
    tables = [_table for _table in tables if _table is not None]
    target_counts = {
        1: monthly_review_target,
        2: new_memorization_target,
        3: recent_review_target,
        4: watch_list_target,
        5: srs_target,
    }
    # FIXME: need to pass argument as keyword argument
    stat_table = render_stats_summary_table(auth=auth, target_counts=target_counts)

    return main_area(
        Div(stat_table, Divider(), Accordion(*tables, multiple=True, animation=True)),
        Div(modal),
        active="Home",
        auth=auth,
    )


@app.get("/close_date")
def change_the_current_date(auth):
    hafiz_data = hafizs[auth]

    # This will retrive the revision records of the recent review, watch list and SRS for the current date as per the hafiz
    revision_data = revisions(
        where=f" revision_date = '{hafiz_data.current_date}' AND mode_id IN (3, 4, 5)"
    )
    for rev in revision_data:
        # if the count is greater than 6 which is not in srs mode then it will graduate that item to next level
        if get_mode_count(rev.item_id, rev.mode_id) > 6 and rev.mode_id != 5:
            graduate_the_item_id(rev.item_id, rev.mode_id, auth)
        # if the next_interval is greater than the end_interval(srs_booster_pack table) then it will graduate that item to monthly cycle
        elif rev.mode_id == 5:
            hafiz_items_details = get_hafizs_items(rev.item_id)
            pack_details = srs_booster_pack[hafiz_items_details.srs_booster_pack_id]
            if hafiz_items_details.next_interval > pack_details.end_interval:
                graduate_the_item_id(rev.item_id, rev.mode_id, auth)

    # This will update the hafiz current date
    hafiz_data.current_date = add_days_to_date(hafiz_data.current_date, 1)
    hafizs.update(hafiz_data)
    return Redirect("/")


@app.get("/report")
def datewise_summary_table_view(auth):
    return main_area(datewise_summary_table(hafiz_id=auth), active="Report", auth=auth)


def render_new_memorization_checkbox(
    auth, item_id=None, page_id=None, label_text=None, **kwrgs
):
    label = label_text or ""

    if page_id is not None:
        item_id_list = items(where=f"page_id = {page_id} AND active != 0")
        item_ids = []
        for i in item_id_list:
            item_ids.append(i.id)
        check_form = Form(
            LabelCheckboxX(
                label,
                hx_get=f"/new_memorization/expand/page/{page_id}",
                checked=False,
                hx_trigger="click",
                onClick="return false",
            ),
            hx_vals='{"title": "CURRENT_TITLE", "description": "CURRENT_DETAILS"}'.replace(
                "CURRENT_TITLE", ""
            ).replace(
                "CURRENT_DETAILS", ""
            ),
            target_id="modal-body",
            data_uk_toggle="target: #modal",
        )
    else:
        current_revision_data = revisions(
            where=f"item_id = {item_id} AND mode_id = 2 AND hafiz_id = {auth};"
        )
        check_form = Form(
            LabelCheckboxX(
                label,
                name=f"is_checked",
                value="1",
                hx_post=f"/new_memorization/update_as_newly_memorized/{item_id}",
                **kwrgs,
                checked=True if current_revision_data else False,
            )
        )
    return check_form


def make_new_memorization_summary_table(auth: str, mode_ids: list[str], route: str):
    current_date = get_current_date(auth)

    def get_last_memorized_item_id():
        """Get the last newly_memorized `item_id` for the hafiz."""
        result = revisions(
            where=f"hafiz_id = {auth} AND mode_id = 2",
            order_by="revision_date DESC, id DESC",
            limit=1,
        )
        return result[0].item_id if result else 0

    def get_last_newly_memorized_page_for_today():
        """Get the page number of the last newly memorized item for today."""
        qry = f"""
            SELECT items.page_id AS page_number FROM revisions
            JOIN items ON revisions.item_id = items.id 
            WHERE revisions.hafiz_id = {auth} AND revisions.mode_id = 2 AND revisions.revision_date = '{current_date}'
            ORDER BY revisions.id DESC;
        """
        result = db.q(qry)
        return result[0]["page_number"] if result else None

    def get_not_memorized_item_ids(page_id):
        """Get not memorized item for a given page."""
        result = hafizs_items(where=f"page_number = {page_id} AND status IS NULL")
        return [i.item_id for i in result]

    def get_next_unmemorized_page_items(item_id):
        """Get the next closest unmemorized item_ids based on the last newly memorized `item_id`"""
        qry = f"""
            SELECT items.id AS item_id, items.page_id AS page_number FROM items
            LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
            WHERE hafizs_items.status IS NULL AND items.active != 0 AND items.id > {item_id}
       """
        ct = db.q(qry)
        grouped = group_by_type(ct, "page")
        if not grouped:
            return []
        first_page = next(iter(grouped))
        return [i["item_id"] for i in grouped[first_page] if i]

    def get_today_memorized_item_ids():
        """Get today's newly_memorized items."""
        result = revisions(where=f"mode_id = 2 AND revision_date = '{current_date}'")
        return [i.item_id for i in result]

    today_page_id = get_last_newly_memorized_page_for_today()
    if today_page_id:
        unmemorized_items = get_not_memorized_item_ids(today_page_id)
    else:
        # If there are no newly memorized items for today, get the closest unmemorized items to display
        last_newly_memorized_item_id = get_last_memorized_item_id()
        unmemorized_items = get_next_unmemorized_page_items(
            last_newly_memorized_item_id
        )
    recent_newly_memorized_items = get_today_memorized_item_ids()

    new_memorization_items = sorted(
        set(unmemorized_items + recent_newly_memorized_items)
    )
    return (
        render_summary_table(
            route=route,
            auth=auth,
            mode_ids=mode_ids,
            item_ids=new_memorization_items,
        ),
        new_memorization_items,
    )


def make_summary_table(
    mode_ids: list[str],
    route: str,
    auth: str,
    total_display_count=0,
    plan_id=None,
):
    current_date = get_current_date(auth)

    def is_review_due(item: dict) -> bool:
        """Check if item is due for review today or overdue."""
        return day_diff(item["next_review"], current_date) >= 0

    def is_reviewed_today(item: dict) -> bool:
        """Check if item was already reviewed today."""
        return item["last_review"] == current_date

    def has_recent_mode_id(item: dict) -> bool:
        """Check if item has the recent_review mode ID."""
        return item["mode_id"] == 3

    def has_monthly_cycle_mode_id(item: dict) -> bool:
        """Check if item has the monthly_cycle mode ID."""
        return item["mode_id"] == 1

    def has_revisions(item: dict) -> bool:
        """Check if item has revisions for current mode."""
        return bool(
            revisions(
                where=f"item_id = {item['item_id']} AND mode_id = {item['mode_id']}"
            )
        )

    def has_newly_memorized_for_today(item: dict) -> bool:
        """Check if item has newly memorized record for the current_date."""
        newly_memorized_record = revisions(
            where=f"item_id = {item['item_id']} AND revision_date = '{current_date}' AND mode_id = 2"
        )
        return len(newly_memorized_record) == 1

    qry = f"""
        SELECT hafizs_items.item_id, items.surah_name, hafizs_items.next_review, hafizs_items.last_review, hafizs_items.mode_id FROM hafizs_items
        LEFT JOIN items on hafizs_items.item_id = items.id 
        WHERE hafizs_items.mode_id IN ({", ".join(mode_ids)}) AND hafizs_items.hafiz_id = {auth}
        ORDER BY hafizs_items.item_id ASC
    """
    ct = db.q(qry)

    # Route-specific condition builders
    route_conditions = {
        "recent_review": lambda item: (
            (is_review_due(item) and not has_newly_memorized_for_today(item))
            or (is_reviewed_today(item) and has_recent_mode_id(item))
        ),
        "watch_list": lambda item: (
            is_review_due(item) or (is_reviewed_today(item) and has_revisions(item))
        ),
        "srs": lambda item: (
            is_review_due(item) or (is_reviewed_today(item) and has_revisions(item))
        ),
        "monthly_cycle": lambda item: (has_monthly_cycle_mode_id(item)),
    }

    recent_items = list(
        dict.fromkeys(i["item_id"] for i in ct if route_conditions[route](i))
    )
    if route == "monthly_cycle":
        recent_items = get_monthly_review_item_ids(
            auth=auth,
            total_display_count=total_display_count,
            ct=ct,
            recent_items=recent_items,
            current_plan_id=plan_id,
        )

    return (
        render_summary_table(
            route=route,
            auth=auth,
            mode_ids=mode_ids,
            item_ids=recent_items,
            plan_id=plan_id,
        ),
        recent_items,
    )


def get_monthly_review_item_ids(
    auth, total_display_count, ct, recent_items, current_plan_id
):
    current_date = get_current_date(auth)

    def has_revisions_today(item: dict) -> bool:
        """Check if item has revisions for current mode."""
        return bool(
            revisions(
                where=f"item_id = {item['item_id']} AND revision_date = '{current_date}' AND mode_id = {item['mode_id']}"
            )
        )

    def get_next_item_range_from_item_id(item_ids, start_item_id, no_of_next_items):
        """Get items from a list starting from a specific number."""
        try:
            start_idx = item_ids.index(start_item_id)
            end_idx = min(start_idx + no_of_next_items, len(item_ids))
            return item_ids[start_idx:end_idx]
        except ValueError:
            return []

    def has_monthly_cycle_mode_id(item: dict) -> bool:
        """Check if item has the monthly_cycle mode ID."""
        return item["mode_id"] == 1

    if current_plan_id is not None:
        # eliminate items that are already revisioned in the current plan_id
        eligible_item_ids = [
            i
            for i in recent_items
            if not revisions(
                where=f"item_id = {i} AND mode_id = 1 AND plan_id = {current_plan_id} AND revision_date != '{current_date}'"
            )
        ]
        # TODO: handle the new user that not have any revision/plan_id
        last_added_revision = revisions(
            where=f"revision_date <> '{current_date}' AND mode_id = 1 AND plan_id = {current_plan_id}",
            order_by="revision_date DESC, id DESC",
            limit=1,
        )
        last_added_item_id = (
            last_added_revision[0].item_id if last_added_revision else 0
        )

        next_item_id = find_next_greater(eligible_item_ids, last_added_item_id)
    else:
        eligible_item_ids = []
        next_item_id = 0

    item_ids = get_next_item_range_from_item_id(
        eligible_item_ids, next_item_id, total_display_count
    )

    # take today revision data that are not in listing (item_ids)
    display_conditions = {
        "monthly_cycle": lambda item: (
            has_monthly_cycle_mode_id(item)
            and has_revisions_today(item)
            and item["item_id"] not in item_ids
        )
    }
    today_revisioned_items = list(
        dict.fromkeys(
            i["item_id"] for i in ct if display_conditions["monthly_cycle"](i)
        )
    )

    recent_items = sorted(item_ids + today_revisioned_items)
    return recent_items


######## New Summary Table ########


def render_summary_table(auth, route, mode_ids, item_ids, plan_id=None):
    is_accordion = route != "monthly_cycle"
    mode_id_mapping = {
        "monthly_cycle": 1,
        "new_memorization": 2,
        "recent_review": 3,
        "watch_list": 4,
        "srs": 5,
    }
    mode_id = mode_id_mapping[route]
    is_newly_memorized = mode_id == 2
    is_monthly_review = mode_id == 1
    current_date = get_current_date(auth)
    # This list is to close the accordian, if all the checkboxes are selected
    is_all_selected = []

    def render_range_row(item_id: str):
        row_id = f"{route}-row-{item_id}"
        plan_condition = f"AND plan_id = {plan_id}" if is_monthly_review else ""
        current_revision_data = revisions(
            where=f"revision_date = '{current_date}' AND item_id = {item_id} AND mode_id IN ({", ".join(mode_ids)}) {plan_condition}"
        )
        is_checked = len(current_revision_data) != 0
        is_all_selected.append(is_checked)
        checkbox_hx_attrs = {
            "hx_post": f"/home/add/{item_id}",
            "hx_select": f"#{row_id}",
            # TODO: make the monthly cycle to only rerender on monthly summary table
            "hx_select_oob": f"#stat-row-{mode_id}, #total_row, #{route}-header"
            + (", #monthly_cycle_link_table" if is_monthly_review else ""),
            "hx_target": f"#{row_id}",
            "hx_swap": "outerHTML",
        }
        vals_dict = {"date": current_date, "mode_id": mode_id}
        if is_monthly_review:
            vals_dict["plan_id"] = plan_id
        record_btn = CheckboxX(
            name=f"is_checked",
            value="1",
            **checkbox_hx_attrs,
            hx_vals=vals_dict,
            hx_include=f"#rev-{item_id}",
            checked=is_checked,
            cls=f"{route}_ids",
            _at_click="handleCheckboxClick($event)",  # To handle `shift+click` selection
        )

        if current_revision_data:
            current_rev_data = current_revision_data[0]
            default_rating = current_rev_data.rating
            change_rating_hx_attrs = {
                "hx_put": f"/revision/{current_rev_data.id}",
                "hx_swap": "none",
            }
        else:
            default_rating = 1
            change_rating_hx_attrs = checkbox_hx_attrs
            change_rating_hx_attrs["hx_vals"] = {
                "date": current_date,
                "mode_id": mode_id,
                "is_checked": True,
            }
            if is_monthly_review:
                change_rating_hx_attrs["hx_vals"]["plan_id"] = plan_id

        # This is to show the interval for srs based on the rating
        if mode_id == 5:
            custom_rating_dict = {
                "1": f"✅ Good - {get_interval_based_on_rating(item_id=item_id, rating=1, is_edit=is_checked,is_dropdown=True)}",
                "0": f"😄 Ok - {get_interval_based_on_rating(item_id=item_id, rating=0, is_edit=is_checked,is_dropdown=True)}",
                "-1": f"❌ Bad - {get_interval_based_on_rating(item_id=item_id, rating=-1, is_edit=is_checked,is_dropdown=True)}",
            }
        else:
            custom_rating_dict = RATING_MAP
        rating_dropdown_input = rating_dropdown(
            default_mode=str(default_rating),
            is_label=False,
            rating_dict=custom_rating_dict,
            # cls="[&>div]:h-8 uk-form-sm w-28",
            id=f"rev-{item_id}",
            hx_trigger="change",
            **change_rating_hx_attrs,
        )

        revs = revisions(where=f"item_id = {item_id} AND mode_id = {mode_id}")
        if mode_id == 5:
            rep_denominator = len(get_srs_interval_list(item_id))
        else:
            rep_denominator = 7
        progress = P(Strong(len(revs)), Span(f"/{rep_denominator}"))
        return Tr(
            Td(get_page_description(item_id)),
            Td(
                get_start_text(item_id),
                cls=TextT.lg,
            ),
            Td(progress) if not (is_newly_memorized or is_monthly_review) else None,
            Td(record_btn),
            Td(
                Form(
                    rating_dropdown_input,
                    Hidden(name="item_id", value=item_id),
                    Hidden(name="is_checked", value=f"{is_checked}"),
                    id=f"{route}_ratings",
                )
            ),
            id=row_id,
        )

    body_rows = list(map(render_range_row, item_ids))
    # unique_page_count = len(set(map(get_page_number, item_ids)))
    target_page_count = get_page_count(item_ids=item_ids)
    progress_page_count = get_page_count(
        revisions(where=f"mode_id = {mode_id} and revision_date = '{current_date}'")
    )
    summary_count = render_progress_display(progress_page_count, target_page_count)
    if not body_rows:
        return None

    # This is used on the select_all checkboxes
    select_all_vals = {
        "mode_id": mode_id,
        "date": current_date,
    }
    if is_monthly_review:
        select_all_vals["plan_id"] = plan_id

    render_output = (
        Div(
            Div(
                (
                    A(
                        "Record",
                        href=f"/{route}",
                        hx_boost="false",
                        cls=(AT.classic, TextPresets.bold_sm, "float-right"),
                    )
                    if route != "monthly_cycle"
                    else None
                ),
                cls="w-full",
            ),
            Table(
                Thead(
                    Tr(
                        Th("Page", cls="min-w-24"),
                        Th("Start Text", cls="min-w-24"),
                        (
                            Th("Reps")
                            if not (is_newly_memorized or is_monthly_review)
                            else None
                        ),
                        Th(
                            CheckboxX(
                                name="is_select_all",
                                hx_vals=select_all_vals,
                                hx_post="/home/bulk_add",
                                hx_trigger="change",
                                hx_include=f"#{route}_ratings",
                                hx_select=f"#{route}_tbody",
                                hx_select_oob=f"#stat-row-{mode_id}, #total_row, #{route}-header"
                                + (
                                    ", #monthly_cycle_link_table"
                                    if is_monthly_review
                                    else ""
                                ),
                                hx_target=f"#{route}_tbody",
                                hx_swap="outerHTML",
                                checked=all(is_all_selected),
                                cls=(
                                    "select_all",
                                    ("hidden" if mode_id == 5 else None),
                                ),
                                x_model="selectAll",  # To update the current status of the checkbox (checked or unchecked)
                            )
                        ),
                        Th("Rating", cls="min-w-24"),
                    )
                ),
                Tbody(*body_rows, id=f"{route}_tbody"),
                id=f"{route}_summary_table",
                # defining the reactive data for for component to reference (alpine.js)
                x_data=select_all_with_shift_click_for_summary_table(
                    class_name=f"{route}_ids"
                ),
                # initializing the updateSelectAll function to select the selectAll checkboxe.
                # if all the below checkboxes are selected.
                x_init="updateSelectAll()",
            ),
        ),
    )
    return (
        AccordionItem(
            Span(f"{modes[mode_id].name} - ", summary_count, id=f"{route}-header"),
            render_output,
            open=(not all(is_all_selected)),
        )
        if is_accordion
        else render_output
    )


######## END ########


# This route is responsible for adding and deleting record for the recent_review and watch_list
# and update the review dates for that item_id
@app.post("/home/add/{item_id}")
def update_status_from_index(
    date: str,
    item_id: str,
    mode_id: int,
    rating: int,
    is_checked: bool = False,
    plan_id: int = None,
):
    checkbox_update_logic(
        mode_id=mode_id,
        rating=rating,
        item_id=item_id,
        date=date,
        is_checked=is_checked,
        plan_id=plan_id,
    )
    return RedirectResponse("/", status_code=303)


@app.post("/home/bulk_add")
def update_multiple_items_from_index(
    mode_id: int,
    date: str,
    item_id: list[int],
    rating: list[int],
    is_checked: list[bool],
    plan_id: str = None,
    is_select_all: bool = False,
):
    for o in zip(item_id, rating, is_checked):
        current_item_id, current_rating, current_is_checked = o
        if not is_select_all:
            checkbox_update_logic(
                mode_id=mode_id,
                rating=current_rating,
                item_id=current_item_id,
                date=date,
                is_checked=is_select_all,
                plan_id=plan_id,
            )
        else:
            if not current_is_checked:
                checkbox_update_logic(
                    mode_id=mode_id,
                    rating=current_rating,
                    item_id=current_item_id,
                    date=date,
                    is_checked=is_select_all,
                    plan_id=plan_id,
                )

    return RedirectResponse("/", status_code=303)


@app.post("/new_memorization/update_as_newly_memorized/{item_id}")
def update_status_as_newly_memorized(
    auth, request, item_id: str, is_checked: bool = False, rating: int = None
):
    qry = f"item_id = {item_id} AND mode_id = 2;"
    revisions_data = revisions(where=qry)
    current_date = get_current_date(auth)
    if not revisions_data and is_checked:
        revisions.insert(
            hafiz_id=auth,
            item_id=item_id,
            revision_date=current_date,
            rating=(
                DEFAULT_RATINGS.get("new_memorization") if rating is None else rating
            ),
            mode_id=2,
        )
        # updating the status of the item to memorized
        try:
            hafizs_items_id = hafizs_items(where=f"item_id = {item_id}")[0]
        except IndexError:
            hafizs_items.insert(
                Hafiz_Items(item_id=item_id, page_number=items[item_id].page_id)
            )
        hafizs_items_id = hafizs_items(where=f"item_id = {item_id}")[0].id
        hafizs_items.update(
            {
                "status": "newly_memorized",
                "mode_id": 2,
                # "last_review": current_date,
                # "next_review": add_days_to_date(current_date, 1),
            },
            hafizs_items_id,
        )
    elif revisions_data and not is_checked:
        revisions.delete(revisions_data[0].id)
        hafizs_items_data = hafizs_items(
            where=f"item_id = {item_id} AND hafiz_id= {auth}"
        )[0]
        del hafizs_items_data.status
        hafizs_items_data.mode_id = 1
        hafizs_items.update(hafizs_items_data)

    populate_hafizs_items_stat_columns(item_id=item_id)
    referer = request.headers.get("Referer")
    return RedirectResponse(referer, status_code=303)


@app.post("/new_memorization/bulk_update_as_newly_memorized")
def bulk_update_status_as_newly_memorized(
    request, item_ids: list[int], auth, rating: int = None
):  # for query string format
    current_date = get_current_date(auth)

    for item_id in item_ids:
        revisions.insert(
            hafiz_id=auth,
            item_id=item_id,
            revision_date=current_date,
            rating=(
                DEFAULT_RATINGS.get("new_memorization") if rating is None else rating
            ),
            mode_id=2,
        )

        try:
            hafizs_items_id = hafizs_items(where=f"item_id = {item_id}")[0]
        except IndexError:
            hafizs_items.insert(
                Hafiz_Items(item_id=item_id, page_number=items[item_id].page_id)
            )
        hafizs_items_id = hafizs_items(where=f"item_id = {item_id}")[0].id
        hafizs_items.update(
            {
                "status": "newly_memorized",
                "mode_id": 2,
                # "last_review": current_date,
                # "next_review": add_days_to_date(current_date, 1),
            },
            hafizs_items_id,
        )

    populate_hafizs_items_stat_columns(item_id=item_id)
    referer = request.headers.get("Referer")
    return Redirect(referer)


@app.get("/tables")
def list_tables(auth):
    return tables_main_area(auth=auth)


@app.get("/tables/{table}")
def view_table(table: str, auth):
    records = db.q(f"SELECT * FROM {table}")
    columns = get_column_headers(table)

    def _render_rows(data: dict):
        def render_cell(column: str):
            if column == "id":
                return Td(
                    A(
                        data[column],
                        href=f"/tables/{table}/{data[column]}/edit",
                        cls=AT.muted,
                    )
                )
            return Td(data[column])

        return Tr(
            *map(render_cell, columns),
            Td(
                A(
                    "Delete",
                    hx_delete=f"/tables/{table}/{data["id"]}",
                    target_id=f"row-{data["id"]}",
                    hx_swap="outerHTML",
                    hx_confirm="Are you sure?",
                    cls=AT.muted,
                ),
            ),
            id=f"row-{data["id"]}",
        )

    table_element = Table(
        Thead(Tr(*map(Th, columns), Th("Action"))),
        Tbody(*map(_render_rows, records)),
    )
    return tables_main_area(
        Div(
            DivFullySpaced(
                DivLAligned(
                    A(
                        UkIcon("undo-2", height=15, width=15),
                        cls="px-6 py-3 shadow-md rounded-sm",
                        href=f"/tables",
                    ),
                    A(
                        Button("New", type="button", cls=ButtonT.link),
                        href=f"/tables/{table}/new",
                    ),
                ),
                DivRAligned(
                    A(
                        Button("Export", type="button", cls=ButtonT.link),
                        href=f"/tables/{table}/export",
                        hx_boost="false",
                    ),
                    A(
                        Button("Import", type="button", cls=ButtonT.link),
                        href=f"/tables/{table}/import",
                    ),
                ),
            ),
            Div(table_element, cls="uk-overflow-auto"),
            cls="space-y-3",
        ),
        active_table=table,
        auth=auth,
    )


def create_dynamic_input_form(schema: dict, **kwargs):
    input_types_map = {"int": "number", "str": "text", "date": "date"}

    def create_input_field(o: dict):
        column, datatype = o
        if column == "id":
            return None
        # datatype is an union type, so we need to extract the first element using __args__
        # and it returns datatype class so to get the name we'll use __name__ attribute
        datatype = datatype.__args__[0].__name__
        input_type = input_types_map.get(datatype, "text")
        # The datatype for the date column are stored in str
        # so we are checking if the 'date'  is in the column name
        if "date" in column:
            input_type = "date"
        # The bool datatype is stored in int
        # so we are creating a column list that are bool to compare against column name
        if column in ["completed"]:
            return Div(
                FormLabel(column),
                LabelRadio(label="True", id=f"{column}-1", name=column, value="1"),
                LabelRadio(label="False", id=f"{column}-2", name=column, value="0"),
                cls="space-y-2",
            )
        if column in ["role", "age_group", "relationship"]:
            return (
                LabelSelect(
                    *map(render_options, OPTION_MAP[column]),
                    label=column.capitalize(),
                    name=column,
                ),
            )
        return LabelInput(column, type=input_type)

    return Form(
        *map(create_input_field, schema.items()),
        DivFullySpaced(
            Button("Save"),
            A(Button("Discard", type="button"), onclick="history.back()"),
        ),
        **kwargs,
        cls="space-y-4",
    )


@app.get("/tables/{table}/{record_id}/edit")
def edit_record_view(table: str, record_id: int, auth):
    current_table = tables[table]
    current_data = current_table[record_id]

    # The completed column is stored in int and it is considered as bool
    # so we are converting it to str in order to select the right radio button using fill_form
    if table == "plans":
        current_data.completed = str(current_data.completed)

    column_with_types = get_column_and_its_type(table)
    # The redirect_link is when we edit the description from the different page it should go back to that page
    form = create_dynamic_input_form(
        column_with_types,
        hx_put=f"/tables/{table}/{record_id}",
        hx_target="body",
        hx_push_url="true",
        hx_vals={"redirect_link": f"/tables/{table}"},
    )

    return tables_main_area(
        Titled(f"Edit page", fill_form(form, current_data)),
        active_table=table,
        auth=auth,
    )


def get_column_and_its_type(table):
    data_class = tables[table].dataclass()
    return data_class.__dict__["__annotations__"]


@app.put("/tables/{table}/{record_id}")
async def update_record(table: str, record_id: int, redirect_link: str, req: Request):
    formt_data = await req.form()
    current_data = formt_data.__dict__.get("_dict")
    # replace the value to none in order to set it as unset if the value is empty
    current_data = {
        key: (value if value != "" else None)
        for key, value in current_data.items()
        if key != "redirect_link"
    }

    tables[table].update(current_data, record_id)

    return RedirectResponse(redirect_link, status_code=303)


@app.delete("/tables/{table}/{record_id}")
def delete_record(table: str, record_id: int):
    try:
        tables[table].delete(record_id)
    except Exception as e:
        return Tr(Td(P(f"Error: {e}"), colspan="11", cls="text-center"))


@app.get("/tables/{table}/new")
def new_record_view(table: str, auth):
    column_with_types = get_column_and_its_type(table)
    return tables_main_area(
        Titled(
            f"Add page",
            create_dynamic_input_form(column_with_types, hx_post=f"/tables/{table}"),
        ),
        active_table=table,
        auth=auth,
    )


@app.post("/tables/{table}")
async def create_new_record(table: str, req: Request):
    formt_data = await req.form()
    current_data = formt_data.__dict__.get("_dict")
    tables[table].insert(current_data)
    return Redirect(f"/tables/{table}")


@app.get("/tables/{table}/export")
def export_specific_table(table: str):
    df = pd.DataFrame(tables[table](), columns=get_column_and_its_type(table).keys())

    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False, header=True)
    csv_buffer.seek(0)

    file_name = f"{table}.csv"
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )


@app.get("/tables/{table}/import")
def import_specific_table_view(table: str):
    form = Form(
        UploadZone(
            DivCentered(Span("Upload Zone"), UkIcon("upload")),
            id="file",
            accept="text/csv",
        ),
        DivFullySpaced(
            Button("Submit"),
            Button(
                "Preview",
                type="button",
                hx_post=f"/tables/{table}/import/preview",
                hx_include="#file",
                hx_encoding="multipart/form-data",
                target_id="preview_table",
                hx_push_url="false",
            ),
            Button("Cancel", type="button", onclick="history.back()"),
        ),
        action=f"/tables/{table}/import",
        method="POST",
    )
    return tables_main_area(
        Titled(
            f"Upload CSV",
            P(
                f"CSV should contain only these columns: ",
                Span(
                    " ,".join(get_column_headers(table)), cls=TextPresets.md_weight_sm
                ),
            ),
            form,
            Div(id="preview_table"),
            cls="space-y-4",
        ),
        active_table=table,
    )


@app.post("/tables/{table}/import/preview")
async def import_specific_table_preview(table: str, file: UploadFile):
    file_content = await file.read()
    imported_df = pd.read_csv(BytesIO(file_content)).fillna("")
    columns = imported_df.columns.tolist()
    records = imported_df.to_dict(orient="records")

    # Check if the columns match the table's columns
    if sorted(columns) != sorted(get_column_headers(table)):
        return Div(
            H3("Filename: ", file.filename),
            P("Please check the columns in the CSV file", cls="text-red-500"),
        )

    def _render_rows(data: dict):
        return Tr(
            *map(lambda col: Td(data[col]), columns),
        )

    preview_table = Table(
        Thead(Tr(*map(Th, columns))),
        Tbody(*map(_render_rows, records)),
    )
    return Div(H3("Filename: ", file.filename), Div(preview_table))


@app.post("/tables/{table}/import")
async def import_specific_table(table: str, file: UploadFile):
    backup_sqlite_db(DB_PATH, "data/backup")
    # Instead of using the import_file method, we are using upsert method to import the csv file
    # as some of the forign key values are being used in another table
    # so we cannot truncate the table
    file_content = await file.read()
    data = pd.read_csv(BytesIO(file_content)).to_dict("records")
    for record in data:
        tables[table].upsert(record)

    return Redirect(f"/tables/{table}")


# this function is used to create infinite scroll for the revisions table
def generate_revision_table_part(part_num: int = 1, size: int = 20) -> Tuple[Tr]:
    start = (part_num - 1) * size
    end = start + size
    data = revisions(order_by="id desc")[start:end]

    def _render_rows(rev: Revision):
        item_id = rev.item_id
        item_details = items[item_id]
        page = item_details.page_id
        return Tr(
            Td(
                CheckboxX(
                    name="ids",
                    value=rev.id,
                    cls="revision_ids",
                    # To trigger the checkboxChanged event to the bulk edit and bulk delete buttons
                    _="on click send checkboxChanged to .toggle_btn",
                    _at_click="handleCheckboxClick($event)",
                )
            ),
            Td(
                A(
                    page,
                    href=f"/revision/edit/{rev.id}",
                    cls=AT.muted,
                )
            ),
            # FIXME: Added temporarly to check is the date is added correctly and need to remove this
            Td(item_details.part),
            Td(rev.mode_id),
            Td(rev.plan_id),
            Td(render_rating(rev.rating)),
            Td(get_surah_name(item_id=item_id)),
            Td(pages[page].juz_number),
            Td(date_to_human_readable(rev.revision_date)),
            Td(
                A(
                    "Delete",
                    hx_delete=f"/revision/delete/{rev.id}",
                    target_id=f"revision-{rev.id}",
                    hx_swap="outerHTML",
                    hx_confirm="Are you sure?",
                    cls=AT.muted,
                ),
            ),
            id=f"revision-{rev.id}",
        )

    paginated = [_render_rows(i) for i in data]

    if len(paginated) == 20:
        paginated[-1].attrs.update(
            {
                "get": f"revision?idx={part_num + 1}",
                "hx-trigger": "revealed",
                "hx-swap": "afterend",
                "hx-select": "tbody > tr",
            }
        )
    return tuple(paginated)


@app.get
def revision(auth, idx: int | None = 1):
    table = Table(
        Thead(
            Tr(
                Th(),  # empty header for checkbox
                Th("Page"),
                Th("Part"),
                # FIXME: Added temporarly to check is the date is added correctly and need to remove this
                Th("Mode"),
                Th("Plan Id"),
                Th("Rating"),
                Th("Surah"),
                Th("Juz"),
                Th("Revision Date"),
                Th("Action"),
            )
        ),
        Tbody(*generate_revision_table_part(part_num=idx)),
        x_data=select_all_checkbox_x_data(class_name="revision_ids"),
    )
    return main_area(
        # To send the selected revision ids for bulk delete and bulk edit
        Form(
            action_buttons(),
            Div(table, cls="uk-overflow-auto"),
        ),
        active="Revision",
        auth=auth,
    )


def create_revision_form(type, auth, backlink="/"):

    def _option(obj):
        return Option(
            f"{obj.id} ({obj.name})",
            value=obj.id,
            # FIXME: Temp condition for selecting siraj, later it should be handled by sess
            # Another caviat is that siraj should be in the top of the list of users
            # or else the edit functionality will not work properly.
            selected=True if "siraj" in obj.name.lower() else False,
        )

    additional_fields = (
        LabelInput(
            "Revision Date",
            name="revision_date",
            type="date",
            value=get_current_date(auth),
            cls="space-y-2 col-span-2",
        ),
    )

    return Form(
        Hidden(name="id"),
        Hidden(name="item_id"),
        Hidden(name="plan_id"),
        # Hide the User selection temporarily
        LabelSelect(
            *map(_option, hafizs()), label="Hafiz Id", name="hafiz_id", cls="hidden"
        ),
        *additional_fields,
        rating_radio(),  # single entry
        Div(
            Button("Save", name="backlink", value=backlink, cls=ButtonT.primary),
            A(Button("Cancel", type="button", cls=ButtonT.secondary), href=backlink),
            cls="flex justify-around items-center w-full",
        ),
        action=f"/revision/{type}",
        method="POST",
    )


@rt("/revision/edit/{revision_id}")
def get(revision_id: int, auth, req):
    current_revision = revisions[revision_id].__dict__
    # Convert rating to string in order to make the fill_form to select the option.
    current_revision["rating"] = str(current_revision["rating"])
    item_id = current_revision["item_id"]
    form = create_revision_form(
        "edit", auth=auth, backlink=req.headers.get("referer", "/")
    )
    return main_area(
        Titled(
            (
                "Edit => ",
                get_page_description(item_id),
                f" - {items[item_id].start_text}",
            ),
            fill_form(form, current_revision),
        ),
        active="Revision",
        auth=auth,
    )


@rt("/revision/edit")
def post(revision_details: Revision, backlink: str, auth):
    # setting the plan_id to None if it is 0
    # as it get defaults to 0 if the field is empty.
    revision_details.plan_id = set_zero_to_none(revision_details.plan_id)
    current_revision = revisions.update(revision_details)
    update_stats_and_interval(
        item_id=current_revision.item_id,
        mode_id=current_revision.mode_id,
        current_date=get_current_date(auth),
    )
    return Redirect(backlink)


@rt("/revision/delete/{revision_id}")
def delete(revision_id: int, auth):
    current_revision = revisions[revision_id]
    revisions.delete(revision_id)
    update_stats_and_interval(
        item_id=current_revision.item_id,
        mode_id=current_revision.mode_id,
        current_date=get_current_date(auth),
    )


@app.delete("/revision")
def revision_delete_all(ids: List[int], auth):
    for id in ids:
        current_revision = revisions[id]
        revisions.delete(id)
        update_stats_and_interval(
            item_id=current_revision.item_id,
            mode_id=current_revision.mode_id,
            current_date=get_current_date(auth),
        )
    return RedirectResponse(revision, status_code=303)


# This is to handle the checkbox on revison page as it was coming as individual ids.
@app.post("/revision/bulk_edit")
def bulk_edit_redirect(ids: List[str]):
    return RedirectResponse(f"/revision/bulk_edit?ids={','.join(ids)}", status_code=303)


@app.get("/revision/bulk_edit")
def bulk_edit_view(ids: str, auth):
    ids = ids.split(",")

    # Get the default values from the first selected revision
    first_revision = revisions[ids[0]]

    def _render_row(id):
        current_revision = revisions[id]
        current_item_id = current_revision.item_id
        item_details = items[current_item_id]
        return Tr(
            Td(get_page_description(current_item_id)),
            # Td(P(item_details.page_id)),
            # Td(P(item_details.surah_name)),
            # Td(P(item_details.part)),
            Td(P(item_details.start_text, cls=TextT.lg)),
            # Td(P(current_revision.revision_date)),
            # Td(P(current_revision.mode_id)),
            # Td(P(current_revision.plan_id)),
            Td(
                CheckboxX(
                    name="ids",
                    value=id,
                    cls="revision_ids",
                    # _at_ is a alias for @
                    _at_click="handleCheckboxClick($event)",  # To handle `shift+click` selection
                )
            ),
            Td(
                rating_dropdown(
                    default_mode=str(current_revision.rating),
                    name=f"rating-{id}",
                    is_label=False,
                ),
                cls="min-w-32",
            ),
        )

    table = Table(
        Thead(
            Tr(
                Th("Page"),
                # Th("Surah"),
                # Th("Part"),
                Th("Start Text"),
                # Th("Date"),
                # Th("Mode"),
                # Th("Plan ID"),
                Th(
                    CheckboxX(
                        cls="select_all",
                        x_model="selectAll",  # To update the current status of the checkbox (checked or unchecked)
                        _at_change="toggleAll()",  # based on that update the status of all the checkboxes
                    )
                ),
                Th("Rating"),
            )
        ),
        Tbody(*[_render_row(i) for i in ids]),
        # defining the reactive data for for component to reference (alpine.js)
        x_data=select_all_checkbox_x_data(class_name="revision_ids"),
        # initializing the toggleAll function to select all the checkboxes by default.
        x_init="toggleAll()",
    )

    action_buttons = Div(
        Button("Save", cls=ButtonT.primary),
        Button(
            "Cancel", type="button", cls=ButtonT.secondary, onclick="history.back()"
        ),
        Button(
            "Delete",
            hx_delete="/revision",
            hx_confirm="Are you sure you want to delete these revisions?",
            hx_target="body",
            hx_push_url="true",
            cls=ButtonT.destructive,
        ),
        cls=(FlexT.block, FlexT.around, FlexT.middle, "w-full"),
    )

    return main_area(
        H1("Bulk Edit Revision"),
        Form(
            # We don't need to send it because not update the mode_id and plan_id
            # Hidden(name="mode_id", value=first_revision.mode_id),
            # Hidden(name="plan_id", value=first_revision.plan_id),
            Div(
                LabelInput(
                    "Revision Date",
                    name="revision_date",
                    type="date",
                    value=first_revision.revision_date,
                    cls="space-y-2 w-full",
                ),
            ),
            Div(table, cls="uk-overflow-auto"),
            action_buttons,
            action="/revision",
            method="POST",
        ),
        active="Revision",
        auth=auth,
    )


@app.post("/revision")
async def bulk_edit_save(revision_date: str, req, auth):
    form_data = await req.form()
    ids_to_update = form_data.getlist("ids")

    for name, value in form_data.items():
        if name.startswith("rating-"):
            current_id = name.split("-")[1]
            if current_id in ids_to_update:
                revisions.update(
                    Revision(
                        id=int(current_id),
                        rating=int(value),
                        revision_date=revision_date,
                    )
                )
                update_stats_and_interval(
                    item_id=revisions[int(current_id)].item_id,
                    mode_id=mode_id,
                    current_date=get_current_date(auth),
                )

    return RedirectResponse("/revision", status_code=303)


def parse_page_string(page_str: str):
    """
    Formats supported:
    - "5" -> (5, 0, 0)
    - "5.2" -> (5, 2, 0)
    - "5-10" -> (5, 0, 10)
    - "5.2-10" -> (5, 2, 10)
    """
    page = page_str
    part = 0
    length = 0

    # Extract length if present (handle range)
    if "-" in page:
        page, length_str = page.split("-")
        length = int(length_str) if length_str else length

    # Extract part if present
    if "." in page:
        page, part_str = page.split(".")
        part = int(part_str) if part_str else part

    return int(page), part, length


@rt("/revision/add")
def get(
    auth,
    plan_id: int,
    item_id: int = None,
    page: str = None,
    max_page: int = 605,
    date: str = None,
):
    if item_id is not None:
        page = get_page_number(item_id)
    elif page is not None:
        # for the single entry, we don't need to use lenght
        page, page_part, length = parse_page_string(page)
        if page >= max_page:
            # if page is invalid then redirect to index
            return Redirect(index)
        item_list = get_item_id(page_number=page)
        # To start the page from beginning even if there is multiple parts
        item_id = item_list[0]

        if page_part:
            # if page_part is 0 or greater than expected value, then redirect to show bulk entry page
            if page_part == 0 or len(item_list) < page_part:
                item_id = item_list[0]
                return Redirect(
                    f"/revision/bulk_add?item_id={item_id}&plan_id={plan_id}&is_part=1"
                )
            else:
                # otherwise show the current page part
                current_page_part = items(where=f"page_id = {page} and active = 1")
                # get the given page_part using index
                item_id = current_page_part[page_part - 1].id
                #  if page has parts then show all decendent parts (full page)
        else:
            if len(item_list) > 1:
                return Redirect(
                    f"/revision/bulk_add?item_id={item_id}&plan_id={plan_id}&is_part=1"
                )
    else:
        return Redirect(index)

    return main_area(
        Titled(
            get_page_description(
                item_id, is_bold=False, custom_text=f" - {items[item_id].start_text}"
            ),
            fill_form(
                create_revision_form("add", auth=auth),
                {
                    "item_id": item_id,
                    "plan_id": plan_id,
                    "revision_date": date,
                },
            ),
        ),
        active="Home",
        auth=auth,
    )


@rt("/revision/add")
def post(revision_details: Revision):
    # The id is set to zero in the form, so we need to delete it
    # before inserting to generate the id automatically
    del revision_details.id
    revision_details.plan_id = set_zero_to_none(revision_details.plan_id)
    revision_details.mode_id = 1

    item_id = revision_details.item_id

    # updating the status of the item to memorized
    hafizs_items_id = hafizs_items(where=f"item_id = {item_id}")[0].id
    hafizs_items.update({"status": "memorized"}, hafizs_items_id)

    rev = revisions.insert(revision_details)
    populate_hafizs_items_stat_columns(item_id=item_id)

    next_item_id = find_next_item_id(item_id)

    # get the next page item ids using next_item_id
    next_page_item_ids = get_item_id(page_number=get_page_number(next_item_id))
    # check if the next page contains multiple items
    is_next_page_is_part = len(next_page_item_ids) > 1

    # if the next page contains multiple items, redirect to bulk revision page
    if is_next_page_is_part:
        return Redirect(
            f"/revision/bulk_add?item_id={next_item_id}&revision_date={rev.revision_date}&plan_id={rev.plan_id}&is_part=1"
        )

    # if the next page has only one item, redirect to single item revision page
    return Redirect(
        f"/revision/add?item_id={find_next_item_id(item_id)}&date={rev.revision_date}&plan_id={rev.plan_id}"
    )


# This is to update the rating from the summary table
@app.put("/revision/{rev_id}")
def update_revision_rating(rev_id: int, rating: int):
    revisions.update({"rating": rating}, rev_id)

    current_revision = revisions[rev_id]
    item_id = current_revision.item_id
    # The recalculation is not need as we are editing the rating for the current_date
    if current_revision.mode_id == 5:
        next_interval = get_interval_based_on_rating(item_id, rating, is_edit=True)

        # Update the next_interval, as it is the only column which is based on the rating
        revisions.update({"next_interval": next_interval}, rev_id)

        current_hafiz_item = get_hafizs_items(item_id)
        current_hafiz_item.next_interval = next_interval
        current_hafiz_item.next_review = add_days_to_date(
            current_revision.revision_date, next_interval
        )
        hafizs_items.update(current_hafiz_item)
    populate_hafizs_items_stat_columns(item_id=item_id)


# Bulk add
@app.get("/revision/bulk_add")
def get(
    auth,
    plan_id: int,
    item_id: int = None,
    # page: int = None,
    page: str = None,
    length: int = 0,
    # is_part is to determine whether it came from single entry page or not
    is_part: bool = False,
    revision_date: str = None,
    max_item_id: int = get_last_item_id(),
    max_page_id: int = 605,
):

    if revision_date is None:
        revision_date = get_current_date(auth)

    # This is to handle the empty and negative value of `No of page`
    if not length or length < 0:
        length = get_display_count(auth)

    # process item_id and page_id
    if item_id is not None:
        page = get_page_number(item_id)
        item_id = get_item_id(page_number=page)[0]
    elif page is not None:
        page, part, length = parse_page_string(page)

        if page >= max_page_id:
            return Redirect(index)

        # if length is not given or invalid value, then set it to default value
        # TODO: Later: handle this in the parse_page_string function
        if not length or length <= 0:
            length = int(get_display_count(auth))

        item_list = get_item_id(page_number=page)
        item_id = item_list[0]

        if part:
            # if part is 0 or greater than expected value, then take first item_id and it redirect to show bulk entry page
            if part == 0 or len(item_list) < part:
                item_id = item_id
            else:
                # otherwise, show the that page-part
                current_page_part = items(where=f"page_id = {page} and active = 1")
                # get the given page_part using index
                item_id = current_page_part[part - 1].id

    # This is to show only one page if it came from single entry
    if is_part:
        length = 1

    last_page = page + length

    item_ids = flatten_list(
        [get_item_id(page_number=p) for p in range(page, last_page)]
    )
    # To start from the not added item id
    if item_id in item_ids:
        item_ids = item_ids[item_ids.index(item_id) :]

    # This is to set the upper limit for continuation logic
    # To prevent the user from adding already added pages twice
    if max_item_id in item_ids:
        if not item_ids[-1] == max_item_id:
            item_ids = item_ids[: item_ids.index(max_item_id)]

    _temp_item_ids = []
    page_surah = get_surah_name(item_id=item_id)
    page_juz = get_juz_name(item_id=item_id)

    for _item_id in item_ids:
        current_surah = get_surah_name(item_id=_item_id)
        current_juz = get_juz_name(item_id=_item_id)

        if current_surah != page_surah and current_juz != page_juz:
            _temp_item_ids.append(f"{page_surah} surah and Juz {page_juz} ends")
            page_surah, page_juz = current_surah, current_juz
        elif current_surah != page_surah:
            _temp_item_ids.append(f"{page_surah} surah ends")
            page_surah = current_surah
        elif current_juz != page_juz:
            _temp_item_ids.append(f"Juz {page_juz} ends")
            page_juz = current_juz

        _temp_item_ids.append(_item_id)

    if _temp_item_ids:
        item_ids = _temp_item_ids

    def _render_row(current_item_id):
        # This is to render the description such as surah and juz end-0
        if isinstance(current_item_id, str):
            return Tr(Td(P(current_item_id), colspan="5", cls="text-center"))

        current_page_details = items[current_item_id]
        return Tr(
            Td(get_page_description(current_item_id)),
            Td(P(current_page_details.start_text, cls=(TextT.lg))),
            Td(
                CheckboxX(
                    name="ids",
                    value=current_item_id,
                    cls="revision_ids",
                    _at_click="handleCheckboxClick($event)",
                )
            ),
            Td(
                rating_dropdown(is_label=False, name=f"rating-{current_item_id}"),
                cls="!pr-0 min-w-32",
            ),
        )

    table = Table(
        Thead(
            Tr(
                Th("Page"),
                Th("Start Text"),
                Th(
                    CheckboxX(
                        cls="select_all", x_model="selectAll", _at_change="toggleAll()"
                    )
                ),
                Th("Rating"),
            )
        ),
        Tbody(*map(_render_row, item_ids)),
        x_data=select_all_checkbox_x_data(
            class_name="revision_ids",
            is_select_all="false" if is_part else "true",
        ),
        x_init="toggleAll()",
    )

    action_buttons = Div(
        Button(
            "Save",
            cls=ButtonT.primary,
        ),
        A(Button("Cancel", type="button", cls=ButtonT.secondary), href=index),
        cls=(FlexT.block, FlexT.around, FlexT.middle, "w-full"),
    )

    # This is to render the surah and juz based in the lenth
    def get_description(type):
        get_type_function = {
            "surah": get_surah_name,
            "juz": get_juz_name,
            "page": get_page_number,
        }
        if type not in get_type_function.keys():
            return ""

        unique_type = list(
            dict.fromkeys(
                [
                    get_type_function[type](item_id=item_id)
                    for item_id in item_ids
                    if isinstance(item_id, int)
                ]
            )
        )
        if len(unique_type) == 1:
            return unique_type[0]
        else:
            return f"{unique_type[0]} => {unique_type[-1]}"

    surah_description = get_description("surah")
    juz_description = get_description("juz")
    page_description = get_description("page")

    return main_area(
        Div(
            # This will show in the desktop view
            H1(
                f"{page_description} - {surah_description} - Juz {juz_description}",
                cls="hidden md:block",
            ),
            # This will show in the mobile view
            Div(
                H2(page_description),
                H2(surah_description),
                H2(f"Juz {juz_description}"),
                cls="[&>*]:font-extrabold space-y-2 block md:hidden",
            ),
            id="header_area",
        ),
        Form(
            Hidden(name="is_part", value=str(is_part)),
            Hidden(name="plan_id", value=plan_id),
            Hidden(name="max_item_id", value=max_item_id),
            LabelInput(
                "Revision Date",
                name="revision_date",
                type="date",
                value=revision_date,
                cls=("space-y-2 col-span-2"),
            ),
            Div(table, cls="uk-overflow-auto", id="table-container"),
            action_buttons,
            action="/revision/bulk_add",
            method="POST",
            onkeydown="if(event.key === 'Enter') event.preventDefault();",
        ),
        Script(src="/public/script.js"),
        active="Home",
        auth=auth,
    )


@rt("/revision/bulk_add")
async def post(
    revision_date: str,
    plan_id: int,
    is_part: bool,
    max_item_id: int,
    auth,
    req,
    length: int = 0,
):
    plan_id = set_zero_to_none(plan_id)
    form_data = await req.form()
    item_ids = form_data.getlist("ids")

    parsed_data = []
    for name, value in form_data.items():
        if name.startswith("rating-"):
            item_id = name.split("-")[1]
            if item_id in item_ids:
                hafizs_items_id = hafizs_items(where=f"item_id = {item_id}")[0].id
                hafizs_items.update({"status": "memorized"}, hafizs_items_id)
                parsed_data.append(
                    Revision(
                        item_id=int(item_id),
                        rating=int(value),
                        hafiz_id=auth,
                        revision_date=revision_date,
                        mode_id=1,
                        plan_id=plan_id,
                    )
                )

    revisions.insert_all(parsed_data)

    # Update the stat columns for the added items
    for rec in parsed_data:
        populate_hafizs_items_stat_columns(item_id=rec.item_id)

    if parsed_data:
        last_item_id = parsed_data[-1].item_id
    else:
        # This is to get the last value from the table to get the next item id
        # If none were selected
        rating_date = [
            name for name, value in form_data.items() if name.startswith("rating-")
        ][::-1]
        if rating_date:
            last_item_id = int(rating_date[0].split("-")[1])
        else:
            return Redirect(index)

    next_item_id = find_next_item_id(last_item_id)

    # if there is no next item id, then we are done with the revision
    # and handling the upper limit logic
    if next_item_id is None or next_item_id >= max_item_id:
        return Redirect(index)

    # get the next page item ids using next_item_id
    next_page_item_ids = get_item_id(page_number=get_page_number(next_item_id))
    # check if the next page contains multiple items
    is_next_page_is_part = len(next_page_item_ids) > 1

    # if current item is is_part,
    # and the next page has only one item, redirect to single item revision page
    if is_part and not is_next_page_is_part:
        return Redirect(
            f"/revision/add?item_id={next_item_id}&date={revision_date}&plan_id={plan_id}"
        )

    # if current item is is_part,
    # and the next page contains multiple items, redirect to bulk revision page
    if is_part and is_next_page_is_part:
        return Redirect(
            f"/revision/bulk_add?item_id={next_item_id}&revision_date={revision_date}&plan_id={plan_id}&is_part=1"
        )
    return Redirect(
        f"/revision/bulk_add?item_id={next_item_id}&revision_date={revision_date}&length={length}&plan_id={plan_id}&max_item_id={max_item_id}"
    )


@app.get("/profile/{current_type}")
def show_page_status(current_type: str, auth, sess, status: str = ""):

    # This query will return all the missing items for that hafiz
    # and we will add the items in to the hafizs_items table
    qry = f"""
    SELECT items.id from items
    LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth} 
    WHERE items.active <> 0 AND hafizs_items.item_id IS Null;
    """
    ct = db.q(qry)
    missing_item_ids = [r["id"] for r in ct]

    if missing_item_ids:
        for missing_item_id in missing_item_ids:
            hafizs_items.insert(
                item_id=missing_item_id,
                page_number=get_page_number(missing_item_id),
                mode_id=1,
            )

    def render_row_based_on_type(type_number: str, records: list, current_type):
        status_name = records[0]["status"]
        status_value = (
            status_name.replace("_", " ").title()
            if status_name is not None
            else "Not Memorized"
        )
        if status and status != standardize_column(status_value):
            return None

        _surahs = sorted({r["surah_id"] for r in records})
        _pages = sorted([r["page_number"] for r in records])
        _juzs = sorted({r["juz_number"] for r in records})

        surah_range = render_type_description(_surahs, "Surah")
        page_range = render_type_description(_pages, "Page")
        juz_range = render_type_description(_juzs, "Juz")

        if current_type == "juz":
            details = [surah_range, page_range]
            details_str = f"{surah_range} ({page_range})"
        elif current_type == "surah":
            details = [juz_range, page_range]
            details_str = f"{juz_range} ({page_range})"
        elif current_type == "page":
            details = [juz_range, surah_range]
            details_str = f"{juz_range} | {surah_range}"

        title = (
            f"{current_type.capitalize()} {type_number}"
            if current_type != "surah"
            else surahs[type_number].name
        )
        item_length = 1
        existing_status = standardize_column(status_value)
        status_filter = (
            "status IS NULL"
            if existing_status == "not_memorized"
            else f"status = '{existing_status}'"
        )

        if current_type == "page":
            where_clause = f"page_number={type_number} and hafiz_id={auth}"
            if status:
                where_clause += f" and {status_filter}"
            item_length = len(hafizs_items(where=where_clause) or [])

        elif current_type in ("surah", "juz"):
            item_ids = grouped.get(type_number, [])
            if item_ids:
                if len(item_ids) > 1:
                    item_id_list = ",".join(str(i["id"]) for i in item_ids)
                    where_clause = f"item_id IN ({item_id_list}) and hafiz_id={auth}"
                    if status:
                        where_clause += f" and {status_filter}"
                    item_length = len(hafizs_items(where=where_clause) or [])

        show_customize_button = item_length > 1
        return Tr(
            Td(title),
            Td(details[0]),
            Td(details[1]),
            # Td(
            #     Form(
            #         # This hidden input is to send the id to the backend even if it is unchecked
            #         Hidden(name=f"{current_type}-{type_number}", value="0"),
            #         CheckboxX(
            #             name=f"{current_type}-{type_number}",
            #             value="1",
            #             cls="profile_rows",  # Alpine js reference
            #             _at_click="handleCheckboxClick($event)",
            #         ),
            #         hx_post=f"/update_checkbox/{current_type}/{type_number}/{status}",
            #         hx_trigger="click",
            #         onClick="return false",
            #         hx_select=f"#{current_type}-{type_number}",
            #         hx_target=f"#{current_type}-{type_number}",
            #         hx_swap="outerHTML",
            #         hx_select_oob="#stats_info",
            #     )
            # ),
            Td(
                Form(
                    Hidden(name="filter_status", value=status),
                    status_dropdown(status_value),
                    hx_post=f"/profile/update_status/{current_type}/{type_number}",
                    hx_target=f"#{current_type}-{type_number}",
                    hx_select=f"#{current_type}-{type_number}",
                    hx_select_oob="#stats_info",
                    hx_swap="outerHTML",
                    hx_trigger="change",
                )
            ),
            # Td(status_value),
            (
                Td(
                    A("Customize ➡️"),
                    cls=(AT.classic, "text-right"),
                    hx_get=f"/profile/custom_status_update/{current_type}/{type_number}"
                    + (f"?status={status}" if status else ""),
                    hx_vals={
                        "title": title,
                        "description": details_str,
                        "filter_status": status,
                    },
                    target_id="my-modal-body",
                    data_uk_toggle="target: #my-modal",
                )
                if show_customize_button
                else Td("")
            ),
            id=f"{current_type}-{type_number}",
        )

    if not current_type:
        current_type = "juz"

    def render_navigation_item(_type: str):
        return Li(
            A(
                f"by {_type}",
                href=f"/profile/{_type}" + (f"?status={status}" if status else ""),
            ),
            cls=("uk-active" if _type == current_type else None),
        )

    qry = f"""SELECT items.id, items.surah_id, pages.page_number, pages.juz_number, hafizs_items.status FROM items 
                          LEFT JOIN pages ON items.page_id = pages.id
                          LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
                          WHERE items.active != 0;"""

    if status in ["memorized", "newly_memorized"]:
        status_condition = f" AND hafizs_items.status = '{status}'"
    elif status == "not_memorized":
        status_condition = " AND hafizs_items.status IS NULL"
    else:
        status_condition = ""
    query_with_status = qry.replace(";", f" {status_condition};")

    qry_data = db.q(query_with_status if status else qry)

    grouped = group_by_type(qry_data, current_type)
    rows = [
        render_row_based_on_type(type_number, records, current_type)
        for type_number, records in grouped.items()
    ]

    def render_filter_btn(text):
        return Label(
            text,
            hx_get=f"/profile/{current_type}?status={standardize_column(text)}",
            hx_target="body",
            hx_push_url="true",
            cls=(
                "cursor-pointer",
                (
                    LabelT.primary
                    if status == standardize_column(text)
                    else LabelT.secondary
                ),
            ),
        )

    filter_btns = DivLAligned(
        P("Status Filter:", cls=TextPresets.muted_sm),
        *map(
            render_filter_btn,
            ["Memorized", "Not Memorized", "Newly Memorized"],
        ),
        (
            Label(
                "X",
                hx_get=f"/profile/{current_type}",
                hx_target="body",
                hx_push_url="true",
                cls=(
                    "cursor-pointer",
                    TextT.xs,
                    LabelT.destructive,
                    (None if status else "invisible"),
                ),
            )
        ),
    )

    # For memorization progress
    unfiltered_data = db.q(qry)
    page_stats = defaultdict(lambda: {"memorized": 0, "total": 0})
    for item in unfiltered_data:
        page = item["page_number"]
        page_stats[page]["total"] += 1
        if item["status"] == "memorized":
            page_stats[page]["memorized"] += 1

    total_memorized_pages = 0
    for page, stats in page_stats.items():
        total_memorized_pages += stats["memorized"] / stats["total"]

    # Is to get the total count of the type: ["juz", "surah", "page"]
    # to show stats below the progress bar
    def total_count(_type, _status):
        type_stats = group_by_type(unfiltered_data, _type)
        count = 0
        for type_number, stats in type_stats.items():

            status_list = [item["status"] == "memorized" for item in stats]
            if _status == "memorized" and all(status_list):
                count += 1
            elif _status == "not_memorized" and not any(status_list):
                count += 1
            elif (
                _status == "partially_memorized"
                and any(status_list)
                and not all(status_list)
            ):
                count += 1
        return count

    type_with_total = {
        "juz": 30,
        "surah": 114,
        "page": 604,
    }

    def render_stat_row(_type):
        memorized_count = total_count(_type, "memorized")
        not_memorized_count = total_count(_type, "not_memorized")
        partially_memorized_count = total_count(_type, "partially_memorized")
        # newly_memorized_count = total_count(_type, "newly_memorized")

        current_type_total = type_with_total[_type]
        count_percentage = lambda x: format_number(x / current_type_total * 100)

        def render_td(count):
            return Td(
                f"{count} ({count_percentage(count)}%)",
                cls="text-center",
            )

        return Tr(
            Th(destandardize_text(_type)),
            *map(
                render_td,
                [
                    memorized_count,
                    not_memorized_count,
                    partially_memorized_count,
                    # newly_memorized_count,
                ],
            ),
        )

    status_stats_table = (
        Table(
            Thead(
                Tr(
                    Th("", cls="uk-table-shrink"),
                    Th("Memorized", cls="min-w-28"),
                    Th("Not Memorized", cls="min-w-28"),
                    Th("Partially Memorized", cls="min-w-28"),
                    # Th("Newly Memorized", cls="min-w-28"),
                )
            ),
            Tbody(*map(render_stat_row, ["juz", "surah", "page"])),
        ),
    )

    progress_bar_with_stats = (
        DivCentered(
            P(
                f"Memorization Progress: {format_number(total_memorized_pages)}/604 Pages ({int(total_memorized_pages/604*100)}%)",
                cls="font-bold text-sm sm:text-lg ",
            ),
            Progress(value=f"{total_memorized_pages}", max="604"),
            # Div(status_stats_table, cls=FlexT.block),
            cls="space-y-2",
            id="stats_info",
        ),
    )
    ##
    modal = Div(
        ModalContainer(
            ModalDialog(
                ModalHeader(
                    ModalTitle(id="my-modal-title"),
                    P(cls=TextPresets.muted_sm, id="my-modal-description"),
                    ModalCloseButton(),
                    cls="space-y-3",
                ),
                Form(
                    ModalBody(
                        Div(id="my-modal-body"),
                        data_uk_overflow_auto=True,
                    ),
                    ModalFooter(
                        Div(id="my-modal-footer"),
                    ),
                    Div(id="my-modal-link"),
                ),
                cls="uk-margin-auto-vertical",
            ),
            id="my-modal",
        ),
        id="modal-container",
    )

    type_details = {
        "page": ["Juz", "Surah"],
        "surah": ["Juz", "Page"],
        "juz": ["Surah", "Page"],
    }

    details = type_details.get(current_type, ["", ""])
    return main_area(
        Div(
            progress_bar_with_stats,
            DividerLine(),
            DivFullySpaced(
                filter_btns,
            ),
            Div(
                TabContainer(
                    *map(render_navigation_item, ["juz", "surah", "page"]),
                ),
                Div(
                    Table(
                        Thead(
                            Tr(
                                Th(current_type.title()),
                                *map(Th, details),
                                # Th(
                                #     CheckboxX(
                                #         cls="select_all",
                                #         x_model="selectAll",
                                #         _at_change="toggleAll()",
                                #     )
                                # ),
                                Th("Status"),
                                Th(""),
                            )
                        ),
                        Tbody(*rows),
                        x_data=select_all_checkbox_x_data(
                            class_name="profile_rows", is_select_all="false"
                        ),
                        x_init="updateSelectAll()",
                    ),
                    cls="h-[68vh] overflow-auto uk-overflow-auto",
                ),
                cls="space-y-5",
            ),
            Div(modal),
            cls="space-y-5",
        ),
        auth=auth,
        active="Memorization Status",
    )


# This is responsible for updating the modal
@app.get("/profile/custom_status_update/{current_type}/{type_number}")
def load_descendant_items_for_profile(
    current_type: str,
    type_number: int,
    title: str,
    description: str,
    filter_status: str,
    auth,
    req,
    sess,
    status: str = None,
):
    if current_type == "juz":
        condition = f"pages.juz_number = {type_number}"
    elif current_type == "surah":
        condition = f"items.surah_id = {type_number}"
    elif current_type == "page":
        condition = f"pages.page_number = {type_number}"
    else:
        return "Invalid current_type"
    qry = f"""SELECT items.id, items.surah_id, pages.page_number, pages.juz_number, hafizs_items.status FROM items 
                          LEFT JOIN pages ON items.page_id = pages.id
                          LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
                          WHERE items.active != 0 AND {condition};"""

    status_condition = (
        f"AND hafizs_items.status = '{status}'"
        if status != "not_memorized"
        else "AND hafizs_items.status IS NULL"
    )
    if status is not None:
        qry = qry.replace(";", f" {status_condition};")
    ct = db.q(qry)

    def render_row(record):
        current_status = destandardize_text(record["status"] or "not_memorized")
        current_id = record["id"]
        return Tr(
            Td(
                # This hidden input is to send the id to the backend even if it is unchecked
                Hidden(name=f"id-{current_id}", value="0"),
                CheckboxX(
                    name=f"id-{current_id}",
                    value="1",
                    cls="partial_rows",  # Alpine js reference
                    _at_click="handleCheckboxClick($event)",
                ),
            ),
            Td(record["page_number"]),
            Td(surahs[record["surah_id"]].name),
            Td(f"Juz {record['juz_number']}"),
            Td(current_status),
        )

    table = Table(
        Thead(
            Tr(
                Th(
                    CheckboxX(
                        cls="select_all",
                        x_model="selectAll",
                        _at_change="toggleAll()",
                    )
                ),
                Th("Page"),
                Th("Surah"),
                Th("Juz"),
                Th("Status"),
            )
        ),
        Tbody(*map(render_row, ct)),
        x_data=select_all_checkbox_x_data(
            class_name="partial_rows", is_select_all="false"
        ),
        x_init="updateSelectAll()",
        id="filtered-table",
    )
    modal_level_dd = Div(
        status_dropdown(status),
        id="my-modal-body",
    )
    base = f"/profile/custom_status_update/{current_type}"
    if type_number is not None:
        base += f"/{type_number}"
    # adding status filter to the response
    query = f"?status={status}&" if status else "?"
    query += f"title={title}&description={description}&filter_status={filter_status}"

    link = base + query

    ##
    def update_button(label, value, hx_select_id, hx_select_oob_id="", cls=""):
        return Button(
            label,
            hx_post=link,
            hx_select=hx_select_id,
            hx_target=hx_select_id,
            hx_swap="outerHTML",
            hx_select_oob=hx_select_oob_id,
            name="action",
            value=value,
            cls=("bg-green-600 text-white", cls),
        )

    return (
        table,
        ModalTitle(
            "" if title == "" else f"{title} - Select Memorized Page",
            id="my-modal-title",
            hx_swap_oob="true",
        ),
        P(
            description,
            id="my-modal-description",
            hx_swap_oob="true",
            cls=TextPresets.muted_lg,
        ),
        Div(
            modal_level_dd,
            update_button(
                label="Update and Close",
                value="close",
                hx_select_id=f"#{current_type}-{type_number}",
                hx_select_oob_id=f"#stats_info",
                cls="uk-modal-close",
            ),
            update_button(
                label="Update and Stay",
                value="stay",
                hx_select_id="#filtered-table",
                hx_select_oob_id="#filtered-table",
            ),
            Button("Cancel", cls=("bg-red-600 text-white", "uk-modal-close")),
            id="my-modal-footer",
            hx_swap_oob="true",
            cls=("space-x-2", "space-y-2"),
        ),
    )


def resolve_update_data(current_item, selected_status):
    if current_item.mode_id in (3, 4):
        return {"status": selected_status}
    if selected_status == "newly_memorized":
        return {"status": selected_status, "mode_id": 2}
    return {"status": selected_status, "mode_id": 1}


# This page is related to `profile`
@app.post("/update_checkbox/{current_type}/{type_number}/{filter_status}")
async def update_status(
    current_type: str, type_number: int, filter_status: str, req: Request, auth
):
    form_data = await req.form()
    existing_status = filter_status
    qry = f"""SELECT items.id, items.surah_id, pages.page_number, pages.juz_number FROM items 
                          LEFT JOIN pages ON items.page_id = pages.id
                          WHERE items.active != 0;"""
    ct = db.q(qry)
    grouped = group_by_type(ct, current_type, feild="id")
    for item_id in grouped[type_number]:
        current_record = hafizs_items(
            where=f"item_id = {item_id} and hafiz_id = {auth}"
        )[0]
        # update logic
        if existing_status == "memorized":
            set_status = None
        elif existing_status is None:
            set_status = "memorized"
        else:
            set_status = current_record.status
        current_record.status = set_status
        hafizs_items.update(current_record)
    query_string = f"?status={filter_status}&" if filter_status else ""
    return RedirectResponse(f"/profile/{current_type}/{query_string}", status_code=303)


@app.post("/profile/update_status/{current_type}/{type_number}")
def profile_page_status_update(
    current_type: str,
    type_number: int,
    req: Request,
    selected_status: str,
    filter_status: str,
    sess,
    auth,
):
    #  "not_memorized" means no status, so store it as NULL in DB
    selected_status = None if selected_status == "not_memorized" else selected_status
    qry = f"""SELECT items.id, items.surah_id, pages.page_number, pages.juz_number FROM items 
                          LEFT JOIN pages ON items.page_id = pages.id
                          WHERE items.active != 0;"""
    ct = db.q(qry)
    is_newly_memorized = selected_status == "newly_memorized"
    grouped = group_by_type(ct, current_type, feild="id")
    for item_id in grouped[type_number]:
        current_item = hafizs_items(where=f"item_id = {item_id} and hafiz_id = {auth}")
        current_item = current_item[0]
        # determine what to update
        update_data = resolve_update_data(current_item, selected_status)
        hafizs_items.update(update_data, current_item.id)
        if is_newly_memorized:
            # add revision newly_memorized pages
            revisions.insert(
                hafiz_id=auth,
                item_id=item_id,
                revision_date=get_current_date(auth),
                rating=DEFAULT_RATINGS.get("new_memorization"),
                mode_id=2,
            )
    referer = req.headers.get("referer", "/")
    return RedirectResponse(referer, status_code=303)


@app.post("/profile/custom_status_update/{current_type}/{type_number}")
async def profile_page_custom_status_update(
    current_type: str,
    type_number: int,
    req: Request,
    sess,
    title: str,
    description: str,
    filter_status: str,
    action: str,
    auth,
    status: str = None,
):
    form_data = await req.form()
    selected_status = form_data.get("selected_status")
    selected_status = None if selected_status == "not_memorized" else selected_status
    is_newly_memorized = selected_status == "newly_memorized"
    for id_str, check in form_data.items():
        if not id_str.startswith("id-"):
            continue  # Skip non-id keys
        # extract id from the key
        try:
            item_id = int(id_str.split("-")[1])
        except (IndexError, ValueError):
            continue  # Skip invalid id keys

        if check != "1":
            continue  # Skip unchecked checkboxes

        current_item = hafizs_items(where=f"item_id = {item_id} and hafiz_id = {auth}")
        current_item = current_item[0]
        # determine what to update
        update_data = resolve_update_data(current_item, selected_status)
        hafizs_items.update(update_data, current_item.id)
        if is_newly_memorized:
            # add revision newly_memorized pages
            revisions.insert(
                hafiz_id=auth,
                item_id=item_id,
                revision_date=get_current_date(auth),
                rating=DEFAULT_RATINGS.get("new_memorization"),
                mode_id=2,
            )

    query_string = f"?status={status}&" if status else "?"
    query_string += (
        f"title={title}&description={description}&filter_status={filter_status}"
    )
    stay_url = (
        f"/profile/custom_status_update/{current_type}/{type_number}{query_string}"
    )
    close_url = f"/profile/{current_type}{query_string}"
    if action == "stay":
        return RedirectResponse(stay_url, status_code=303)
    elif action == "close":
        return RedirectResponse(close_url, status_code=303)
    else:
        return Redirect(close_url)


@app.get
def backup():
    if not os.path.exists(DB_PATH):
        return Titled("Error", P("Database file not found"))

    backup_path = backup_sqlite_db(DB_PATH, "data/backup")

    return FileResponse(backup_path, filename="quran_backup.db")


def graduate_btn_recent_review(
    item_id, is_graduated=False, is_disabled=False, **kwargs
):
    return Switch(
        hx_vals={"item_id": item_id},
        hx_post=f"/recent_review/graduate",
        # target_id=f"row-{item_id}",
        # hx_swap="none",
        checked=is_graduated,
        name=f"is_checked",
        id=f"graduate-btn-{item_id}",
        cls=("hidden" if is_disabled else ""),
        **kwargs,
    )


@app.get("/recent_review")
def recent_review_view(auth):
    hafiz_items_data = hafizs_items(where="mode_id IN (2,3,4)", order_by="item_id ASC")
    items_id_with_mode = [
        {
            "item_id": hafiz_item.item_id,
            "mode_id": 3 if (hafiz_item.mode_id == 2) else hafiz_item.mode_id,
        }
        for hafiz_item in hafiz_items_data
    ]
    # custom sort order to group the graduated and ungraduated
    items_id_with_mode.sort(key=lambda x: (x["mode_id"], x["item_id"]))

    # To get the earliest date from revisions based on the item_id
    item_ids = [item["item_id"] for item in items_id_with_mode]
    qry = f"""
    SELECT MIN(revision_date) as earliest_date
    FROM revisions
    WHERE item_id IN ({", ".join(map(str, item_ids))})
    """
    ct = db.q(qry)
    earliest_date = ct[0]["earliest_date"]

    # generate last ten days for column header
    # earliest_date = calculate_date_difference(days=10, date_format="%Y-%m-%d")

    current_date = get_current_date(auth)
    # Change the date range to start from the earliest date
    date_range = pd.date_range(
        start=(earliest_date or current_date), end=current_date, freq="D"
    )[::-1]

    def render_row(o):
        item_id, mode_id = o["item_id"], o["mode_id"]

        def render_checkbox(date):
            formatted_date = date.strftime("%Y-%m-%d")
            current_revision_data = revisions(
                where=f"revision_date = '{formatted_date}' AND item_id = {item_id} AND mode_id IN (2,3);"
            )

            # To render the checkbox as intermidiate image
            if current_revision_data:
                is_newly_memorized = current_revision_data[0].mode_id == 2
            else:
                is_newly_memorized = False

            return Td(
                Form(
                    Hidden(name="date", value=formatted_date),
                    CheckboxX(
                        name=f"is_checked",
                        value="1",
                        hx_post=f"/recent_review/update_status/{item_id}",
                        target_id=f"count-{item_id}",
                        checked=True if current_revision_data else False,
                        _at_change="updateVisibility($event.target)",
                        # This @click is to handle the shift+click.
                        _at_click=f"handleShiftClick($event, 'date-{formatted_date}')",
                        disabled=(mode_id == 4) or is_newly_memorized,
                        cls=(
                            "hidden",
                            "disabled:opacity-50",
                            # date-<class> is to identify the row for shift+click
                            f"date-{formatted_date}",
                            (
                                # If it is newly memorized then render the intermidiate checkbox icon
                                "checked:bg-[image:var(--uk-form-checkbox-image-indeterminate)]"
                                if is_newly_memorized
                                else ""
                            ),
                        ),
                    ),
                    cls="",
                ),
                Span("-", cls="hidden"),
                cls="text-center",
            )

        revision_count = get_mode_count(item_id, 3)

        return Tr(
            Td(get_page_description(item_id), cls="sticky left-0 z-20 bg-white"),
            Td(get_start_text(item_id), cls=TextT.lg),
            Td(
                revision_count,
                cls="text-center",
                id=f"count-{item_id}",
            ),
            Td(
                Div(
                    graduate_btn_recent_review(
                        item_id,
                        is_graduated=(mode_id == 4),
                        is_disabled=(revision_count == 0),
                    ),
                    cls=(FlexT.block, FlexT.center, FlexT.middle, "min-h-11"),
                )
            ),
            *map(render_checkbox, date_range),
            id=f"row-{item_id}",
        )

    table = Table(
        Thead(
            Tr(
                Th("Pages", cls="min-w-28 sm:min-w-36 sticky left-0 z-20 bg-white"),
                Th("Start Text", cls="min-w-28"),
                Th("Count"),
                Th("Graduate"),
                *[
                    Th(date.strftime("%b %d %a"), cls="!text-center sm:min-w-28")
                    for date in date_range
                ],
            )
        ),
        Tbody(*map(render_row, items_id_with_mode)),
        cls=(TableT.middle, TableT.divider, TableT.hover, TableT.sm, TableT.justify),
    )
    content_body = Div(
        H2("Recent Review"),
        Div(
            table,
            cls="uk-overflow-auto",
            id="recent_review_table_area",
        ),
        cls="text-xs sm:text-sm",
        # Currently this variable is not being used but it is needed for alpine js attributes
        x_data="{ showAll: false }",
    )

    return main_area(
        content_body,
        Script(src="/public/recent_review_logic.js"),
        active="Home",
        auth=auth,
    )


@app.post("/recent_review/update_status/{item_id}")
def update_status_for_recent_review(item_id: int, date: str, is_checked: bool = False):

    checkbox_update_logic(
        mode_id=3, rating=1, item_id=item_id, date=date, is_checked=is_checked
    )
    revision_count = get_mode_count(item_id, 3)

    if revision_count > 6:
        # We are redirecting to swap the entire row
        # as we want to render the disabled checkbox with graduated button
        return RedirectResponse(f"/recent_review/graduate?item_id={item_id}")

    return revision_count, graduate_btn_recent_review(
        item_id, is_disabled=(revision_count == 0), hx_swap_oob="true"
    )


@app.post("/recent_review/graduate")
def graduate_recent_review(item_id: int, auth, is_checked: bool = False):

    # Retry logic with 3 attempts and 50ms delay
    # To handle multiple simultaneous req from the user
    # typically when shift-clicking the checkbox where it will trigger multiple requests
    for attempt in range(3):
        try:
            graduate_the_item_id(
                item_id=item_id, mode_id=3, auth=auth, checked=is_checked
            )
            break  # Success, exit the loop
        except Exception as e:
            if attempt < 2:  # Only delay if not the last attempt
                time.sleep(0.05)

    # We can also use the route funtion to return the entire page as output
    # And the HTMX headers are used to change the (re)target,(re)select only the current row
    return recent_review_view(auth), HtmxResponseHeaders(
        retarget=f"#row-{item_id}",
        reselect=f"#row-{item_id}",
        reswap="outerHTML",
    )


@app.get("/watch_list")
def watch_list_view(auth):
    current_date = get_current_date(auth)
    week_column = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6", "Week 7"]

    # This is to only get the watch_list item_id (which are not graduated yet)
    hafiz_items_data = hafizs_items(
        where=f"(mode_id = 4 OR watch_list_graduation_date IS NOT NULL) AND hafiz_id = {auth}",
        order_by="mode_id DESC, next_review ASC, item_id ASC",
    )

    def graduate_btn_watch_list(
        item_id, is_graduated=False, is_disabled=False, **kwargs
    ):
        return Switch(
            hx_vals={"item_id": item_id},
            hx_post=f"/watch_list/graduate",
            # target_id=f"row-{item_id}",
            # hx_swap="none",
            checked=is_graduated,
            name=f"is_checked",
            id=f"graduate-btn-{item_id}",
            cls=("hidden" if is_disabled else ""),
            **kwargs,
        )

    def render_row(hafiz_item):
        item_id = hafiz_item.item_id
        is_graduated = hafiz_item.mode_id == 1
        last_review = hafiz_item.last_review

        watch_list_revisions = revisions(
            where=f"item_id = {item_id} AND mode_id = 4", order_by="revision_date ASC"
        )
        weeks_revision_excluded = week_column[len(watch_list_revisions) :]

        revision_count = get_mode_count(item_id, 4)

        if not is_graduated:
            due_day = day_diff(last_review, current_date)
        else:
            due_day = 0

        def render_checkbox(_):
            return Td(
                CheckboxX(
                    hx_post=f"/watch_list/add",
                    hx_vals={"item_id": item_id},
                    hx_include="#global_rating, #global_date",
                    hx_swap="outerHTML",
                    target_id=f"row-{item_id}",
                    hx_select=f"#row-{item_id}",
                ),
                cls="text-center",
            )

        def render_hyphen(_):
            return Td(
                Span("-"),
                cls="text-center",
            )

        def render_rev(rev: Revision):
            rev_date = rev.revision_date
            ctn = (
                render_rating(rev.rating).split()[0],
                (
                    f" {date_to_human_readable(rev_date)}"
                    if not (rev_date == current_date)
                    else None
                ),
            )
            return Td(
                (
                    A(
                        *ctn,
                        hx_get=f"/watch_list/edit/{rev.id}",
                        target_id="my-modal-body",
                        data_uk_toggle="target: #my-modal",
                        cls=AT.classic,
                    )
                    if not is_graduated
                    else Span(*ctn)
                ),
                cls="text-center",
            )

        if is_graduated or revision_count >= 7:
            due_day_message = ""
        elif due_day >= 7:
            due_day_message = due_day - 7
        else:
            due_day_message = "-"

        return Tr(
            Td(get_page_description(item_id), cls="sticky left-0 z-20 bg-white"),
            Td(get_start_text(item_id), cls=TextT.lg),
            Td(revision_count, cls="text-center"),
            Td(
                date_to_human_readable(hafiz_item.next_review)
                if (not is_graduated) and revision_count < 7
                else ""
            ),
            Td(due_day_message),
            Td(
                graduate_btn_watch_list(
                    item_id,
                    is_graduated=is_graduated,
                    is_disabled=(revision_count == 0),
                ),
                cls=(FlexT.block, FlexT.center, FlexT.middle, "min-h-11"),
            ),
            *map(render_rev, watch_list_revisions),
            *map(
                render_checkbox,
                ([weeks_revision_excluded.pop(0)] if due_day >= 7 else []),
            ),
            *map(render_hyphen, weeks_revision_excluded),
            id=f"row-{item_id}",
        )

    table = Table(
        Thead(
            Tr(
                Th("Pages", cls="min-w-28 sm:min-w-36 sticky left-0 z-20 bg-white"),
                Th("Start Text", cls="min-w-28"),
                Th("Count"),
                Th("Next Review", cls="min-w-28 "),
                Th("Due day"),
                Th("Graduate", cls="column_to_scroll"),
                *[Th(week, cls="!text-center sm:min-w-28") for week in week_column],
            )
        ),
        Tbody(*map(render_row, hafiz_items_data)),
        cls=(TableT.middle, TableT.divider, TableT.hover, TableT.sm, TableT.justify),
    )
    modal = ModalContainer(
        ModalDialog(
            ModalHeader(ModalCloseButton()),
            ModalBody(
                Div(id="my-modal-body"),
                data_uk_overflow_auto=True,
            ),
            ModalFooter(),
            cls="uk-margin-auto-vertical",
        ),
        id="my-modal",
    )

    content_body = Div(
        H2("Watch List"),
        Div(
            rating_dropdown(
                id="global_rating",
                cls="flex-1",
            ),
            LabelInput(
                "Revision Date",
                name="revision_date",
                type="date",
                value=current_date,
                id="global_date",
                cls="flex-1",
            ),
            cls=(FlexT.block, FlexT.middle, "w-full gap-3"),
        ),
        Div(
            table,
            modal,
            cls="uk-overflow-auto",
            id="watch_list_table_area",
        ),
        cls="text-xs sm:text-sm",
        # Currently this variable is not being used but it is needed for alpine js attributes
        x_data="{ showAll: false }",
    )

    return main_area(
        content_body,
        Script(src="/public/watch_list_logic.js"),
        active="Home",
        auth=auth,
    )


# TODO: Needs refactoring, as it was being used only once
def watch_list_form(item_id: int, min_date: str, _type: str, auth):
    page = items[item_id].page_id
    current_date = get_current_date(auth)

    return Container(
        H1(get_page_description(item_id), f" - {items[item_id].start_text}"),
        Form(
            LabelInput(
                "Revision Date",
                name="revision_date",
                min=min_date,
                max=current_date,
                type="date",
                value=current_date,
            ),
            Hidden(name="id"),
            Hidden(name="page_no", value=page),
            Hidden(name="mode_id", value=4),
            Hidden(name="item_id", value=item_id),
            rating_radio(),  # single entry
            Div(
                Button("Save", cls=ButtonT.primary),
                (
                    Button(
                        "Delete",
                        cls=ButtonT.destructive,
                        hx_delete=f"/watch_list",
                        hx_swap="none",
                    )
                    if _type == "edit"
                    else None
                ),
                A(
                    Button("Cancel", type="button", cls=ButtonT.secondary),
                    href=f"/watch_list",
                ),
                cls="flex justify-around items-center w-full",
            ),
            action=f"/watch_list/{_type}",
            method="POST",
        ),
        cls=("mt-5", ContainerT.xl, "space-y-3"),
    )


@app.get("/watch_list/edit/{rev_id}")
def watch_list_edit_form(rev_id: int, auth):
    current_revision = revisions[rev_id].__dict__
    current_revision["rating"] = str(current_revision["rating"])
    return fill_form(
        watch_list_form(current_revision["item_id"], "", "edit", auth), current_revision
    )


@app.post("/watch_list/edit")
def watch_list_edit_data(revision_details: Revision):
    revisions.update(revision_details)
    item_id = revision_details.item_id
    update_review_dates(item_id, 4)
    populate_hafizs_items_stat_columns(item_id=item_id)
    return RedirectResponse(f"/watch_list", status_code=303)


@app.delete("/watch_list")
def watch_list_delete_data(id: int, item_id: int):
    revisions.delete(id)
    update_review_dates(item_id, 4)
    populate_hafizs_items_stat_columns(item_id=item_id)
    return Redirect("/watch_list")


@app.post("/watch_list/add")
def watch_list_add_data(revision_details: Revision, auth):
    revision_details.mode_id = 4
    revisions.insert(revision_details)
    item_id = revision_details.item_id

    revision_count = get_mode_count(item_id, 4)

    if revision_count > 6:
        graduate_the_item_id(item_id=item_id, mode_id=4, auth=auth)
        return RedirectResponse(f"/watch_list", status_code=303)

    update_review_dates(item_id, 4)
    populate_hafizs_items_stat_columns(item_id=item_id)

    return RedirectResponse("/watch_list", status_code=303)


@app.post("/watch_list/graduate")
def graduate_watch_list(item_id: int, auth, is_checked: bool = False):

    graduate_the_item_id(item_id=item_id, mode_id=4, auth=auth, checked=is_checked)

    return watch_list_view(auth), HtmxResponseHeaders(
        retarget=f"#row-{item_id}",
        reselect=f"#row-{item_id}",
        reswap="outerHTML",
    )


@app.get
def import_db(auth):
    current_dbs = [
        Li(f, cls=ListT.circle) for f in os.listdir("data") if f.endswith(".db")
    ]
    form = Form(
        UploadZone(
            DivCentered(Span("Upload Zone"), UkIcon("upload")),
            id="file",
            accept=".db",
        ),
        Button("Submit"),
        action=import_db,
        method="POST",
    )
    return main_area(
        Div(
            Div(H2("Current DBs"), Ul(*current_dbs)),
            Div(H1("Upload DB"), form),
            cls="space-y-6",
        ),
        active="Revision",
        auth=auth,
    )


@app.post
async def import_db(file: UploadFile):
    path = "data/" + file.filename
    if DB_PATH == path:
        return Titled("Error", P("Cannot overwrite the current DB"))

    file_content = await file.read()
    with open(path, "wb") as f:
        f.write(file_content)

    return RedirectResponse(index)


@app.get
def theme():
    return ThemePicker()


def get_not_memorized_records(auth, custom_where=None):
    default = "hafizs_items.status IS NULL AND items.active != 0"
    if custom_where:
        default = f"{custom_where}"
    not_memorized_tb = f"""
        SELECT items.id, items.surah_id, items.surah_name,
        hafizs_items.item_id, hafizs_items.status, hafizs_items.hafiz_id, pages.juz_number, pages.page_number, revisions.revision_date, revisions.id AS revision_id
        FROM items 
        LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
        LEFT JOIN pages ON items.page_id = pages.id
        LEFT JOIN revisions ON items.id = revisions.item_id
        WHERE {default};
    """
    return db.q(not_memorized_tb)


def group_by_type(data, current_type, feild=None):
    columns_map = {
        "juz": "juz_number",
        "surah": "surah_id",
        "page": "page_number",
        "item_id": "item_id",
        "id": "id",
    }
    grouped = defaultdict(
        list
    )  # defaultdict() is creating the key as the each column_map number and value as the list of records
    for row in data:
        grouped[row[columns_map[current_type]]].append(
            row if feild is None else row[feild]
        )
    sorted_grouped = dict(sorted(grouped.items(), key=lambda x: int(x[0])))
    return sorted_grouped


def get_closest_unmemorized_item_id(auth, last_newly_memorized_item_id: int):
    not_memorized = get_not_memorized_records(auth)
    grouped_by_item_id = group_by_type(not_memorized, "id")
    not_memorized_item_ids = list(grouped_by_item_id.keys())

    def get_next_item_id(not_memorized_item_ids, last_newly_memorized_item_id):
        sorted_item_ids = sorted(not_memorized_item_ids)
        for item_id in sorted_item_ids:
            if item_id > last_newly_memorized_item_id:
                return item_id
        return None

    # next_item_id represent the next closest unmemorized item_id
    next_item_id = get_next_item_id(
        not_memorized_item_ids, last_newly_memorized_item_id
    )
    if next_item_id is None:
        display_next = "No more pages"
    else:
        display_next = get_page_description(next_item_id, is_link=False)
        # display_next = (Span(Strong(next_pg)), " - ", next_surah)

    return next_item_id, display_next


def render_row_based_on_type(
    auth,
    type_number: str,
    records: list,
    current_type,
    row_link: bool = True,
):
    _surahs = sorted({r["surah_id"] for r in records})
    _pages = sorted([r["page_number"] for r in records])
    _juzs = sorted({r["juz_number"] for r in records})

    def render_range(list, _type=""):
        first_description = list[0]
        last_description = list[-1]

        if _type == "Surah":
            _type = ""
            first_description = surahs[first_description].name
            last_description = surahs[last_description].name

        if len(list) == 1:
            return f"{_type} {first_description}"
        return f"{_type}{"" if _type == "" else "s"} {first_description} – {last_description}"

    surah_range = render_range(_surahs, "Surah")
    page_range = render_range(_pages, "Page")
    juz_range = render_range(_juzs, "Juz")

    if current_type == "juz":
        details = f"{surah_range} ({page_range})"
    elif current_type == "surah":
        details = f"{juz_range} ({page_range})"
    elif current_type == "page":
        details = f"{juz_range} | {surah_range}"
    title = (
        f"{current_type.capitalize()} {type_number}"
        if current_type != "surah"
        else surahs[type_number].name
    )

    filter_url = f"/new_memorization/expand/{current_type}/{type_number}"
    if current_type == "page":
        item_ids = [item.id for item in items(where=f"page_id = {type_number}")]
        get_page = (
            f"/new_memorization/add/{current_type}?item_id={item_ids[0]}"
            if len(item_ids) == 1
            else filter_url
        )
    else:
        get_page = filter_url

    hx_attrs = {
        "hx_get": get_page,
        "hx_vals": '{"title": "CURRENT_TITLE", "description": "CURRENT_DETAILS"}'.replace(
            "CURRENT_TITLE", title or ""
        ).replace(
            "CURRENT_DETAILS", details or ""
        ),
        "target_id": "modal-body",
        "data_uk_toggle": "target: #modal",
    }

    if current_type != "page":
        link_text = "Show Pages ➡️"
    else:
        link_text = "Set as Newly Memorized"
    item_ids = [item.id for item in items(where=f"page_id = {type_number}")]
    render_attrs = {
        "hx_select": f"#new_memorization_{current_type}-{type_number}",
        "hx_target": f"#new_memorization_{current_type}-{type_number}",
        "hx_swap": "outerHTML",
        "hx_select_oob": "#recently_memorized_table",
    }
    if len(item_ids) == 1 and not row_link and current_type == "page":
        link_content = render_new_memorization_checkbox(
            auth=auth, item_id=item_ids[0], **render_attrs
        )
    elif len(item_ids) > 1 and current_type == "page":
        link_content = render_new_memorization_checkbox(
            auth=auth, page_id=type_number, **render_attrs
        )
    else:
        link_content = A(
            link_text,
            cls=AT.classic,
            # **hx_attrs,
            hx_attrs={**hx_attrs},
        )

    hx_attributes = hx_attrs if current_type != "page" else {} if row_link else {}
    return Tr(
        Td(title),
        Td(details),
        Td(link_content),
        **hx_attributes,
        id=f"new_memorization_{current_type}-{type_number}",
    )


def render_navigation_item(
    _type: str,
    current_type: str,
):
    return Li(
        A(
            f"by {_type}",
            href=f"/new_memorization/{_type}",
        ),
        cls=("uk-active" if _type == current_type else None),
    )


def flatten_input(data):
    if not data:
        return []
    seen = set()  # use a set to filtered out duplicate entries
    flat = []  # use a list to get order
    for page, records in data:
        for entry in records:
            key = entry["page_number"]
            if key not in seen:
                flat.append(entry)
                seen.add(key)
    return flat


def group_consecutive_by_date(records):
    if not records:
        return []
    # Sort by page_number ASC so we can group sequence pages
    records = sorted(records, key=lambda x: x["page_number"])

    groups = []
    current_group = [records[0]]

    for prev, curr in zip(records, records[1:]):
        # Consecutive pages and same date
        is_consecutive = curr["page_number"] == prev["page_number"] + 1
        same_date = curr["revision_date"] == prev["revision_date"]

        if is_consecutive and same_date:
            current_group.append(curr)
        else:
            groups.append(current_group)
            current_group = [curr]

    groups.append(current_group)

    # Sort final groups by latest revision_id in descending order
    def latest_revision(group):
        return max(item["revision_date"] for item in group)

    sorted_groups = sorted(groups, key=latest_revision, reverse=True)
    return sorted_groups


def format_output(groups: list):
    formatted = {}
    for group in groups:
        pages = [item["page_number"] for item in group]
        juz = group[0]["juz_number"]
        surahs = list(
            dict.fromkeys(item["surah_name"] for item in group)
        )  # get list of unique surahs
        page_str = (
            f"Page {pages[0]}" if len(pages) == 1 else f"Pages {pages[0]} - {pages[-1]}"
        )
        surah_str = " - ".join(surahs)
        title = page_str
        details = f"Juz {juz} | {surah_str}"
        rev_date = group[0]["revision_date"]
        for page in pages:
            formatted[page] = (title, details, rev_date)
    return formatted


@app.delete("/new_memorization/update_as_newly_memorized/{item_id}")
def delete(auth, request, item_id: str):
    qry = f"item_id = {item_id} AND mode_id = 2;"
    revisions_data = revisions(where=qry)
    revisions.delete(revisions_data[0].id)
    hafizs_items_data = hafizs_items(where=f"item_id = {item_id} AND hafiz_id= {auth}")[
        0
    ]
    del hafizs_items_data.status
    hafizs_items_data.mode_id = 1
    hafizs_items.update(hafizs_items_data)
    populate_hafizs_items_stat_columns(item_id=item_id)

    referer = request.headers.get("Referer")
    return Redirect(referer)


@app.get("/new_memorization/{current_type}")
def new_memorization(auth, current_type: str):
    if not current_type:
        current_type = "surah"
    ct = get_not_memorized_records(auth)
    grouped = group_by_type(ct, current_type)
    not_memorized_rows = [
        render_row_based_on_type(
            auth=auth,
            type_number=type_number,
            records=records,
            current_type=current_type,
            row_link=False,
        )
        for type_number, records in list(grouped.items())
    ]
    not_memorized_table = Div(
        Table(
            Thead(
                Tr(
                    Th("Name"),
                    Th("Range / Details"),
                    Th("Set As Newly Memorized"),
                ),
            ),
            Tbody(*not_memorized_rows),
        ),
        cls="uk-overflow-auto h-[45vh] p-4",
    )
    modal = ModalContainer(
        ModalDialog(
            ModalHeader(
                ModalTitle(id="modal-title"),
                P(cls=TextPresets.muted_sm, id="modal-description"),
                ModalCloseButton(),
                cls="space-y-3",
            ),
            ModalBody(
                Div(id="modal-body"),
                data_uk_overflow_auto=True,
            ),
            ModalFooter(),
            cls="uk-margin-auto-vertical",
        ),
        id="modal",
    )

    where_query = f"""
    revisions.mode_id = 2 AND revisions.hafiz_id = {auth} AND items.active != 0 
    ORDER BY revisions.revision_date DESC, revisions.id DESC 
    LIMIT 10;
    """
    newly_memorized = get_not_memorized_records(auth, where_query)
    grouped = group_by_type(newly_memorized, "item_id")

    # Sort grouped items by earliest revision_date in each list of records
    sorted_grouped_items = sorted(
        grouped.items(),
        key=lambda item: max(
            (datetime.strptime(rec["revision_date"], "%Y-%m-%d"), rec["revision_id"])
            for rec in item[1]
        ),
        reverse=True,
    )

    def render_recently_memorized_row(type_number: str, records: list, auth):
        revision_date = records[0]["revision_date"]

        next_page_item_id, display_next = (0, "")
        if type_number:
            next_page_item_id, display_next = get_closest_unmemorized_item_id(
                auth, type_number
            )
        render_attrs = {
            "hx_select": f"#recently_memorized_table",
            "hx_target": f"#recently_memorized_table",
            "hx_swap": "outerHTML",
            "hx_select_oob": "#new_memorization_table",
        }
        return Tr(
            Td(get_page_description(records[0]["item_id"])),
            Td(date_to_human_readable(revision_date)),
            Td(
                render_new_memorization_checkbox(
                    auth=auth,
                    item_id=next_page_item_id,
                    label_text=display_next,
                    **render_attrs,
                )
                if next_page_item_id
                else display_next
            ),
            Td(
                A(
                    "Delete",
                    hx_delete=f"/new_memorization/update_as_newly_memorized/{type_number}",
                    hx_confirm="Are you sure? This page might be available in other modes.",
                ),
                cls=AT.muted,
            ),
        )

    newly_memorized_rows = [
        render_recently_memorized_row(
            type_number,
            records,
            auth=auth,
        )
        for type_number, records in sorted_grouped_items
        if type_number is not None
    ]
    recent_newly_memorized_table = Div(
        Table(
            Thead(
                Tr(
                    Th("Name"),
                    Th("Revision Date"),
                    Th("Set As Newly Memorized"),
                    Th("Action"),
                ),
            ),
            Tbody(*newly_memorized_rows),
        ),
        cls="uk-overflow-auto h-[25vh] p-4",
    )

    return main_area(
        H1("New Memorization", cls="uk-text-center"),
        Div(
            Div(
                H4("Recently Memorized Pages"),
                recent_newly_memorized_table,
                cls="mt-4",
                id="recently_memorized_table",
            ),
            Div(
                H4("Select a Page Not Yet Memorized"),
                TabContainer(
                    *map(
                        lambda nav: render_navigation_item(nav, current_type),
                        ["juz", "surah", "page"],
                    ),
                ),
                not_memorized_table,
                id="new_memorization_table",
            ),
            cls="space-y-4",
        ),
        Div(modal),
        active="Home",
        auth=auth,
    )


@app.get("/new_memorization/expand/{current_type}/{type_number}")
def load_descendant_items_for_new_memorization(
    auth, current_type: str, type_number: int, title: str, description: str
):
    if current_type == "juz":
        condition = f"pages.juz_number = {type_number}"
    elif current_type == "surah":
        condition = f"items.surah_id = {type_number}"
    elif current_type == "page":
        condition = f"pages.page_number = {type_number}"
    else:
        return "Invalid current_type"

    qry = f"""SELECT items.id, items.surah_id, pages.page_number, pages.juz_number, hafizs_items.status FROM items
                          LEFT JOIN pages ON items.page_id = pages.id
                          LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
                          WHERE items.active != 0 AND hafizs_items.status IS NULL AND {condition}"""
    ct = db.q(qry)

    def render_row(record):
        return Tr(
            Td(
                # This hidden input is to send the id to the backend even if it is unchecked
                CheckboxX(
                    name=f"item_ids",
                    value=record["id"],
                    cls="partial_rows",  # Alpine js reference
                    _at_click="handleCheckboxClick($event)",
                ),
            ),
            Td(record["page_number"]),
            Td(surahs[record["surah_id"]].name),
            Td(f"Juz {record['juz_number']}"),
        )

    table = Div(
        Table(
            Thead(
                Tr(
                    Th(
                        CheckboxX(
                            cls="select_all",
                            x_model="selectAll",
                            _at_change="toggleAll()",
                        )
                    ),
                    Th("Page"),
                    Th("Surah"),
                    Th("Juz"),
                )
            ),
            Tbody(*map(render_row, ct)),
            x_data=select_all_checkbox_x_data(
                class_name="partial_rows", is_select_all="false"
            ),
            x_init="updateSelectAll()",
        ),
        cls="uk-overflow-auto max-h-[75vh] p-4",
    )

    return (
        Form(
            table,
            Button("Set as Newly Memorized", cls="bg-green-600 text-white"),
            hx_post=f"/new_memorization/bulk_update_as_newly_memorized",
            cls="space-y-2",
        ),
        ModalTitle(
            "" if title == "" else f"{title} - Select Memorized Page",
            id="modal-title",
            hx_swap_oob="true",
        ),
        P(
            description,
            id="modal-description",
            hx_swap_oob="true",
            cls=TextPresets.muted_lg,
        ),
    )


# FIXME: Check whether this function is used or not
def create_new_memorization_revision_form(
    current_type: str, title: str, description: str, current_date: str
):

    return Div(
        Form(
            LabelInput(
                "Revision Date",
                name="revision_date",
                type="date",
                value=current_date,
            ),
            Input(name="page_no", type="hidden"),
            Input(name="mode_id", type="hidden"),
            Input(name="item_id", type="hidden"),
            rating_radio(),  # Not now
            Div(
                Button("Save", cls=ButtonT.primary),
                # A(
                #     Button("Cancel", type="button", cls=ButtonT.secondary),
                #     href=f"/new_memorization/{current_type}",
                # ),
                Button(
                    "Cancel", type="button", cls=ButtonT.secondary + "uk-modal-close"
                ),
                cls="flex justify-around items-center w-full",
            ),
            action=f"/new_memorization/add/{current_type}",
            method="POST",
        ),
        ModalTitle(
            "" if title == "" else f"{title} - Select Memorized Page",
            id="modal-title",
            hx_swap_oob="true",
        ),
        P(
            description,
            id="modal-description",
            hx_swap_oob="true",
            cls=TextPresets.muted_lg,
        ),
    )


# FIXME: Check whether this route is used or not
@rt("/new_memorization/add/{current_type}")
def get(
    auth,
    current_type: str,
    item_id: str,
    title: str = None,
    description: str = None,
    max_item_id: int = 836,
    date: str = None,
):
    item_id = int(item_id)
    if item_id >= max_item_id:
        return Redirect(new_memorization)

    page = items[item_id].page_id
    return Titled(
        f"{page} - {get_surah_name(item_id=item_id)} - {items[item_id].start_text}",
        fill_form(
            create_new_memorization_revision_form(
                current_type, title, description, get_current_date(auth)
            ),
            {
                "page_no": page,
                "mode_id": 2,
                "plan_id": None,
                "revision_date": date,
                "item_id": item_id,
            },
        ),
    )


# FIXME: Check whether this route is used or not
@rt("/new_memorization/add/{current_type}")
def post(
    request, current_type: str, page_no: int, item_id: int, revision_details: Revision
):
    # The id is set to zer in the form, so we need to delete it
    # before inserting to generate the id automatically
    del revision_details.id
    revision_details.plan_id = set_zero_to_none(revision_details.plan_id)
    try:
        hafizs_items(where=f"item_id = {item_id}")[0]
    except IndexError:
        # updating the status of the item to memorized
        hafizs_items.insert(Hafiz_Items(item_id=item_id, page_number=page_no))
    hafizs_items_id = hafizs_items(where=f"item_id = {item_id}")[0].id
    hafizs_items.update(
        {"status": "newly_memorized", "mode_id": revision_details.mode_id},
        hafizs_items_id,
    )
    revisions.insert(revision_details)
    referer = request.headers.get("referer")
    # return Redirect(f"/new_memorization/{current_type}")
    return Redirect(referer or f"/new_memorization/{current_type}")


def get_ordered_mode_name_and_id():
    mode_name_list = [mode.name for mode in modes()]
    mode_id_list = [mode.id for mode in modes()]
    # to display the mode names in the correct order
    mode_id_list, mode_name_list = zip(
        *sorted(
            zip(mode_id_list, mode_name_list), key=lambda x: int(x[1].split(".")[0])
        )
    )
    return list(mode_id_list), list(mode_name_list)


@app.get("/page_details")
def page_details_view(auth):
    # Get mode name and ids from the db
    mode_id_list, mode_name_list = get_ordered_mode_name_and_id()

    # Build dynamic CASE statements for each mode
    mode_case_statements = []
    for mode_id in mode_id_list:
        case_stmt = f"COALESCE(SUM(CASE WHEN revisions.mode_id = {mode_id} THEN 1 END), '-') AS '{mode_id}'"
        mode_case_statements.append(case_stmt)
    mode_cases = ",\n".join(mode_case_statements)

    display_pages_query = f"""SELECT 
                            items.id,
                            items.surah_id,
                            pages.page_number,
                            pages.juz_number,
                            {mode_cases},
                            SUM(revisions.rating) AS rating_summary
                        FROM revisions
                        LEFT JOIN items ON revisions.item_id = items.id
                        LEFT JOIN pages ON items.page_id = pages.id
                        WHERE revisions.hafiz_id = {auth} AND items.active != 0
                        GROUP BY items.id
                        ORDER BY pages.page_number;"""
    hafiz_items_with_details = db.q(display_pages_query)
    grouped = group_by_type(hafiz_items_with_details, "id")

    def render_row_based_on_type(
        records: list,
        row_link: bool = True,
    ):
        r = records[0]

        get_page = f"/page_details/{r['id']}"  # item_id

        hx_attrs = (
            {
                "hx_get": get_page,
                "hx_target": "body",
                "hx_replace_url": "true",
                "hx_push_url": "true",
            }
            if row_link
            else {}
        )
        rating_summary = r["rating_summary"]

        return Tr(
            Td(get_page_description(item_id=r["id"], link="#")),
            *map(lambda id: Td(r[str(id)]), mode_id_list),
            Td(rating_summary),
            Td(
                A(
                    "See Details ➡️",
                    cls=AT.classic,
                ),
                cls="text-right",
            ),
            **hx_attrs,
        )

    rows = [
        render_row_based_on_type(records)
        for type_number, records in list(grouped.items())
    ]
    table = Table(
        Thead(
            Tr(
                Th("Page"),
                *map(Th, mode_name_list),
                Th("Rating Summary"),
                Th(""),
                cls="sticky top-16 z-25 bg-white",
            )
        ),
        Tbody(*rows),
    )

    return main_area(
        Title("Page Details"),
        table,
        active="Page Details",
        auth=auth,
    )


@app.get("/page_details/{item_id}")
def display_page_level_details(auth, item_id: int):
    # Prevent editing description for inactive items
    is_active_item = bool(items(where=f"id = {item_id} and active != 0"))
    if not is_active_item:
        return Redirect("/page_details")

    # Get mode name and ids from the db
    mode_id_list, mode_name_list = get_ordered_mode_name_and_id()

    # Avoid showing nav buttons (to go closest revisoned page) when there are no revisions for a page
    rev_data = revisions(where=f"item_id = {item_id}")  # TODO verify
    is_show_nav_btn = bool(rev_data)

    def _render_row(data, columns):
        tds = []
        for col in columns:
            value = data.get(col, "")
            if col == "rating":
                value = RATING_MAP.get(str(value), value)
            if col == "revision_date":
                value = date_to_human_readable(str(value))
            tds.append(Td(value))
        return Tr(*tds)

    def make_mode_title_for_table(mode_id):
        mode_details = modes(where=f"id = {mode_id}")
        if mode_details:
            mode_details = mode_details[0]
            mode_name, mode_description = (mode_details.name, mode_details.description)
        else:
            mode_name, mode_description = ("", "")
        return H2(mode_name, Subtitle(mode_description))

    ###### Title and Juz
    is_item_exist = items(where=f"id = {item_id}")
    if is_item_exist:
        page_description = get_page_description(item_id, is_bold=False, is_link=False)
        juz = f"Juz {get_juz_name(item_id=item_id)}"
    else:
        Redirect("/page_details")

    ####### Summary of first memorization
    if not mode_id_list:
        # If no modes exist, skip first revision logic
        memorization_summary = ""
    else:
        first_revision_data = revisions(
            where=f"item_id = {item_id} and hafiz_id = {auth} and mode_id IN ({', '.join(map(str, mode_id_list))})",
            order_by="revision_date ASC",
            limit=1,
        )

        if first_revision_data:
            first_revision = first_revision_data[0]
            first_memorized_date = (
                first_revision.revision_date
                if first_revision
                else Redirect("/page_details")
            )
            first_memorized_mode_id = (
                first_revision.mode_id if first_revision else Redirect("/page_details")
            )
            first_memorized_mode_name, description = make_mode_title_for_table(
                first_memorized_mode_id
            )
            memorization_summary = Div(
                H2("Summary"),
                P(
                    "This page was added on: ",
                    Span(Strong(date_to_human_readable(first_memorized_date))),
                    " under ",
                    Span(Strong(first_memorized_mode_name)),
                ),
            )
        else:
            memorization_summary = ""

    ########### Display Tables

    def build_revision_query(mode_ids, row_alias):
        """It fetch the revision data for the current item_id with specified mode_ids"""
        return f"""
            SELECT
                ROW_NUMBER() OVER (ORDER BY revision_date ASC) AS {row_alias},
                revision_date,
                rating,
                modes.name AS mode_name,
            CASE
                WHEN LAG(revision_date) OVER (ORDER BY revision_date) IS NULL THEN ''
                ELSE CAST(
                    JULIANDAY(revision_date) - JULIANDAY(LAG(revision_date) OVER (ORDER BY revision_date))
                    AS INTEGER
                )
            END AS interval
            FROM revisions
            JOIN modes ON revisions.mode_id = modes.id
            WHERE item_id = {item_id} AND hafiz_id = {auth} AND revisions.mode_id IN ({", ".join(map(str, mode_ids))})
            ORDER BY revision_date ASC;
        """

    def create_mode_table(mode_ids, is_summary=False):
        """Generate a table for the specified mode, returning both its visibility status and the table itself"""
        query = build_revision_query(mode_ids, "s_no")
        data = db.q(query)
        # determine table visibility
        has_data = len(data) > 0
        cols = ["s_no", "revision_date", "rating", "interval"]
        cls = "uk-overflow-auto max-h-[30vh] p-4"
        if is_summary:
            # summary table has all the modes, so we need to add mode_name column
            cols.insert(3, "mode_name")
            cls = ""

        table = Div(
            Table(
                Thead(*(Th(col.replace("_", " ").title()) for col in cols)),
                # get the table data for specific column
                Tbody(*[_render_row(row, cols) for row in data]),
            ),
            cls=cls,
        )

        return has_data, table

    ########### Summary Table
    has_summary_data, summary_table = create_mode_table(mode_id_list, is_summary=True)

    ########### Mode specific tables
    # Dynamically generate tables for each specific revision mode
    mode_data_map = {}
    for mode_id in mode_id_list:
        has_data, table = create_mode_table([mode_id])
        mode_data_map[mode_id] = (has_data, table)

    # Create mode sections dynamically
    mode_sections = []
    for mode_id in mode_id_list:
        is_display, table = mode_data_map[mode_id]
        if is_display:  # Only show if there's data
            mode_sections.append(Div(make_mode_title_for_table(mode_id), table))

    ########### Previous and Next Page Navigation
    def create_nav_button(item_id, arrow, show_nav):
        return A(
            arrow if item_id and show_nav else "",
            href=f"/page_details/{item_id}" if item_id is not None else "#",
            cls="uk-button uk-button-default",
        )

    def get_prev_next_item_ids(current_item_id):
        def build_nav_query(operator, sort_order):
            return f"""SELECT items.id, pages.page_number FROM revisions
                       LEFT JOIN items ON revisions.item_id = items.id
                       LEFT JOIN pages ON items.page_id = pages.id
                       WHERE revisions.hafiz_id = {auth} AND items.active != 0 AND items.id {operator} {current_item_id}
                       ORDER BY items.id {sort_order} LIMIT 1;"""

        prev_result = db.q(build_nav_query("<", "DESC"))
        next_result = db.q(build_nav_query(">", "ASC"))
        prev_id = prev_result[0]["id"] if prev_result else None
        next_id = next_result[0]["id"] if next_result else None
        return prev_id, next_id

    prev_id, next_id = get_prev_next_item_ids(item_id)
    # Show nav arrows if there is a previous/next items and that is revisioned page
    prev_pg = create_nav_button(prev_id, "⬅️", is_show_nav_btn)
    next_pg = create_nav_button(next_id, "➡️", is_show_nav_btn)

    ########### Display Editable Description and Start Text
    item_details = items[item_id]
    description = item_details.description
    start_text = item_details.start_text

    edit_description = DivVStacked(
        Table(
            Tr(
                Td("Description: "),
                Td(description, id="description"),
            ),
            Tr(
                Td("Start Text: "),
                Td(start_text, id="start_text", cls=TextT.lg),
            ),
            Tr(
                Td(
                    Div(
                        Button(
                            "Edit",
                            hx_get=f"/page_description/edit/{item_id}",
                            cls=(ButtonT.default, ButtonT.xs),
                        ),
                        id="btns",
                    ),
                    colspan="2",
                ),
                cls="text-center",
            ),
            cls="max-w-xs",
            id="item_description_table",
        ),
    )
    return main_area(
        Div(
            Div(
                DivFullySpaced(
                    prev_pg,
                    Div(
                        DivVStacked(
                            H1(page_description, cls="uk-text-center"),
                        ),
                        id="page-details-header",
                    ),
                    next_pg,
                ),
                Subtitle(Strong(juz), cls="uk-text-center"),
                edit_description,
                cls="space-y-8",
            ),
            Div(
                memorization_summary,
                Div(H2("Summary Table"), summary_table) if has_summary_data else None,
                *mode_sections,
                cls="space-y-6",
            ),
        ),
        active="Page Details",
        auth=auth,
    )


@app.get("/page_description/edit/{item_id}")
def page_description_edit_form(item_id: int):
    item_details = items[item_id]
    description = item_details.description
    start_text = item_details.start_text
    description_field = (
        LabelInput(
            "Description: ",
            name="description",
            value=description,
            id="description",
            hx_swap_oob="true",
            placeholder=description,
        ),
    )
    start_text_field = (
        LabelInput(
            "Start Text: ",
            name="start_text",
            value=start_text,
            id="start_text",
            hx_swap_oob="true",
            placeholder=start_text,
            cls=TextT.lg,
        ),
    )
    buttons = Div(
        Button(
            "Update",
            hx_put=f"/tables/items/{item_id}",
            hx_vals={"redirect_link": f"/page_details/{item_id}"},
            hx_target="#item_description_table",
            hx_select="#item_description_table",
            hx_select_oob="#page-details-header",
            hx_include="#description, #start_text",
            cls=(ButtonT.default, ButtonT.xs),
        ),
        Button(
            "Cancel",
            type="button",
            hx_get=f"/page_details/{item_id}",
            hx_target="#item_description_table",
            hx_select="#item_description_table",
            cls=(ButtonT.default, ButtonT.xs),
        ),
        cls="space-x-4",
        hx_swap_oob="true",
        id="btns",
    )

    return description_field, start_text_field, buttons


######################### SRS Pages #########################
@app.get("/srs")
def srs_detailed_page_view(
    auth,
    sort_col: str = "last_review_date",
    sort_type: str = "desc",
    is_bad_streak: bool = True,
):
    current_date = get_current_date(auth)

    # This table is responsible for showing the eligible pages for SRS
    columns = [
        "Page",
        "Start Text",
        "Bad Streak",
        "Last Review Date",
        "Bad %",
        "Total Count",
        "Bad Count",
    ]
    # based on the is_bad_steak we are filtering only the bad_streak items
    bad_streak_items = hafizs_items(
        where=f"mode_id <> 5 AND status IS NOT NULL {"AND bad_streak > 0" if is_bad_streak else ""}",
        order_by="last_review DESC",
    )

    # sorted the records based on the sort_col and sort_type from the input, and after page sort to group them on main sort
    eligible_records = []
    for record in bad_streak_items:
        current_item_id = record.item_id
        total_count = record.count
        bad_count = record.bad_count
        bad_percent = (
            format_number((bad_count / total_count) * 100) if total_count > 0 else 0
        )
        eligible_records.append(
            {
                "page": current_item_id,
                "start_text": get_start_text(current_item_id),
                "bad_streak": record.bad_streak,
                "last_review_date": record.last_review,
                "bad_%": bad_percent,
                "total_count": total_count,
                "bad_count": bad_count,
            }
        )
    eligible_records = sorted(eligible_records, key=lambda x: x["page"])
    eligible_records = sorted(
        eligible_records, key=lambda x: x[sort_col], reverse=(sort_type == "desc")
    )

    def render_srs_eligible_rows(record: dict):
        current_item_id = record["page"]
        page_description = get_page_description(current_item_id)
        start_srs_link = A(
            "Start SRS",
            hx_get=f"/start-srs/{current_item_id}",
            hx_target=f"#srs_eligible_row_{current_item_id}",
            hx_select=f"#srs_eligible_row_{current_item_id}",
            hx_select_oob="#current_srs_table",
            cls=AT.classic,
        )
        bad_percentage = (
            f"{record["bad_%"]}%"
            if isinstance(record["bad_%"], int)
            else record["bad_%"]
        )
        checkbox = CheckboxX(
            name=f"item_ids",
            value=current_item_id,
            cls="srs_eligible_table",
            _at_click="handleCheckboxClick($event)",  # To handle `shift+click` selection
        )
        return Tr(
            Td(page_description),
            Td(record["start_text"]),
            Td(checkbox),
            Td(start_srs_link),
            Td(record["bad_streak"]),
            Td(render_date(record["last_review_date"])),
            Td(bad_percentage),
            Td(record["total_count"]),
            Td(record["bad_count"]),
            id=f"srs_eligible_row_{current_item_id}",
        )

    sort_fields = Form(
        P("Sort Options: ", cls=TextT.bold),
        custom_select(name="sort_col", vals=columns, default_val=sort_col),
        custom_select(name="sort_type", vals=["ASC", "DESC"], default_val=sort_type),
        Hidden(name="is_bad_streak", value="False"),
        LabelSwitch(
            label="Bad Streak",
            id="is_bad_streak",
            cls=(FlexT.block, FlexT.center, FlexT.middle, "gap-2"),
            lbl_cls="leading-none md:leading-6",
            checked=is_bad_streak,
        ),
        P("Applying the sort...", cls="htmx-indicator"),
        cls=("w-full gap-1 md:gap-4", FlexT.block, FlexT.middle),
        hx_get="/srs",
        hx_target="#srs_eligible_table",
        hx_select="#srs_eligible_table",
        hx_swap="outerHTML",
        hx_trigger="change",
        hx_replace_url="true",
        hx_indicator=".htmx-indicator",
    )
    srs_start_btn = Button(
        "Start SRS",
        type="button",
        hx_post="/start-srs",
        hx_target="body",
        cls=(ButtonT.xs, ButtonT.primary),
    )
    srs_eligible_table = Div(
        H4("Eligible Pages"),
        Div(
            sort_fields,
            Form(
                Div(
                    Table(
                        Thead(
                            Tr(
                                *map(Td, columns[:2]),
                                Td(
                                    CheckboxX(
                                        cls=("select_all"),
                                        x_model="selectAll",  # To update the current status of the checkbox (checked or unchecked)
                                        _at_change="toggleAll()",  # based on that update the status of all the checkboxes
                                    )
                                ),
                                Td(""),
                                *map(Td, columns[2:]),
                            ),
                            cls="sticky z-50 top-0 bg-white",
                        ),
                        Tbody(*map(render_srs_eligible_rows, eligible_records)),
                        # defining the reactive data for for component to reference (alpine.js)
                        x_data=select_all_with_shift_click_for_summary_table(
                            class_name="srs_eligible_table"
                        ),
                        # initializing the updateSelectAll function to select the selectAll checkboxe.
                        # if all the below checkboxes are selected.
                        x_init="updateSelectAll()",
                    ),
                    cls="space-y-2 uk-overflow-auto h-[32vh]",
                    id="srs_eligible_table",
                ),
                srs_start_btn,
                cls="space-y-2",
            ),
        ),
        cls="space-y-2 mt-4",
    )

    ############ current_srs_table ############
    current_srs_items = [
        i.item_id
        for i in hafizs_items(
            where=f"mode_id = 5", order_by="next_review DESC, item_id ASC"
        )
    ]

    # To sort the current srs records by due date
    current_srs_records = []
    for item_id in current_srs_items:
        hafiz_items_data = hafizs_items(where=f"item_id = {item_id}")
        if hafiz_items_data:
            hafiz_items_data = hafiz_items_data[0]
            last_review = hafiz_items_data.last_review
            next_review = hafiz_items_data.next_review
            if next_review:
                due = calculate_days_difference(next_review, current_date)
            else:
                # this is to render the "-" if there is no next page
                due = -1
            last_interval = hafiz_items_data.last_interval
            current_interval = hafiz_items_data.current_interval
            next_interval = hafiz_items_data.next_interval

            current_srs_records.append(
                {
                    "page": item_id,
                    "start_text": get_start_text(item_id),
                    "last_review": last_review,
                    "next_review": next_review,
                    "due": due,
                    "last_interval": last_interval,
                    "current_interval": current_interval,
                    "next_interval": next_interval,
                }
            )
    current_srs_records = sorted(
        current_srs_records, key=lambda x: x["due"], reverse=True
    )

    # This table shows the current srs pages for the user
    def render_current_srs_rows(records: dict):
        due = records["due"]
        if due < 0:
            due = "-"

        return Tr(
            Td(get_page_description(records["page"])),
            Td(records["start_text"]),
            Td(render_date(records["last_review"])),
            Td(render_date(records["next_review"])),
            Td(due),
            Td(records["last_interval"]),
            Td(records["current_interval"]),
            Td(records["next_interval"]),
        )

    current_srs_table = Div(
        H4("SRS Pages"),
        Div(
            Table(
                Thead(
                    Tr(
                        Td("Page"),
                        Td("Start Text"),
                        Td("Last Review"),
                        Td("Next Review"),
                        Td("Due"),
                        # TODO: The column names are renamed temporarly for testing
                        Td("Previous Interval"),
                        Td("Actual Interval"),
                        Td("Next Interval"),
                    ),
                    cls="sticky z-50 top-0 bg-white",
                ),
                Tbody(*map(render_current_srs_rows, current_srs_records)),
            ),
            cls="space-y-2 uk-overflow-auto h-[32vh]",
            id="current_srs_table",
        ),
    )

    return main_area(
        Div(
            DivFullySpaced(
                H1(get_mode_name(5)),
                A(
                    "Refresh stats",
                    hx_get="/update_stats_column",
                    hx_swap="none",
                    cls=AT.classic,
                ),
            ),
            srs_eligible_table,
            Divider(cls=("mb-4", DividerT.icon)),
            current_srs_table,
        ),
        auth=auth,
        active="SRS",
    )


# This route is responsible for the adding single record
@app.get("/start-srs/{item_id}")
def start_srs(item_id: int, auth):
    current_date = get_current_date(auth)
    # TODO: Currently this only takes the first booster pack from the srs_booster_pack table
    booster_pack_details = srs_booster_pack[1]
    srs_booster_id = booster_pack_details.id
    next_interval = booster_pack_details.start_interval
    next_review_date = add_days_to_date(current_date, next_interval)

    # Change the current mode_id for the item_id to 5(srs)
    # TODO: What about the status?
    current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")
    if current_hafiz_items:
        current_hafiz_items = current_hafiz_items[0]
        current_hafiz_items.srs_booster_pack_id = srs_booster_id
        current_hafiz_items.mode_id = 5
        current_hafiz_items.next_interval = next_interval
        current_hafiz_items.srs_start_date = current_date
        current_hafiz_items.next_review = next_review_date
        hafizs_items.update(current_hafiz_items)

    return RedirectResponse("/srs")


# This route is responsible for the adding multiple record
@app.post("/start-srs")
async def start_srs_for_multiple_records(req, auth):
    form_data = await req.form()
    item_ids = form_data.getlist("item_ids")

    for item_id in item_ids:
        start_srs(item_id, auth)

    return RedirectResponse(req.headers.get("referer", "/srs"), status_code=303)


@app.get("/change_current_date")
def change_current_date(auth):
    current_date = get_current_date(auth)
    label_input = LabelInput(
        label="Current date",
        id="current_date",
        type="date",
        value=current_date,
        hx_post="/change_current_date",
        hx_target="body",
        hx_trigger="change",
    )
    return main_area(label_input, auth=auth)


@app.post("/change_current_date")
def update_current_date(auth, current_date: str):
    current_hafiz = hafizs[auth]
    current_hafiz.current_date = current_date
    hafizs.update(current_hafiz)
    return RedirectResponse("/change_current_date", status_code=303)


@app.get("/update_stats_column")
def update_stats_column():
    populate_hafizs_items_stat_columns()


@app.get("/settings")
def settings_page(auth):
    current_hafiz = hafizs[auth]

    def render_field(label, field_type, required=True, **kwargs):
        """
        Creates a standardized form input field with a label.
        - The field ID is generated by standardizing the label
        - The field value is populated from current_hafiz.field_name
        """
        field_name = standardize_column(label)
        value = getattr(current_hafiz, field_name)
        return LabelInput(
            label,
            id=field_name,
            type=field_type,
            value=value,
            required=required,
            **kwargs,
        )

    form = Form(
        render_field("Name", "text"),
        render_field("Daily Capacity", "number", False),
        render_field("Current Date", "date"),
        render_field("Display Count", "number", min=1),
        DivHStacked(
            Button("Update", type="submit", cls=ButtonT.primary),
            Button(
                "Discard", hx_get="/settings", hx_target="body", cls=ButtonT.destructive
            ),
        ),
        action="/settings",
        method="POST",
    )
    return main_area(
        Div(
            H1("Hafiz Preferences", cls=TextT.center),
            Div(form, cls="max-w-xl mx-auto"),
            cls="space-y-6",
        ),
        auth=auth,
        active="Settings",
    )


@app.post("/settings")
def update_setings(auth, hafiz_data: Hafiz):
    display_count = hafiz_data.display_count
    # Use existing value if display_count is invalid
    if not display_count or display_count < 0:
        hafiz_data.display_count = get_display_count(auth)

    hafizs.update(
        hafiz_data,
        hafizs[auth].id,
    )
    return RedirectResponse("/settings", status_code=303)


serve()
