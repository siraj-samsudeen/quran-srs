from fasthtml.common import *
import fasthtml.common as fh
from monsterui.all import *
from utils import *
from collections import defaultdict
from globals import *


def user_auth(req, sess):
    # Check user authentication
    user_id = req.scope["user_auth"] = sess.get("user_auth", None)
    if user_id:
        try:
            users[user_id]
        except NotFoundError:
            del sess["user_auth"]
            user_id = None
    if not user_id:
        return RedirectResponse("/users/login", status_code=303)


user_bware = Beforeware(
    user_auth,
    skip=["/users/login", "/users/signup", "/users/logout"],
)


def hafiz_auth(req, sess):
    # Check hafiz authentication
    hafiz_id = req.scope["auth"] = sess.get("auth", None)
    if hafiz_id:
        try:
            hafizs[hafiz_id]
        except NotFoundError:
            del sess["auth"]
            hafiz_id = None
    if not hafiz_id:
        return RedirectResponse("/users/hafiz_selection", status_code=303)

    revisions.xtra(hafiz_id=hafiz_id)
    hafizs_items.xtra(hafiz_id=hafiz_id)
    plans.xtra(hafiz_id=hafiz_id)


hafiz_bware = Beforeware(
    hafiz_auth,
    skip=[
        "/users/login",
        "/users/signup",
        "/users/logout",
        r"/users/\d+$",  # for deleting the user
        "/users/hafiz_selection",
        "/users/add_hafiz",
    ],
)

hyperscript_header = Script(src="https://unpkg.com/hyperscript.org@0.9.14")
alpinejs_header = Script(
    src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js", defer=True
)


# Create sub-apps with the beforeware
def create_app_with_auth(**kwargs):
    app, rt = fast_app(
        before=[user_bware, hafiz_bware],
        hdrs=(Theme.blue.headers(), hyperscript_header, alpinejs_header),
        bodykw={"hx-boost": "true"},
        **kwargs,
    )
    setup_toasts(app)
    return app, rt


def error_toast(sess, msg):
    add_toast(sess, msg, "error")


def success_toast(sess, msg):
    add_toast(sess, msg, "success")


def warning_toast(sess, msg):
    add_toast(sess, msg, "warning")


def main_area(*args, active=None, auth=None, **kwargs):
    is_active = lambda x: AT.primary if x == active else None
    title = A("Quran SRS", href="/")
    hafiz_name = A(
        f"{hafizs[auth].name if auth is not None else "Select hafiz"}",
        href="/users/hafiz_selection",
        method="GET",
    )
    additional_info = kwargs.get("additional_info")
    if additional_info:
        additional_info = " (", additional_info, ")"
    return Title("Quran SRS"), Container(
        Div(
            NavBar(
                A("Home", href="/", cls=is_active("Home")),
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
                A("Revision", href="/revision", cls=is_active("Revision")),
                A("Tables", href="/admin/tables", cls=is_active("Tables")),
                A("Report", href="/report", cls=is_active("Report")),
                A(
                    "SRS",
                    href="/srs",
                    cls=is_active("SRS"),
                ),
                A("Settings", href="/hafiz/settings", cls=is_active("Settings")),
                A("logout", href="/users/logout"),
                brand=H3(title, Span(" - "), hafiz_name, additional_info),
            ),
            DividerLine(y_space=0),
            cls="bg-white sticky top-0 z-50",
            hx_boost="false",
        ),
        Main(*args, cls="p-4", id="main") if args else None,
        cls=ContainerT.xl,
    )


def get_surah_name(page_id=None, item_id=None):
    if item_id:
        surah_id = items[item_id].surah_id
    else:
        surah_id = items(where=f"page_id = {page_id}")[0].surah_id
    surah_details = surahs[surah_id]
    return surah_details.name


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


def get_not_memorized_records(auth, custom_where=None):
    default = "hafizs_items.status_id = 6 AND items.active != 0"
    if custom_where:
        default = f"{custom_where}"
    not_memorized_tb = f"""
        SELECT items.id, items.surah_id, items.surah_name,
        hafizs_items.item_id, hafizs_items.status_id, hafizs_items.hafiz_id, pages.juz_number, pages.page_number, revisions.revision_date, revisions.id AS revision_id
        FROM items 
        LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
        LEFT JOIN pages ON items.page_id = pages.id
        LEFT JOIN revisions ON items.id = revisions.item_id
        WHERE {default};
    """
    return db.q(not_memorized_tb)


