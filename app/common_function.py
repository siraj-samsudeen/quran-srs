from fasthtml.common import *
import fasthtml.common as fh
from monsterui.all import *
from utils import *
from collections import defaultdict
from globals import *
import math


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
    skip=["/users/login", "/users/logout"],
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
style_css = Link(rel="stylesheet", href="/public/css/style.css")


# Create sub-apps with the beforeware
def create_app_with_auth(**kwargs):
    app, rt = fast_app(
        before=[user_bware, hafiz_bware],
        hdrs=(Theme.blue.headers(), hyperscript_header, alpinejs_header, style_css),
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


def main_area(*args, active=None, auth=None):
    is_active = lambda x: AT.primary if x == active else None
    title = A("Quran SRS", href="/")
    hafiz_name = A(
        f"{hafizs[auth].name if auth is not None else "Select hafiz"}",
        href="/users/hafiz_selection",
        method="GET",
    )
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
                A(
                    "New Memorization",
                    href="/new_memorization",
                    cls=is_active("New Memorization"),
                ),
                A("Revision", href="/revision", cls=is_active("Revision")),
                A("Tables", href="/admin/tables", cls=is_active("Tables")),
                A("Report", href="/report", cls=is_active("Report")),
                A("Settings", href="/hafiz/settings", cls=is_active("Settings")),
                A("logout", href="/users/logout"),
                brand=H3(title, Span(" - "), hafiz_name),
                cls="py-3",
            ),
            DividerLine(y_space=0),
            cls="bg-white sticky top-0 z-50",
            hx_boost="false",
        ),
        Main(*args, id="main") if args else None,
        cls=(ContainerT.xl, "px-0.5"),
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
    else:
        page, description = item_description.split(" ", maxsplit=1)
    return A(
        Span(page, cls=TextPresets.bold_lg),
        Br(),
        Span(description),
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
    # The page is not started, if it is not memorized and mode the is full cycle (as it is the default mode)
    default = f"hafizs_items.memorized = 0 AND hafizs_items.mode_id = {FULL_CYCLE_MODE_ID} AND items.active != 0"
    if custom_where:
        default = f"{custom_where}"
    not_memorized_tb = f"""
        SELECT items.id, items.surah_id, items.surah_name,
        hafizs_items.item_id, hafizs_items.memorized, hafizs_items.hafiz_id, pages.juz_number, pages.page_number, revisions.revision_date, revisions.id AS revision_id
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


def get_srs_daily_limit(auth):
    # 50% percentage of daily capacity
    return math.ceil(get_daily_capacity(auth) * 0.5)


def get_full_cycle_daily_limit(auth):
    # 50% percentage of daily capacity
    return math.ceil(get_daily_capacity(auth) * 0.5)


def get_last_added_full_cycle_page(auth):
    current_date = get_current_date(auth)
    last_full_cycle_record = db.q(
        f"""
        SELECT hafizs_items.page_number FROM revisions
        LEFT JOIN hafizs_items ON revisions.item_id = hafizs_items.id AND hafizs_items.hafiz_id = {auth}
        WHERE revisions.revision_date < '{current_date}' AND revisions.mode_id = {FULL_CYCLE_MODE_ID} AND revisions.hafiz_id = {auth}
        ORDER BY revisions.revision_date DESC, revisions.item_id DESC
        LIMIT 1
    """
    )
    if last_full_cycle_record:
        return last_full_cycle_record[0]["page_number"]


def find_next_memorized_item_id(item_id):
    memorized_and_srs_item_ids = [
        i.item_id for i in hafizs_items(where="memorized = 1")
    ]
    return find_next_greater(memorized_and_srs_item_ids, item_id)


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


def get_actual_interval(item_id):
    hafiz_items_details = get_hafizs_items(item_id)
    current_date = get_current_date(hafiz_items_details.hafiz_id)

    last_review = hafiz_items_details.last_review
    if not last_review:
        return None
    return calculate_days_difference(last_review, current_date)


def get_planned_next_interval(item_id):
    return get_hafizs_items(item_id).next_interval


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
            cls=cls,
            **kwargs,
        ),
        cls="rounded-sm",
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


def get_unrevised_memorized_item_ids(auth, plan_id):
    qry = f"""
        SELECT hafizs_items.item_id from hafizs_items
        LEFT JOIN revisions ON revisions.item_id == hafizs_items.item_id AND revisions.plan_id = {plan_id} AND revisions.hafiz_id = {auth}
        WHERE hafizs_items.memorized = 1 AND hafizs_items.hafiz_id = {auth} AND revisions.item_id is Null;
        """
    data = db.q(qry)
    return [r["item_id"] for r in data]


def get_last_item_id():
    return items(where="active = 1", order_by="id DESC")[0].id


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


def get_current_plan_id():
    unique_seq_plan_id = [
        i.id for i in plans(where="completed <> 1", order_by="id DESC")
    ]

    if unique_seq_plan_id and not len(unique_seq_plan_id) > 1:
        return unique_seq_plan_id[0]
    return None


def get_page_count(records: list[Revision] = None, item_ids: list = None) -> float:
    total_count = 0
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


def get_full_review_item_ids(auth, total_display_count, ct, item_ids, current_plan_id):
    current_date = get_current_date(auth)

    def has_revisions_today(item: dict) -> bool:
        """Check if item has revised today for current mode."""
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

    def has_full_cycle_mode_id(item: dict) -> bool:
        return item["mode_id"] == FULL_CYCLE_MODE_ID

    if current_plan_id is not None:
        # eliminate items that are already revisioned in the current plan_id
        eligible_item_ids = [
            i
            for i in item_ids
            if not revisions(
                where=f"item_id = {i} AND mode_id = {FULL_CYCLE_MODE_ID} AND plan_id = {current_plan_id} AND revision_date != '{current_date}'"
            )
        ]
        # TODO: handle the new user that not have any revision/plan_id
        last_added_revision = revisions(
            where=f"revision_date <> '{current_date}' AND mode_id = {FULL_CYCLE_MODE_ID} AND plan_id = {current_plan_id}",
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

    # take today revision data that are not in today's target (item_ids)
    display_conditions = {
        "full_cycle": lambda item: (
            has_full_cycle_mode_id(item)
            and has_revisions_today(item)
            and item["item_id"] not in item_ids
        )
    }
    today_revisioned_items = list(
        dict.fromkeys(i["item_id"] for i in ct if display_conditions["full_cycle"](i))
    )

    item_ids = sorted(item_ids + today_revisioned_items)
    return item_ids


def create_count_link(count: int, rev_ids: str):
    if not rev_ids:
        return count
    return A(
        count,
        href=f"/revision/bulk_edit?ids={rev_ids}",
        cls=AT.classic,
    )


def render_summary_table(auth, route, mode_ids, item_ids, plan_id=None):
    is_accordion = route != "full_cycle"
    mode_id_mapping = {
        "full_cycle": FULL_CYCLE_MODE_ID,
        "new_memorization": NEW_MEMORIZATION_MODE_ID,
        "daily_reps": DAILY_REPS_MODE_ID,
        "weekly_reps": WEEKLY_REPS_MODE_ID,
        "srs": SRS_MODE_ID,
    }
    mode_id = mode_id_mapping[route]
    is_newly_memorized = mode_id == NEW_MEMORIZATION_MODE_ID
    is_full_review = mode_id == FULL_CYCLE_MODE_ID
    is_srs = mode_id == SRS_MODE_ID
    current_date = get_current_date(auth)
    # This list is to close the accordian, if all the checkboxes are selected
    is_all_selected = []

    # Sort the item_ids by not revised(top) and revised(bottom)
    # records = db.q(
    #     f"""
    #     SELECT hafizs_items.item_id FROM hafizs_items
    #     LEFT JOIN revisions on hafizs_items.item_id = revisions.item_id AND hafizs_items.hafiz_id = revisions.hafiz_id AND revisions.revision_date = '{current_date}'
    #     WHERE hafizs_items.hafiz_id = {auth} AND hafizs_items.item_id IN ({', '.join(map(str, item_ids))})
    #     ORDER BY revisions.item_id, hafizs_items.item_id ASC
    # """
    # )
    # item_ids = [r["item_id"] for r in records]

    def render_range_row(item_id: str):
        row_id = f"{route}-row-{item_id}"
        plan_condition = f"AND plan_id = {plan_id}" if is_full_review else ""
        current_revision_data = revisions(
            where=f"revision_date = '{current_date}' AND item_id = {item_id} AND mode_id IN ({', '.join(mode_ids)}) {plan_condition}"
        )
        is_checked = len(current_revision_data) != 0
        is_all_selected.append(is_checked)
        checkbox_hx_attrs = {
            "hx_post": f"/add/{item_id}",
            "hx_select": f"#{row_id}",
            # TODO: make the full cycle to only rerender on full summary table
            "hx_select_oob": f"#stat-row-{mode_id}, #total_row, #total-ticked-count-footer, #{route}-header"
            + (", #full_cycle_link_table, #page" if is_full_review else ""),
            "hx_target": f"#{row_id}",
            "hx_swap": "outerHTML",
        }
        vals_dict = {"date": current_date, "mode_id": mode_id}
        if is_full_review:
            vals_dict["plan_id"] = plan_id
        record_btn = CheckboxX(
            name=f"is_checked",
            value="1",
            **checkbox_hx_attrs,
            hx_vals=vals_dict,
            hx_include=f"#rev-{item_id}",
            checked=is_checked,
            cls=(
                f"{route}_ids",
                "add-checkbox",  # This class-name is used to disable the checkbox when closing the date to prevent it from being updated
                "disabled:opacity-50",
            ),
            _at_click="handleCheckboxClick($event)",  # To handle `shift+click` selection
            data_testid=f"{item_id}-checkbox",
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
            if is_full_review:
                change_rating_hx_attrs["hx_vals"]["plan_id"] = plan_id

        rating_dropdown_input = rating_dropdown(
            default_mode=str(default_rating),
            is_label=False,
            id=f"rev-{item_id}",
            cls="update-dropdown",  # This class-name is used to disable the dropdown when closing the date to prevent it from being updated
            hx_trigger="change",
            **change_rating_hx_attrs,
        )

        return Tr(
            Td(get_page_description(item_id)),
            Td(
                get_start_text(item_id),
                cls=TextT.lg,
            ),
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
            cls="bg-green-100" if is_checked else None,
        )

    body_rows = list(map(render_range_row, item_ids))
    if not body_rows:
        return None

    select_all_vals = {
        "mode_id": mode_id,
        "date": current_date,
    }
    if is_full_review:
        select_all_vals["plan_id"] = plan_id

    render_output = (
        Div(
            Table(
                Thead(
                    Tr(
                        Th("Page", cls="min-w-24"),
                        Th("Start Text", cls="min-w-24"),
                        (
                            Th("Reps")
                            if not (is_newly_memorized or is_full_review or is_srs)
                            else None
                        ),
                        Th(
                            CheckboxX(
                                name="is_select_all",
                                hx_vals=select_all_vals,
                                hx_post="/bulk_add",
                                hx_trigger="change",
                                hx_include=f"#{route}_ratings",
                                hx_select=f"#{route}_tbody",
                                hx_select_oob=f"#stat-row-{mode_id}, #total_row, #total-ticked-count-footer, #{route}-header"
                                + (
                                    ", #full_cycle_link_table, #page"
                                    if is_full_review
                                    else ""
                                ),
                                hx_target=f"#{route}_tbody",
                                hx_swap="outerHTML",
                                checked=all(is_all_selected),
                                cls=(
                                    "select_all",
                                    "bulk-add-checkbox",  # This class-name is used to disable the checkbox when closing the date to prevent it from being updated
                                    "disabled:opacity-50",
                                    ("hidden" if mode_id == SRS_MODE_ID else None),
                                ),
                                x_model="selectAll",  # To update the current status of the checkbox (checked or unchecked)
                            )
                        ),
                        Th("Rating", cls="min-w-24"),
                    )
                ),
                Tbody(*body_rows, id=f"{route}_tbody", data_testid=f"{route}_tbody"),
                id=f"{route}_summary_table",
                x_data=select_all_with_shift_click_for_summary_table(
                    class_name=f"{route}_ids"
                ),
                # initializing the updateSelectAll function to select the selectAll checkboxe.
                # if all the below checkboxes are selected.
                x_init="updateSelectAll()",
                # This is responsible for preserving the scroll position when hx-swap happens, to prevent scroll jump.
                hx_on__before_request="sessionStorage.setItem('scroll', window.scrollY)",
                hx_on__after_swap="window.scrollTo(0, sessionStorage.getItem('scroll'))",
            ),
        ),
    )
    return (
        AccordionItem(
            Span(modes[mode_id].name, id=f"{route}-header"),
            render_output,
            open=(not all(is_all_selected)),
        )
        if is_accordion
        else render_output
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
        return item["last_review"] == current_date

    def has_mode_id(item: dict, mode_id: int) -> bool:
        return item["mode_id"] == mode_id

    def has_memorized(item: dict) -> bool:
        return item["memorized"]

    def has_revisions(item: dict) -> bool:
        """Check if item has revisions for current mode."""
        return bool(
            revisions(
                where=f"item_id = {item['item_id']} AND mode_id = {item['mode_id']}"
            )
        )

    def has_revisions_today(item: dict) -> bool:
        """Check if item has revisions for current mode today."""
        return bool(
            revisions(
                where=f"item_id = {item['item_id']} AND mode_id = {item['mode_id']} AND revision_date = '{current_date}'"
            )
        )

    def has_newly_memorized_for_today(item: dict) -> bool:
        newly_memorized_record = revisions(
            where=f"item_id = {item['item_id']} AND revision_date = '{current_date}' AND mode_id = {NEW_MEMORIZATION_MODE_ID}"
        )
        return len(newly_memorized_record) == 1

    qry = f"""
        SELECT hafizs_items.item_id, items.surah_name, hafizs_items.next_review, hafizs_items.last_review, hafizs_items.mode_id, hafizs_items.memorized, hafizs_items.page_number FROM hafizs_items
        LEFT JOIN items on hafizs_items.item_id = items.id 
        WHERE hafizs_items.mode_id IN ({', '.join(mode_ids)}) AND hafizs_items.hafiz_id = {auth}
        ORDER BY hafizs_items.item_id ASC
    """
    ct = db.q(qry)

    # Route-specific condition builders
    route_conditions = {
        "daily_reps": lambda item: (
            (is_review_due(item) and not has_newly_memorized_for_today(item))
            or (is_reviewed_today(item) and has_mode_id(item, DAILY_REPS_MODE_ID))
        ),
        "weekly_reps": lambda item: (
            has_mode_id(item, WEEKLY_REPS_MODE_ID)
            and (
                is_review_due(item) or (is_reviewed_today(item) and has_revisions(item))
            )
        ),
        "srs": lambda item: (is_review_due(item) or has_revisions_today(item)),
        "full_cycle": lambda item: has_memorized(item),
    }

    filtered_records = [i for i in ct if route_conditions[route](i)]

    def get_unique_item_ids(records):
        return list(dict.fromkeys(record["item_id"] for record in records))

    if route == "srs":
        srs_daily_limit = get_srs_daily_limit(auth)
        exclude_start_page = get_last_added_full_cycle_page(auth)

        # Exclude 3 days worth of pages from SRS (upcoming pages not yet reviewed)
        if exclude_start_page is not None:
            exclude_end_page = exclude_start_page + (srs_daily_limit * 3)

            filtered_records = [
                record
                for record in filtered_records
                if record["page_number"] < exclude_start_page
                or record["page_number"] > exclude_end_page
            ]

        item_ids = get_unique_item_ids(filtered_records)

        # On a daily basis, This will rotate the items to show (first/last) pages, to ensure that the user can focus on all the pages.
        if get_day_from_date(current_date) % 2 == 0:
            item_ids = item_ids[:srs_daily_limit]
        else:
            item_ids = item_ids[-srs_daily_limit:]
    else:
        item_ids = get_unique_item_ids(filtered_records)

    if route == "full_cycle":
        item_ids = get_full_review_item_ids(
            auth=auth,
            total_display_count=total_display_count,
            ct=ct,
            item_ids=item_ids,
            current_plan_id=plan_id,
        )

    return render_summary_table(
        route=route,
        auth=auth,
        mode_ids=mode_ids,
        item_ids=item_ids,
        plan_id=plan_id,
    )


# This funtion is to convert the mode ids to string
def get_reps_table(mode_ids, route, auth):
    """Helper to get table and target count for rep modes."""
    return make_summary_table(
        mode_ids=[str(mid) for mid in mode_ids],
        route=route,
        auth=auth,
    )


def render_current_date(auth):
    current_date = get_current_date(auth)
    return P(
        Span("System Date: ", cls=TextPresets.bold_lg),
        Span(date_to_human_readable(current_date), id="current_date_description"),
    )
