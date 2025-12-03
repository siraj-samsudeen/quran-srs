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
# DaisyUI (Tailwind component library) - same classes work in Phoenix
daisyui_css = Link(
    rel="stylesheet",
    href="https://cdn.jsdelivr.net/npm/daisyui@4.12.14/dist/full.min.css",
)
style_css = Link(rel="stylesheet", href="/public/css/style.css")
favicon = Link(rel="icon", type="image/svg+xml", href="/public/favicon.svg")


# Create sub-apps with the beforeware
def create_app_with_auth(**kwargs):
    app, rt = fast_app(
        before=[user_bware, hafiz_bware],
        hdrs=(
            Theme.blue.headers(),
            daisyui_css,
            hyperscript_header,
            alpinejs_header,
            style_css,
            favicon,
        ),
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

    # Admin dropdown
    admin_dropdown = Div(
        Button(
            "Admin ▾",
            type="button",
            cls=f"px-3 py-2 rounded hover:bg-gray-100 {AT.primary if active in ['Admin', 'Tables'] else ''}",
            **{"@click": "open = !open"},
        ),
        Div(
            A("Tables", href="/admin/tables", cls="block px-4 py-2 hover:bg-gray-100"),
            A(
                "Backup",
                href="/admin/backup",
                cls="block px-4 py-2 hover:bg-gray-100",
                hx_boost="false",
            ),
            A(
                "All Backups",
                href="/admin/backups",
                cls="block px-4 py-2 hover:bg-gray-100",
                hx_boost="false",
            ),
            cls="absolute left-0 mt-2 w-48 bg-white border rounded-lg shadow-lg z-20",
            **{"x-show": "open", "@click.away": "open = false", "x-cloak": true},
        ),
        cls="relative inline-block",
        **{"x-data": "{ open: false }"},
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
                admin_dropdown,
                A("Report", href="/report", cls=is_active("Report")),
                A("Settings", href="/hafiz/settings", cls=is_active("Settings")),
                A("Logout", href="/users/logout"),
                brand=H3(title, Span(" - "), hafiz_name),
                cls="py-3",
            ),
            DividerLine(y_space=0),
            cls="bg-background sticky top-0 z-50",
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
    default = f"hafizs_items.memorized = 0 AND items.active != 0"
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
    # 100% percentage of daily capacity
    return get_daily_capacity(auth)


def get_last_added_full_cycle_page(auth):
    current_date = get_current_date(auth)
    last_full_cycle_record = db.q(
        f"""
        SELECT hafizs_items.page_number FROM revisions
        LEFT JOIN hafizs_items ON revisions.item_id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
        WHERE revisions.revision_date < '{current_date}' AND revisions.mode_code = '{FULL_CYCLE_MODE_CODE}' AND revisions.hafiz_id = {auth}
        ORDER BY revisions.revision_date DESC, revisions.item_id DESC
        LIMIT 1
    """
    )
    if last_full_cycle_record:
        return last_full_cycle_record[0]["page_number"]


def find_next_memorized_item_id(item_id):
    memorized_and_srs_item_ids = [
        i.item_id
        for i in hafizs_items(
            where=f"memorized = 1 AND mode_code IN ('{FULL_CYCLE_MODE_CODE}', '{SRS_MODE_CODE}')"
        )
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

        for rev in items_rev_data:
            current_rating = rev.rating

            if current_rating == -1:
                bad_streak += 1
                good_streak = 0
            elif current_rating == 1:
                good_streak += 1
                bad_streak = 0
            else:
                good_streak = 0
                bad_streak = 0

            last_review = rev.revision_date

        return {
            "good_streak": good_streak,
            "bad_streak": bad_streak,
            "last_review": last_review,
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


def get_hafizs_items(item_id):
    current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")
    if current_hafiz_items:
        return current_hafiz_items[0]
    else:
        return ValueError(f"No hafizs_items found for item_id {item_id}")


def get_mode_count(item_id, mode_code):
    mode_records = revisions(where=f"item_id = {item_id} AND mode_code = '{mode_code}'")
    return len(mode_records)


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
    return revisions.insert(**kwargs)


def render_rating(rating: int):
    return RATING_MAP.get(str(rating))


def rating_dropdown(
    rating="None",
    name="rating",
    cls="",
    **kwargs,
):
    def mk_options(o):
        id, name = o
        is_selected = lambda m: m == str(rating)
        return fh.Option(name, value=id, selected=is_selected(id))

    return fh.Select(
        fh.Option("-", value="None", selected=rating == "None"),
        *map(mk_options, RATING_MAP.items()),
        name=name,
        # DaisyUI: select (base), select-bordered (adds border), select-sm (small dropdowns)
        cls=f"select select-bordered select-sm {cls}",
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


def get_mode_name(mode_code: str):
    return modes[mode_code].name


def get_last_item_id():
    return items(where="active = 1", order_by="id DESC")[0].id


def get_juz_name(page_id=None, item_id=None):
    if item_id:
        qry = f"SELECT pages.juz_number FROM pages LEFT JOIN items ON pages.id = items.page_id WHERE items.id = {item_id}"
        juz_number = db.q(qry)[0]["juz_number"]
    else:
        juz_number = pages[page_id].juz_number
    return juz_number


def get_mode_name_and_code():
    all_modes = modes()
    mode_code_list = [mode.code for mode in all_modes]
    mode_name_list = [mode.name for mode in all_modes]
    return mode_code_list, mode_name_list


def delete_hafiz(hafiz_id: int):
    hafizs.delete(hafiz_id)


def get_current_plan_id():
    unique_seq_plan_id = [
        i.id for i in plans(where="completed <> 1", order_by="id DESC")
    ]

    if unique_seq_plan_id and not len(unique_seq_plan_id) > 1:
        return unique_seq_plan_id[0]
    return None


def get_item_page_portion(item_id: int) -> float:
    """
    Calculates the portion of a page that a single item represents.
    For example, if a page is divided into 4 items, each item represents 0.25 of the page.
    """
    page_no = items[item_id].page_id
    total_parts = items(where=f"page_id = {page_no} and active = 1")
    if not total_parts:
        return 0
    return 1 / len(total_parts)


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
        total_count += get_item_page_portion(item_id)
    return format_number(total_count)


def get_full_review_item_ids(
    auth, total_page_count, mode_specific_hafizs_items_records, item_ids
):
    current_date = get_current_date(auth)
    plan_id = get_current_plan_id()

    def get_next_item_range_from_item_id(
        eligible_item_ids, start_item_id, total_page_count
    ):
        """Get items from a list starting from a specific number."""
        try:
            start_index = eligible_item_ids.index(start_item_id)
            item_ids_to_process = eligible_item_ids[start_index:]
        except ValueError:
            item_ids_to_process = eligible_item_ids

        final_item_ids = []
        current_page_count = 0
        for item_id in item_ids_to_process:
            if current_page_count >= total_page_count:
                break
            current_page_count += get_item_page_portion(item_id)
            final_item_ids.append(item_id)

        is_plan_finished = len(eligible_item_ids) == len(final_item_ids)

        return is_plan_finished, final_item_ids

    if plan_id is not None:
        # Filter out items that have been revised in the current plan (but not today)
        revised_items_in_plan = revisions(
            where=f"mode_code = '{FULL_CYCLE_MODE_CODE}' AND plan_id = {plan_id} AND revision_date != '{current_date}'",
            order_by="revision_date DESC, id DESC",
        )
        # Convert to set for faster lookup
        revised_items_in_plan_set = {r.item_id for r in revised_items_in_plan}
        eligible_item_ids = [i for i in item_ids if i not in revised_items_in_plan_set]

        last_added_item_id = (
            revised_items_in_plan[0].item_id if revised_items_in_plan else 0
        )

        # Find the next item to start the review from
        next_item_id = find_next_greater(eligible_item_ids, last_added_item_id)
    else:
        eligible_item_ids = []
        next_item_id = 0

    is_plan_finished, next_item_ids = get_next_item_range_from_item_id(
        eligible_item_ids, next_item_id, total_page_count
    )

    # Get all item_ids revised today in full_cycle mode
    today_full_cycle_revisions = {
        r.item_id
        for r in revisions(
            where=f"revision_date = '{current_date}' AND mode_code = '{FULL_CYCLE_MODE_CODE}'"
        )
    }

    # Get items that have been revised today in full_cycle mode, but are not in the session_item_ids
    today_revisioned_items = [
        item["item_id"]
        for item in mode_specific_hafizs_items_records
        if item["item_id"] in today_full_cycle_revisions
        and item["item_id"] not in next_item_ids
    ]

    # Combine and sort the item_ids
    final_item_ids = sorted(list(set(next_item_ids + today_revisioned_items)))
    return is_plan_finished, final_item_ids


def create_count_link(count: int, rev_ids: str):
    if not rev_ids:
        return count
    return A(
        count,
        href=f"/revision/bulk_edit?ids={rev_ids}",
        cls=AT.classic,
    )


def row_background_color(rating):
    # Determine background color based on rating
    if rating is None:
        return
    if rating == 1:  # Good
        bg_color = "bg-green-100"
    elif rating == 0:  # Ok
        bg_color = "bg-yellow-50"
    elif rating == -1:  # Bad
        bg_color = "bg-red-50"
    return bg_color


def render_range_row(records, current_date=None, mode_code=None, plan_id=None):
    """Render a single table row for an item in the summary table.

    Args:
        records: contains the item and revision record
        current_date: Current date for the hafiz
        mode_code: Mode code
        plan_id: Plan ID (optional, for full cycle)
    """
    item_id = records["item"].id
    rating = records["revision"].rating if records["revision"] else None
    row_id = f"row-{mode_code}-{item_id}"

    if rating is None:
        action_link_attr = {"hx_post": f"/add/{item_id}"}
    else:
        action_link_attr = {"hx_put": f"/edit/{records["revision"].id}"}

    vals_dict = {"date": current_date, "mode_code": mode_code, "item_id": item_id}
    if plan_id:
        vals_dict["plan_id"] = plan_id

    rating_dropdown_input = rating_dropdown(
        rating=rating,
        id=f"rev-{item_id}",
        data_testid=f"rating-{item_id}",
        **action_link_attr,
        hx_vals=vals_dict,
        hx_trigger="change",
        hx_target=f"#{row_id}",
        hx_swap="outerHTML",
    )

    # Checkbox for bulk selection - only show if not already rated
    if rating is None:
        checkbox_cell = Td(
            fh.Input(
                type="checkbox",
                # when form is submitted, all checked values go into item_ids[] array
                name="item_ids",
                # each checkbox carries the item's ID
                value=item_id,
                cls="checkbox bulk-select-checkbox",
                **{"@change": "count = $root.querySelectorAll('.bulk-select-checkbox:checked').length"},
            ),
            cls="w-8 text-center",
        )
    else:
        # Empty Td for rated items - maintains column alignment
        checkbox_cell = Td(cls="w-8")

    return Tr(
        checkbox_cell,
        Td(get_page_description(item_id)),
        Td(
            records["item"].start_text or "-",
            cls="text-lg",
        ),
        Td(
            Form(
                rating_dropdown_input,
                Hidden(name="item_id", value=item_id),
            )
        ),
        id=row_id,
        cls=row_background_color(rating),
    )


def get_mode_condition(mode_code: str):
    # The full cycle mode is a special case, where it also shows the SRS pages
    mode_code_mapping = {
        FULL_CYCLE_MODE_CODE: [f"'{FULL_CYCLE_MODE_CODE}'", f"'{SRS_MODE_CODE}'"],
    }
    retrieved_mode_codes = mode_code_mapping.get(mode_code)
    if retrieved_mode_codes is None:
        mode_condition = f"mode_code = '{mode_code}'"
    else:
        mode_condition = f"mode_code IN ({', '.join(retrieved_mode_codes)})"
    return mode_condition


def render_bulk_action_bar(mode_code, current_date, plan_id):
    """Render a sticky bulk action bar for applying ratings to selected items."""
    plan_id_val = plan_id or ""

    def bulk_button(rating_value, label, btn_cls):
        return Button(
            label,
            hx_post="/bulk_rate",
            hx_vals={"rating": rating_value, "mode_code": mode_code, "date": current_date, "plan_id": plan_id_val},
            hx_include=f"#{mode_code}_tbody [name='item_ids']:checked",
            hx_target=f"#summary_table_{mode_code}",
            hx_swap="outerHTML",
            # Reset count immediately to hide bulk bar while HTMX processes
            **{"@click": "count = 0"},
            cls=(btn_cls, "px-4 py-2"),
        )

    return Div(
        Div(
            Span("Selected: ", cls="font-medium"),
            Span(x_text="count", cls="font-bold"),
            cls="text-sm",
        ),
        Div(
            bulk_button(1, "Good", ButtonT.primary),
            bulk_button(0, "Ok", ButtonT.secondary),
            bulk_button(-1, "Bad", ButtonT.destructive),
            cls="flex gap-2",
        ),
        id=f"bulk-bar-{mode_code}",
        cls="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg p-3 flex justify-between items-center z-50",
        # x-show controls visibility when count changes; style ensures hidden by default after HTMX swap
        x_show="count > 0",
        style="display: none",
    )


def render_summary_table(auth, mode_code, item_ids, is_plan_finished):
    current_date = get_current_date(auth)
    plan_id = get_current_plan_id()

    # Query all today's revisions once for efficiency
    plan_condition = f"AND plan_id = {plan_id}" if plan_id else ""
    today_revisions = revisions(
        where=f"revision_date = '{current_date}' AND item_id IN ({', '.join(map(str, item_ids))}) AND {get_mode_condition(mode_code)} {plan_condition}"
    )
    # Create lookup dictionary: item_id -> rating
    revisions_lookup = {rev.item_id: rev for rev in today_revisions}

    # Query all items data once
    items_with_revisions = [
        {"item": items[item_id], "revision": revisions_lookup.get(item_id)}
        for item_id in item_ids
    ]

    # Render rows
    body_rows = [
        render_range_row(
            records,
            current_date,
            mode_code,
            plan_id,
        )
        for records in items_with_revisions
    ]
    if not body_rows:
        return (mode_code, None)

    if is_plan_finished:
        body_rows.append(
            Tr(
                Td(
                    Span(
                        "Plan is finished, mark pages in ",
                        A("Profile", href="/profile", cls=AT.classic),
                        " to continue, or a new plan will be created",
                    ),
                    colspan=4,
                    cls="text-center text-lg",
                )
            )
        )

    bulk_bar = render_bulk_action_bar(mode_code, current_date, plan_id)

    table = Div(
        Table(
            Thead(
                Tr(
                    Th(
                        fh.Input(
                            type="checkbox",
                            cls="checkbox select-all-checkbox",
                            **{"@change": "$root.querySelectorAll('.bulk-select-checkbox').forEach(cb => cb.checked = $el.checked); count = $el.checked ? $root.querySelectorAll('.bulk-select-checkbox').length : 0"},
                        ),
                        cls="w-8 text-center",
                    ),
                    Th("Page", cls="min-w-24"),
                    Th("Start Text", cls="min-w-24"),
                    Th("Rating", cls="min-w-16"),
                )
            ),
            Tbody(*body_rows, id=f"{mode_code}_tbody"),
            cls=(TableT.middle, TableT.divider, TableT.sm),
            # To prevent scroll jumping
            hx_on__before_request="sessionStorage.setItem('scroll', window.scrollY)",
            hx_on__after_swap="window.scrollTo(0, sessionStorage.getItem('scroll'))",
        ),
        bulk_bar,
        id=f"summary_table_{mode_code}",
        x_data="{ count: 0 }",
    )
    return (mode_code, table)


def make_summary_table(
    mode_code: str,
    auth: str,
    total_page_count=0,
    table_only=False,
):
    current_date = get_current_date(auth)

    def is_review_due(item: dict) -> bool:
        """Check if item is due for review today or overdue."""
        return day_diff(item["next_review"], current_date) >= 0

    def is_reviewed_today(item: dict) -> bool:
        return item["last_review"] == current_date

    def has_mode_code(item: dict, mode_code: str) -> bool:
        return item["mode_code"] == mode_code

    def has_memorized(item: dict) -> bool:
        return item["memorized"]

    def has_revisions(item: dict) -> bool:
        """Check if item has revisions for current mode."""
        return bool(
            revisions(
                where=f"item_id = {item['item_id']} AND mode_code = '{item['mode_code']}'"
            )
        )

    def has_revisions_today(item: dict) -> bool:
        """Check if item has revisions for current mode today."""
        return bool(
            revisions(
                where=f"item_id = {item['item_id']} AND mode_code = '{item['mode_code']}' AND revision_date = '{current_date}'"
            )
        )

    def has_newly_memorized_for_today(item: dict) -> bool:
        newly_memorized_record = revisions(
            where=f"item_id = {item['item_id']} AND revision_date = '{current_date}' AND mode_code = '{NEW_MEMORIZATION_MODE_CODE}'"
        )
        return len(newly_memorized_record) == 1

    qry = f"""
        SELECT hafizs_items.item_id, items.surah_name, hafizs_items.next_review, hafizs_items.last_review, hafizs_items.mode_code, hafizs_items.memorized, hafizs_items.page_number FROM hafizs_items
        LEFT JOIN items on hafizs_items.item_id = items.id
        WHERE {get_mode_condition(mode_code)} AND hafizs_items.hafiz_id = {auth}
        ORDER BY hafizs_items.item_id ASC
    """
    mode_specific_hafizs_items_records = db.q(qry)

    # Route-specific condition builders
    route_conditions = {
        DAILY_REPS_MODE_CODE: lambda item: (
            (is_review_due(item) and not has_newly_memorized_for_today(item))
            or (is_reviewed_today(item) and has_mode_code(item, DAILY_REPS_MODE_CODE))
        ),
        WEEKLY_REPS_MODE_CODE: lambda item: (
            has_mode_code(item, WEEKLY_REPS_MODE_CODE)
            and (
                is_review_due(item) or (is_reviewed_today(item) and has_revisions(item))
            )
        ),
        SRS_MODE_CODE: lambda item: (is_review_due(item) or has_revisions_today(item)),
        FULL_CYCLE_MODE_CODE: lambda item: has_memorized(item),
    }

    filtered_records = [
        i for i in mode_specific_hafizs_items_records if route_conditions[mode_code](i)
    ]

    def get_unique_item_ids(records):
        return list(dict.fromkeys(record["item_id"] for record in records))

    if mode_code == SRS_MODE_CODE:
        exclude_start_page = get_last_added_full_cycle_page(auth)

        # Exclude 3 days worth of pages from SRS (upcoming pages not yet reviewed)
        if exclude_start_page is not None:
            exclude_end_page = exclude_start_page + (
                get_full_cycle_daily_limit(auth) * 3
            )

            filtered_records = [
                record
                for record in filtered_records
                if record["page_number"] < exclude_start_page
                or record["page_number"] > exclude_end_page
            ]

        item_ids = get_unique_item_ids(filtered_records)

        # On a daily basis, This will rotate the items to show (first/last) pages, to ensure that the user can focus on all the pages.
        srs_daily_limit = get_srs_daily_limit(auth)
        if get_day_from_date(current_date) % 2 == 0:
            item_ids = item_ids[:srs_daily_limit]
        else:
            item_ids = item_ids[-srs_daily_limit:]
    else:
        item_ids = get_unique_item_ids(filtered_records)

    if mode_code == FULL_CYCLE_MODE_CODE:
        is_plan_finished, item_ids = get_full_review_item_ids(
            auth=auth,
            total_page_count=total_page_count,
            mode_specific_hafizs_items_records=mode_specific_hafizs_items_records,
            item_ids=item_ids,
        )
    else:
        is_plan_finished = False

    result = render_summary_table(
        auth=auth,
        mode_code=mode_code,
        item_ids=item_ids,
        is_plan_finished=is_plan_finished,
    )
    if table_only:
        return result[1]  # Just the table element for HTMX swap
    return result


def render_current_date(auth):
    current_date = get_current_date(auth)
    return P(
        Span("System Date: ", cls=TextPresets.bold_lg),
        Span(date_to_human_readable(current_date), data_testid="system-date"),
    )