def get_current_date(auth) -> str:
    current_hafiz = hafizs[auth]
    current_date = current_hafiz.current_date
    if current_date is None:
        current_date = hafizs.update(current_date=current_time(), id=auth).current_date
    return current_date


def get_daily_capacity(auth):
    current_hafiz = hafizs[auth]
    return current_hafiz.daily_capacity


def populate_hafizs_items_stat_columns(item_id: int = None):

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
                bad_streak += 1
                good_streak = 0
            elif current_rating == 1:
                good_count += 1
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


def get_auth(sess):
    return sess.get("user_auth", None)


def get_hafizs_items(item_id):
    current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")
    if current_hafiz_items:
        return current_hafiz_items[0]
    else:
        return ValueError(f"No hafizs_items found for item_id {item_id}")


def get_mode_count(item_id, mode_id):
    mode_records = revisions(where=f"item_id = {item_id} AND mode_id = {mode_id}")
    return len(mode_records)


def get_start_text(item_id):
    try:
        return items[item_id].start_text
    except:
        return "-"


####################### Recent_review, Watch_list and SRS common function #######################


def get_next_interval(item_id, rating):
    hafiz_items_details = get_hafizs_items(item_id)
    srs_pack_details = srs_booster_pack[hafiz_items_details.srs_booster_pack_id]
    # Get the intervals for pridicting the next interval
    intervals = srs_pack_details.interval_days.split(",")
    intervals = list(map(int, intervals))
    rating_intervals = get_interval_triplet(
        target_interval=interval_to_check, interval_list=intervals
    )
    return rating_intervals[rating + 1]


def update_actual_interval(item_id, current_date):
    """Update the current_interval in hafizs_items table"""
    current_hafiz_details = get_hafizs_items(item_id)
    if current_hafiz_details.mode_id == 5:

        # This is to handle the case where if it is newly added into the SRS
        if revisions(
            where=f"item_id={current_hafiz_details.item_id} and mode_id={current_hafiz_details.mode_id}"
        ):
            last_review = current_hafiz_details.last_review
        else:
            last_review = current_hafiz_details.srs_start_date

        current_hafiz_details.current_interval = calculate_days_difference(
            last_review, current_date
        )
        hafizs_items.update(current_hafiz_details)


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


def graduate_the_item_id(item_id: int, mode_id: int, auth: int, checked: bool = True):
    last_review_date = get_lastest_date(item_id, mode_id)
    recent_review = {
        "mode_id": 3,
        "last_review": last_review_date,
        "next_review": add_days_to_date(last_review_date, 1),
    }
    watch_list = {
        "status_id": 4,
        "mode_id": 4,
        "last_review": last_review_date,
        "next_review": add_days_to_date(last_review_date, 7),
        "watch_list_graduation_date": None,
    }
    memorized = {
        "status_id": 1,
        "mode_id": 1,
        "last_review": None,
        "next_review": None,
        "watch_list_graduation_date": get_current_date(auth),
    }
    srs = {
        "status_id": 1,
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


def recalculate_intervals_on_srs_records(item_id: int, current_date: str):
    """
    Recalculates SRS (Spaced Repetition System) intervals for a specific item based on its revision history.
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
    # Here we are starting the recalculation from the first records last_interval
    # as the booster pack start_interval may change in future
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
            target_interval=last_interval, interval_list=intervals
        )
        calculated_next_interval = rating_intervals[rev.rating + 1]

        if calculated_next_interval > end_interval:
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


def get_srs_interval_list(item_id: int):
    current_hafiz_item = get_hafizs_items(item_id)
    booster_pack_details = srs_booster_pack[current_hafiz_item.srs_booster_pack_id]
    end_interval = booster_pack_details.end_interval

    booster_pack_intervals = booster_pack_details.interval_days.split(",")
    booster_pack_intervals = list(map(int, booster_pack_intervals))

    # To only get the intervals for this booster pack, as it contains more intervals than necessary
    interval_list = [
        interval for interval in booster_pack_intervals if interval < end_interval
    ]
    # And also get the next greater interval if it exists, for graduation logic
    first_greater = next(
        (interval for interval in booster_pack_intervals if interval >= end_interval),
        None,
    )
    if first_greater is not None:
        interval_list.append(first_greater)

    return interval_list


def get_interval_based_on_rating(item_id: int, rating: int):
    current_hafiz_item = get_hafizs_items(item_id)

    intervals = get_srs_interval_list(item_id)
    rating_intervals = get_interval_triplet(
        target_interval=current_hafiz_item.next_interval, interval_list=intervals
    )
    return rating_intervals[rating + 1]


def add_revision_record(**kwargs):
    revisions.insert(**kwargs)


def remove_revision_record(item_id, mode_id, date):
    revision_record = revisions(
        where=f"item_id = {item_id} AND mode_id = {mode_id} AND revision_date = '{date}'"
    )
    if not revision_record:
        return None
    revisions.delete(revision_record[0].id)


RATING_MAP = {"1": "✅ Good", "0": "😄 Ok", "-1": "❌ Bad"}


def render_rating(rating: int):
    return RATING_MAP.get(str(rating))


def rating_dropdown(
    default_mode="1",
    is_label=True,
    name="rating",
    cls="",
    **kwargs,
):
    def mk_options(o):
        id, name = o
        is_selected = lambda m: m == default_mode
        return fh.Option(name, value=id, selected=is_selected(id))

    return Div(
        fh.Select(
            map(mk_options, RATING_MAP.items()),
            label=("Rating" if is_label else None),
            name=name,
            select_kwargs={"name": name},
            cls=("[&>div]:h-8 uk-form-sm w-24", cls),
            **kwargs,
        ),
        cls="max-w-24 outline outline-gray-200 outline-1 rounded-sm",
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


def start_srs(item_id: int, auth):
    current_date = get_current_date(auth)
    # TODO: Currently this only takes the first booster pack from the srs_booster_pack table
    booster_pack_details = srs_booster_pack[1]
    srs_booster_id = booster_pack_details.id
    next_interval = booster_pack_details.start_interval
    next_review_date = add_days_to_date(current_date, next_interval)

    current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")
    if current_hafiz_items:
        current_hafiz_items = current_hafiz_items[0]
        current_hafiz_items.srs_booster_pack_id = srs_booster_id
        current_hafiz_items.mode_id = 5
        current_hafiz_items.status_id = 5
        current_hafiz_items.next_interval = next_interval
        current_hafiz_items.srs_start_date = current_date
        current_hafiz_items.next_review = next_review_date
        hafizs_items.update(current_hafiz_items)


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


def get_mode_name(mode_id: int):
    return modes[mode_id].name


def find_next_memorized_srs_item_id(item_id):
    memorized_and_srs_item_ids = [
        i.item_id for i in hafizs_items(where="status_id IN (1, 5)")
    ]
    return find_next_greater(memorized_and_srs_item_ids, item_id)


def get_unrevised_memorized_item_ids(auth, plan_id):
    qry = f"""
        SELECT hafizs_items.item_id from hafizs_items
        LEFT JOIN revisions ON revisions.item_id == hafizs_items.item_id AND revisions.plan_id = {plan_id} AND revisions.hafiz_id = {auth}
        WHERE hafizs_items.status_id IN (1, 5) AND hafizs_items.hafiz_id = {auth} AND revisions.item_id is Null;
        """
    data = db.q(qry)
    return [r["item_id"] for r in data]


def get_last_item_id():
    return items(where="active = 1", order_by="id DESC")[0].id


def get_display_count(auth):
    current_hafiz = hafizs[auth]
    return current_hafiz.display_count


def get_juz_name(page_id=None, item_id=None):
    if item_id:
        qry = f"SELECT pages.juz_number FROM pages LEFT JOIN items ON pages.id = items.page_id WHERE items.id = {item_id}"
        juz_number = db.q(qry)[0]["juz_number"]
    else:
        juz_number = pages[page_id].juz_number
    return juz_number


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


def delete_hafiz(hafiz_id: int):
    hafizs.delete(hafiz_id)
