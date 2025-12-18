from fasthtml.common import *
import fasthtml.common as fh
from monsterui.all import *
from utils import *
from collections import defaultdict
from constants import *
from database import (
    db,
    hafizs,
    hafizs_items,
    items,
    modes,
    pages,
    plans,
    revisions,
    surahs,
    users,
    Hafiz_Items,
    Revision,
)
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
    skip=["/users/login", "/users/logout", "/users/signup"],
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
        return RedirectResponse("/hafiz/selection", status_code=303)

    revisions.xtra(hafiz_id=hafiz_id)
    hafizs_items.xtra(hafiz_id=hafiz_id)
    plans.xtra(hafiz_id=hafiz_id)


hafiz_bware = Beforeware(
    hafiz_auth,
    skip=[
        "/users/login",
        "/users/logout",
        "/users/signup",
        r"/users/delete/\d+$",
        "/users/account",  # User-level settings, no hafiz required
        "/hafiz/selection",
        "/hafiz/add",
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
# Tabulator (interactive data tables with sorting, filtering, search)
tabulator_css = Link(
    rel="stylesheet",
    href="https://unpkg.com/tabulator-tables@6.3.0/dist/css/tabulator_semanticui.min.css",
)
tabulator_js = Script(src="https://unpkg.com/tabulator-tables@6.3.0/dist/js/tabulator.min.js")
style_css = Link(rel="stylesheet", href="/public/css/style.css")
favicon = Link(rel="icon", type="image/svg+xml", href="/public/favicon.svg")


# Create sub-apps with the beforeware
def create_app_with_auth(**kwargs):
    app, rt = fast_app(
        before=[user_bware, hafiz_bware],
        hdrs=(
            Theme.blue.headers(),
            daisyui_css,
            tabulator_css,
            tabulator_js,
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
        href="/hafiz/selection",
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
                    href="/profile/table",
                    cls=is_active("Memorization Status"),
                ),
                A(
                    "Page Details",
                    href="/page_details",
                    cls=is_active("Page Details"),
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


def group_by_type(data, current_type, feild=None, preserve_order=False):
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
    # preserve_order=True keeps SQL ORDER BY; False sorts by key (page number)
    if preserve_order:
        return dict(grouped)
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


def get_hafizs_items(item_id) -> Hafiz_Items | None:
    """Get hafiz_items record for the given item_id, or None if not found."""
    current_hafiz_items = hafizs_items(where=f"item_id = {item_id}")
    if current_hafiz_items:
        return current_hafiz_items[0]
    return None


def get_mode_count(item_id, mode_code):
    mode_records = revisions(where=f"item_id = {item_id} AND mode_code = '{mode_code}'")
    return len(mode_records)


def get_actual_interval(item_id):
    hafiz_items_details = get_hafizs_items(item_id)
    if hafiz_items_details is None:
        return None
    current_date = get_current_date(hafiz_items_details.hafiz_id)

    last_review = hafiz_items_details.last_review
    if not last_review:
        return None
    return calculate_days_difference(last_review, current_date)


def get_planned_next_interval(item_id):
    hafiz_items_details = get_hafizs_items(item_id)
    if hafiz_items_details is None:
        return None
    return hafiz_items_details.next_interval


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


def get_mode_icon(mode_code: str) -> str:
    """Returns emoji icon for each mode."""
    icons = {
        NEW_MEMORIZATION_MODE_CODE: "🆕",
        DAILY_REPS_MODE_CODE: "☀️",
        WEEKLY_REPS_MODE_CODE: "📅",
        FORTNIGHTLY_REPS_MODE_CODE: "📆",
        MONTHLY_REPS_MODE_CODE: "🗓️",
        FULL_CYCLE_MODE_CODE: "🔄",
        SRS_MODE_CODE: "🧠",
    }
    return icons.get(mode_code, "📖")


def can_graduate(mode_code: str) -> bool:
    """Returns True if mode can be manually graduated (DR, WR, FR, MR)."""
    return mode_code in GRADUATABLE_MODES


def get_last_item_id():
    result = items(where="active = 1", order_by="id DESC")
    return result[0].id if result else 0


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


def get_full_review_item_ids(auth, mode_specific_hafizs_items_records, item_ids):
    """Get all eligible Full Cycle items (not yet revised in current plan + revised today)."""
    current_date = get_current_date(auth)
    plan_id = get_current_plan_id()

    if plan_id is not None:
        # Filter out items that have been revised in the current plan (but not today)
        revised_items_in_plan = revisions(
            where=f"mode_code = '{FULL_CYCLE_MODE_CODE}' AND plan_id = {plan_id} AND revision_date != '{current_date}'",
            order_by="revision_date DESC, id DESC",
        )
        # Convert to set for faster lookup
        revised_items_in_plan_set = {r.item_id for r in revised_items_in_plan}
        eligible_item_ids = [i for i in item_ids if i not in revised_items_in_plan_set]

        # Check if plan is finished (no more items to review)
        is_plan_finished = len(eligible_item_ids) == 0
    else:
        eligible_item_ids = []
        is_plan_finished = False

    # Get all item_ids revised today in full_cycle mode
    today_full_cycle_revisions = {
        r.item_id
        for r in revisions(
            where=f"revision_date = '{current_date}' AND mode_code = '{FULL_CYCLE_MODE_CODE}'"
        )
    }

    # Get items that have been revised today in full_cycle mode, but are not in eligible_item_ids
    today_revisioned_items = [
        item["item_id"]
        for item in mode_specific_hafizs_items_records
        if item["item_id"] in today_full_cycle_revisions
        and item["item_id"] not in eligible_item_ids
    ]

    # Combine and sort the item_ids
    final_item_ids = sorted(list(set(eligible_item_ids + today_revisioned_items)))
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


def render_range_row(records, current_date=None, mode_code=None, plan_id=None, hide_start_text=False):
    """Render a single table row for an item in the summary table.

    Args:
        records: contains the item and revision record
        current_date: Current date for the hafiz
        mode_code: Mode code
        plan_id: Plan ID (optional, for full cycle)
        hide_start_text: If True, hide start text (for consecutive pages)
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
        Td(
            A(
                get_page_number(item_id),
                href=f"/page_details/{item_id}",
                cls="font-mono font-bold hover:underline",
            ),
            cls="w-12 text-center",
        ),
        Td(
            # Hidden text with tap-to-reveal using Alpine.js
            Div(
                Span("● ● ●", cls="text-gray-400 cursor-pointer select-none", x_show="!revealed", **{"@click": "revealed = true"}),
                Span(records["item"].start_text or "-", x_show="revealed", x_cloak=True),
                x_data="{ revealed: false }",
            )
            if hide_start_text
            else Span(records["item"].start_text or "-"),
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


def render_pagination_controls(mode_code, current_page, total_pages, total_items, info_text=None):
    """Render pagination controls for navigating between pages."""
    is_first_page = current_page <= 1
    is_last_page = current_page >= total_pages

    # Compute bounded page values to avoid out-of-range requests
    prev_page = max(1, current_page - 1)
    next_page = min(total_pages, current_page + 1)

    prev_button = Button(
        "👈",
        hx_get=f"/page/{mode_code}?page={prev_page}",
        hx_target=f"#summary_table_{mode_code}",
        hx_swap="outerHTML",
        cls=(ButtonT.secondary, "px-4 py-2"),
        data_testid=f"pagination-prev-{mode_code}",
    ) if not is_first_page else Span()

    next_button = Button(
        "👉",
        hx_get=f"/page/{mode_code}?page={next_page}",
        hx_target=f"#summary_table_{mode_code}",
        hx_swap="outerHTML",
        cls=(ButtonT.secondary, "px-4 py-2"),
        data_testid=f"pagination-next-{mode_code}",
    ) if not is_last_page else Span()

    # Use custom info_text if provided, otherwise default format
    default_info = f"Page {current_page} of {total_pages} ({total_items} items)"
    page_info = Span(
        info_text or default_info,
        cls="text-sm font-medium",
        data_testid=f"pagination-info-{mode_code}",
    )

    return Div(
        Div(
            prev_button,
            page_info,
            next_button,
            cls="flex justify-between items-center gap-4",
        ),
        cls="p-3 border-t bg-gray-50",
        data_testid=f"pagination-controls-{mode_code}",
    )


def render_bulk_action_bar(mode_code, current_date, plan_id):
    """Render a sticky bulk action bar for applying ratings to selected items.

    Note: Bulk selection is page-local - selections reset when navigating pages or applying filters.
    """
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

    # Select all checkbox - toggles all items
    select_all_checkbox = Div(
        fh.Input(
            type="checkbox",
            cls="checkbox",
            **{
                "@change": """
                    $root.querySelectorAll('.bulk-select-checkbox').forEach(cb => cb.checked = $el.checked);
                    count = $el.checked ? $root.querySelectorAll('.bulk-select-checkbox').length : 0
                """,
                ":checked": "count > 0 && count === $root.querySelectorAll('.bulk-select-checkbox').length",
            },
        ),
        # Show "Select All" when not all selected, "Clear All" when all selected
        Span("Select All", cls="text-sm ml-2", x_show="count < $root.querySelectorAll('.bulk-select-checkbox').length"),
        Span("Clear All", cls="text-sm ml-2", x_show="count === $root.querySelectorAll('.bulk-select-checkbox').length"),
        Span("|", cls="text-gray-300 mx-2"),
        Span(x_text="count", cls="font-bold"),
        cls="flex items-center",
    )

    return Div(
        select_all_checkbox,
        Div(
            bulk_button(1, "Good", ButtonT.primary),
            bulk_button(0, "Ok", ButtonT.secondary),
            bulk_button(-1, "Bad", ButtonT.destructive),
            cls="flex gap-2",
        ),
        id=f"bulk-bar-{mode_code}",
        cls="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg p-3 flex justify-between items-center z-50",
    )


def render_surah_header(surah_id, juz_number):
    """Render a surah section header row with surah name and juz indicator."""
    surah_name = surahs[surah_id].name
    return Tr(
        Td(
            Span(f"📖 {surah_name}", cls="font-semibold"),
            Span(f" (Juz {juz_number})", cls="text-gray-500 text-sm"),
            colspan=4,
            cls="bg-base-200 py-1 px-2",
        ),
        cls="surah-header",
    )


def render_summary_table(auth, mode_code, item_ids, is_plan_finished, page=1, items_per_page=None):
    current_date = get_current_date(auth)
    plan_id = get_current_plan_id()

    # Calculate pagination
    total_items = len(item_ids)

    # Calculate page-equivalents for all modes (items can be partial pages)
    if item_ids:
        total_page_equivalents = sum(get_item_page_portion(item_id) for item_id in item_ids)
    else:
        total_page_equivalents = 0

    if items_per_page and items_per_page > 0:
        total_pages = math.ceil(total_items / items_per_page)
        page = max(1, min(page, total_pages))  # Clamp page to valid range
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_item_ids = item_ids[start_idx:end_idx]
    else:
        paginated_item_ids = item_ids
        total_pages = 1

    # Query all today's revisions once for efficiency
    plan_condition = f"AND plan_id = {plan_id}" if plan_id else ""
    if paginated_item_ids:
        today_revisions = revisions(
            where=f"revision_date = '{current_date}' AND item_id IN ({', '.join(map(str, paginated_item_ids))}) AND {get_mode_condition(mode_code)} {plan_condition}"
        )
    else:
        today_revisions = []
    # Create lookup dictionary: item_id -> rating
    revisions_lookup = {rev.item_id: rev for rev in today_revisions}

    # Query all items data once
    items_with_revisions = [
        {"item": items[item_id], "revision": revisions_lookup.get(item_id)}
        for item_id in paginated_item_ids
    ]

    # Group items by surah and render with headers
    # Track consecutive pages to hide start text for recall practice
    body_rows = []
    current_surah_id = None
    prev_page_id = None
    for records in items_with_revisions:
        item = records["item"]
        # Add surah header when surah changes
        if item.surah_id != current_surah_id:
            current_surah_id = item.surah_id
            juz_number = get_juz_name(item_id=item.id)
            body_rows.append(render_surah_header(current_surah_id, juz_number))
            # Reset consecutive tracking on surah change
            prev_page_id = None
        # Check if this is a consecutive page (hide start text for recall)
        is_consecutive = prev_page_id is not None and item.page_id == prev_page_id + 1
        # Add the item row
        body_rows.append(
            render_range_row(records, current_date, mode_code, plan_id, hide_start_text=is_consecutive)
        )
        prev_page_id = item.page_id
    # Show empty-state message when no items on current page (keeps table structure intact)
    if not body_rows:
        body_rows = [
            Tr(
                Td(
                    "No pages to review on this page.",
                    colspan=4,  # spans checkbox, page, start text, rating columns
                    cls="text-center text-gray-500 py-4",
                )
            )
        ]

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

    # Render pagination controls
    pagination_controls = None
    if items_per_page and total_pages > 1:
        # Show page-equivalents when item count differs from page count (due to split pages)
        if total_items != int(total_page_equivalents):
            info_text = f"Page {page} of {total_pages} ({total_items} items, {format_number(total_page_equivalents)} pages)"
        else:
            info_text = None
        pagination_controls = render_pagination_controls(mode_code, page, total_pages, total_items, info_text)

    table_content = [
        Table(
            Tbody(*body_rows, id=f"{mode_code}_tbody"),
            cls=(TableT.middle, TableT.divider, TableT.sm),
            # To prevent scroll jumping
            hx_on__before_request="sessionStorage.setItem('scroll', window.scrollY)",
            hx_on__after_swap="window.scrollTo(0, sessionStorage.getItem('scroll'))",
        ),
    ]

    if pagination_controls:
        table_content.append(pagination_controls)

    table_content.append(bulk_bar)

    table = Div(
        *table_content,
        id=f"summary_table_{mode_code}",
        x_data="{ count: 0 }",
    )
    return (mode_code, table)


# === Mode Filter Predicates ===
#
# Predicates determine which items appear in each mode's summary table.
#
# Pattern Overview:
# - Daily Reps: Special case - shows items due OR reviewed today (excludes newly memorized)
# - Standard Rep Modes (Weekly/Fortnightly/Monthly): Must be in mode AND (due OR reviewed today with history)
# - SRS: Due OR has revisions today in SRS mode
# - Full Cycle: Item must be marked as memorized
#
# Standard rep modes use a factory function (_create_standard_rep_mode_predicate) to avoid
# duplication since they share identical logic. See also REP_MODES_CONFIG in fixed_reps.py.


def _is_review_due(item: dict, current_date: str) -> bool:
    """Check if item is due for review today or overdue."""
    return day_diff(item["next_review"], current_date) >= 0


def _is_reviewed_today(item: dict, current_date: str) -> bool:
    """Check if item was reviewed today."""
    return item["last_review"] == current_date


def _has_memorized(item: dict) -> bool:
    """Check if item is marked as memorized."""
    return item["memorized"]


def _has_revisions_in_mode(item: dict) -> bool:
    """Check if item has any revisions in its current mode."""
    item_id = item["item_id"]
    mode_code = item["mode_code"]
    return bool(revisions(where=f"item_id = {item_id} AND mode_code = '{mode_code}'"))


def _has_revisions_today_in_mode(item: dict, current_date: str) -> bool:
    """Check if item has revisions in its current mode today."""
    item_id = item["item_id"]
    mode_code = item["mode_code"]
    return bool(
        revisions(
            where=f"item_id = {item_id} AND mode_code = '{mode_code}' AND revision_date = '{current_date}'"
        )
    )


def _was_newly_memorized_today(item: dict, current_date: str) -> bool:
    """Check if item was newly memorized today (has NM revision today)."""
    item_id = item["item_id"]
    return bool(
        revisions(
            where=f"item_id = {item_id} AND revision_date = '{current_date}' AND mode_code = '{NEW_MEMORIZATION_MODE_CODE}'"
        )
    )


def _create_standard_rep_mode_predicate(mode_code: str):
    """
    Factory function to create predicates for standard rep modes.

    Standard rep modes (Weekly, Fortnightly, Monthly) share identical logic:
    - Item must be in the specified mode
    - Item is due for review OR reviewed today with revision history

    Args:
        mode_code: The mode code constant (e.g., WEEKLY_REPS_MODE_CODE)

    Returns:
        A predicate function that takes (item, current_date) and returns bool
    """

    def predicate(item: dict, current_date: str) -> bool:
        if item["mode_code"] != mode_code:
            return False
        return _is_review_due(item, current_date) or (
            _is_reviewed_today(item, current_date) and _has_revisions_in_mode(item)
        )

    return predicate


def should_include_in_daily_reps(item: dict, current_date: str) -> bool:
    """Predicate for Daily Reps mode: due for review OR reviewed today (unless just memorized)."""
    is_due = _is_review_due(item, current_date) and not _was_newly_memorized_today(
        item, current_date
    )
    reviewed_in_mode = (
        _is_reviewed_today(item, current_date)
        and item["mode_code"] == DAILY_REPS_MODE_CODE
    )
    return is_due or reviewed_in_mode


# Generate predicates for standard rep modes using the factory
# These three modes share identical logic, differing only in mode code
should_include_in_weekly_reps = _create_standard_rep_mode_predicate(WEEKLY_REPS_MODE_CODE)
should_include_in_fortnightly_reps = _create_standard_rep_mode_predicate(FORTNIGHTLY_REPS_MODE_CODE)
should_include_in_monthly_reps = _create_standard_rep_mode_predicate(MONTHLY_REPS_MODE_CODE)


def should_include_in_srs(item: dict, current_date: str) -> bool:
    """Predicate for SRS mode: due for review OR has revisions today."""
    return _is_review_due(item, current_date) or _has_revisions_today_in_mode(
        item, current_date
    )


def should_include_in_full_cycle(item: dict, current_date: str) -> bool:
    """Predicate for Full Cycle mode: item must be memorized."""
    return _has_memorized(item)


# Mode to predicate mapping
# Note: Weekly/Fortnightly/Monthly predicates are generated by _create_standard_rep_mode_predicate()
# to avoid duplication. Daily has unique logic (excludes newly memorized) and remains separate.
# See also: REP_MODES_CONFIG in fixed_reps.py for mode graduation logic.
MODE_PREDICATES = {
    DAILY_REPS_MODE_CODE: should_include_in_daily_reps,
    WEEKLY_REPS_MODE_CODE: should_include_in_weekly_reps,
    FORTNIGHTLY_REPS_MODE_CODE: should_include_in_fortnightly_reps,
    MONTHLY_REPS_MODE_CODE: should_include_in_monthly_reps,
    SRS_MODE_CODE: should_include_in_srs,
    FULL_CYCLE_MODE_CODE: should_include_in_full_cycle,
}


def make_summary_table(
    mode_code: str,
    auth: str,
    table_only=False,
    page=1,
    items_per_page=None,
):
    current_date = get_current_date(auth)

    qry = f"""
        SELECT hafizs_items.item_id, items.surah_name, hafizs_items.next_review, hafizs_items.last_review, hafizs_items.mode_code, hafizs_items.memorized, hafizs_items.page_number FROM hafizs_items
        LEFT JOIN items on hafizs_items.item_id = items.id
        WHERE {get_mode_condition(mode_code)} AND hafizs_items.hafiz_id = {auth}
        ORDER BY hafizs_items.item_id ASC
    """
    mode_specific_hafizs_items_records = db.q(qry)

    # Filter using named predicates
    predicate = MODE_PREDICATES[mode_code]
    filtered_records = [
        item
        for item in mode_specific_hafizs_items_records
        if predicate(item, current_date)
    ]

    def get_unique_item_ids(records):
        return list(dict.fromkeys(record["item_id"] for record in records))

    if mode_code == SRS_MODE_CODE:
        exclude_start_page = get_last_added_full_cycle_page(auth)

        # Exclude upcoming pages from SRS (pages not yet reviewed in Full Cycle)
        # Hardcoded to 60 pages (~3 days worth at typical 20 pages/day)
        if exclude_start_page is not None:
            SRS_EXCLUSION_ZONE = 60
            exclude_end_page = exclude_start_page + SRS_EXCLUSION_ZONE

            filtered_records = [
                record
                for record in filtered_records
                if record["page_number"] < exclude_start_page
                or record["page_number"] > exclude_end_page
            ]

    item_ids = get_unique_item_ids(filtered_records)

    if mode_code == FULL_CYCLE_MODE_CODE:
        is_plan_finished, item_ids = get_full_review_item_ids(
            auth=auth,
            mode_specific_hafizs_items_records=mode_specific_hafizs_items_records,
            item_ids=item_ids,
        )
    else:
        is_plan_finished = False

    # Hide tab entirely if no items to display
    if not item_ids:
        return None

    result = render_summary_table(
        auth=auth,
        mode_code=mode_code,
        item_ids=item_ids,
        is_plan_finished=is_plan_finished,
        page=page,
        items_per_page=items_per_page,
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


# === New Memorization Tab ===


def render_nm_row(item, current_date, is_memorized_today, prev_page_id=None):
    """Render a single row in the New Memorization table with checkbox."""
    item_id = item.id
    row_id = f"row-NM-{item_id}"

    # Check if this is a consecutive page (hide start text for recall)
    is_consecutive = prev_page_id is not None and item.page_id == prev_page_id + 1

    # Checkbox for marking as memorized
    checkbox = fh.Input(
        type="checkbox",
        name="item_ids",
        value=item_id,
        checked=is_memorized_today,
        cls="checkbox bulk-select-checkbox",
        hx_post=f"/new_memorization/toggle/{item_id}",
        hx_target=f"#summary_table_{NEW_MEMORIZATION_MODE_CODE}",
        hx_swap="outerHTML",
        hx_vals={"date": current_date},
        # Update count when checkbox changes
        **{"@change": "count = $root.querySelectorAll('.bulk-select-checkbox:checked').length"},
    )

    # Row background: green if memorized today
    bg_class = "bg-green-100" if is_memorized_today else ""

    return Tr(
        Td(checkbox, cls="w-8 text-center"),
        Td(
            A(
                get_page_number(item_id),
                href=f"/page_details/{item_id}",
                cls="font-mono font-bold hover:underline",
            ),
            cls="w-12 text-center",
        ),
        Td(
            # Hidden text with tap-to-reveal using Alpine.js
            Div(
                Span("● ● ●", cls="text-gray-400 cursor-pointer select-none", x_show="!revealed", **{"@click": "revealed = true"}),
                Span(item.start_text or "-", x_show="revealed", x_cloak=True),
                x_data="{ revealed: false }",
            )
            if is_consecutive
            else Span(item.start_text or "-"),
            cls="text-lg",
        ),
        id=row_id,
        cls=bg_class,
    )


def render_nm_bulk_action_bar(current_date):
    """Render bulk action bar for New Memorization mode.

    Unlike other modes that have Good/Ok/Bad buttons, NM only has
    a single 'Mark as Memorized' button.
    """
    mode_code = NEW_MEMORIZATION_MODE_CODE

    # Select all checkbox - toggles all unchecked items
    select_all_checkbox = Div(
        fh.Input(
            type="checkbox",
            cls="checkbox",
            **{
                "@change": """
                    $root.querySelectorAll('.bulk-select-checkbox:not(:checked)').forEach(cb => {
                        if ($el.checked) cb.checked = true;
                    });
                    if (!$el.checked) {
                        $root.querySelectorAll('.bulk-select-checkbox').forEach(cb => cb.checked = false);
                    }
                    count = $root.querySelectorAll('.bulk-select-checkbox:checked').length
                """,
                ":checked": "count > 0 && count === $root.querySelectorAll('.bulk-select-checkbox').length",
            },
        ),
        Span("Select All", cls="text-sm ml-2", x_show="count < $root.querySelectorAll('.bulk-select-checkbox').length"),
        Span("Clear All", cls="text-sm ml-2", x_show="count === $root.querySelectorAll('.bulk-select-checkbox').length"),
        Span("|", cls="text-gray-300 mx-2"),
        Span(x_text="count", cls="font-bold"),
        cls="flex items-center",
    )

    mark_button = Button(
        "Mark as Memorized",
        hx_post="/new_memorization/bulk_mark",
        hx_vals={"date": current_date},
        hx_include=f"#{mode_code}_tbody [name='item_ids']:checked",
        hx_target=f"#summary_table_{mode_code}",
        hx_swap="outerHTML",
        **{"@click": "count = 0"},
        cls=(ButtonT.primary, "px-4 py-2"),
    )

    return Div(
        select_all_checkbox,
        mark_button,
        id=f"bulk-bar-{mode_code}",
        cls="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg p-3 flex justify-between items-center z-50",
    )


def make_new_memorization_table(auth, page=1, items_per_page=None, table_only=False):
    """Build the New Memorization tab content showing unmemorized pages.

    Shows:
    - Unmemorized items (hafizs_items.memorized = 0)
    - Items marked as memorized today (NM revisions today) - these stay until Close Date
    """
    current_date = get_current_date(auth)
    mode_code = NEW_MEMORIZATION_MODE_CODE

    # Query unmemorized items
    qry = f"""
        SELECT hafizs_items.item_id, hafizs_items.page_number
        FROM hafizs_items
        WHERE hafizs_items.hafiz_id = {auth}
          AND hafizs_items.memorized = 0
        ORDER BY hafizs_items.item_id ASC
    """
    unmemorized_records = db.q(qry)
    unmemorized_item_ids = set(r["item_id"] for r in unmemorized_records)

    # Get today's NM revisions (to show "memorized today" state)
    today_nm_revisions = revisions(
        where=f"revision_date = '{current_date}' AND mode_code = '{NEW_MEMORIZATION_MODE_CODE}' AND hafiz_id = {auth}"
    )
    today_nm_item_ids = set(r.item_id for r in today_nm_revisions)

    # Combine: unmemorized + memorized today (union)
    all_item_ids = sorted(unmemorized_item_ids | today_nm_item_ids)

    # Hide tab entirely if no items to display
    if not all_item_ids:
        return None

    # Pagination
    total_items = len(all_item_ids)
    if items_per_page and items_per_page > 0:
        total_pages = math.ceil(total_items / items_per_page)
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_item_ids = all_item_ids[start_idx:end_idx]
    else:
        paginated_item_ids = all_item_ids
        total_pages = 1

    # Get item details for paginated items
    items_data = [items[item_id] for item_id in paginated_item_ids]

    # Render rows with surah headers
    body_rows = []
    current_surah_id = None
    prev_page_id = None

    for item in items_data:
        # Add surah header when surah changes
        if item.surah_id != current_surah_id:
            current_surah_id = item.surah_id
            juz_number = get_juz_name(item_id=item.id)
            body_rows.append(render_surah_header(current_surah_id, juz_number))
            prev_page_id = None  # Reset consecutive tracking on surah change

        is_memorized_today = item.id in today_nm_item_ids
        body_rows.append(render_nm_row(item, current_date, is_memorized_today, prev_page_id))
        prev_page_id = item.page_id

    # Empty state
    if not body_rows:
        body_rows = [
            Tr(
                Td(
                    "All pages memorized!",
                    colspan=3,
                    cls="text-center text-gray-500 py-4",
                )
            )
        ]

    bulk_bar = render_nm_bulk_action_bar(current_date)

    # Pagination controls
    pagination_controls = None
    if items_per_page and total_pages > 1:
        pagination_controls = render_pagination_controls(mode_code, page, total_pages, total_items)

    table_content = [
        Table(
            Tbody(*body_rows, id=f"{mode_code}_tbody"),
            cls=(TableT.middle, TableT.divider, TableT.sm),
            hx_on__before_request="sessionStorage.setItem('scroll', window.scrollY)",
            hx_on__after_swap="window.scrollTo(0, sessionStorage.getItem('scroll'))",
        ),
    ]

    if pagination_controls:
        table_content.append(pagination_controls)

    table_content.append(bulk_bar)

    table = Div(
        *table_content,
        id=f"summary_table_{mode_code}",
        x_data="{ count: 0 }",
    )

    if table_only:
        return table
    return (mode_code, table)


# Rep mode configuration UI - used in profile and new memorization flows
REP_MODE_OPTIONS = [
    (DAILY_REPS_MODE_CODE, "☀️ Daily"),
    (WEEKLY_REPS_MODE_CODE, "📅 Weekly"),
    (FORTNIGHTLY_REPS_MODE_CODE, "📆 Fortnightly"),
    (MONTHLY_REPS_MODE_CODE, "🗓️ Monthly"),
]


def render_rep_config_form(
    form_id="rep-config-form",
    default_mode_code=DAILY_REPS_MODE_CODE,
    show_advanced=False,
    custom_thresholds=None,
):
    """
    Render a flexible rep configuration form for setting mode and repetition counts.

    Args:
        form_id: Form ID for HTMX targeting
        default_mode_code: Default selected mode
        show_advanced: Whether to show advanced config (all modes) by default
        custom_thresholds: Dict of mode_code -> threshold (existing values)

    Returns:
        Div containing the rep configuration form elements
    """
    custom_thresholds = custom_thresholds or {}

    def mode_option(code, label):
        return fh.Option(label, value=code, selected=code == default_mode_code)

    mode_select = fh.Select(
        *[mode_option(code, label) for code, label in REP_MODE_OPTIONS],
        name="mode_code",
        cls="select select-bordered select-sm w-full",
        x_model="selectedMode",
    )

    # Get default rep count for selected mode
    default_rep_count = custom_thresholds.get(
        default_mode_code, DEFAULT_REP_COUNTS.get(default_mode_code, 7)
    )

    simple_rep_input = Div(
        FormLabel("Repetitions", cls="text-sm"),
        fh.Input(
            type="number",
            name="rep_count",
            min="0",
            max="99",
            value=default_rep_count,
            cls="input input-bordered input-sm w-20",
            x_model="repCounts[selectedMode]",
        ),
        cls="flex items-center gap-2",
    )

    def advanced_rep_input(mode_code, label):
        threshold = custom_thresholds.get(mode_code, DEFAULT_REP_COUNTS.get(mode_code, 7))
        return Div(
            FormLabel(label, cls="text-sm w-24"),
            fh.Input(
                type="number",
                name=f"rep_count_{mode_code}",
                min="0",
                max="99",
                value=threshold,
                cls="input input-bordered input-sm w-20",
                x_model=f"repCounts['{mode_code}']",
            ),
            cls="flex items-center gap-2",
        )

    advanced_inputs = Div(
        *[advanced_rep_input(code, label) for code, label in REP_MODE_OPTIONS],
        cls="grid grid-cols-2 gap-2",
        x_show="advancedMode",
        x_cloak=True,
    )

    advanced_toggle = Div(
        FormLabel(
            fh.Input(
                type="checkbox",
                cls="checkbox checkbox-sm",
                x_model="advancedMode",
            ),
            Span("Advanced config (set all modes)", cls="text-sm ml-2"),
            cls="cursor-pointer",
        ),
        cls="mt-2",
    )

    # Alpine.js state initialization
    alpine_init = {
        "selectedMode": f"'{default_mode_code}'",
        "advancedMode": "true" if show_advanced else "false",
        "repCounts": str({
            code: custom_thresholds.get(code, DEFAULT_REP_COUNTS.get(code, 7))
            for code, _ in REP_MODE_OPTIONS
        }).replace("'", '"'),
    }
    alpine_data = "{ " + ", ".join(f"{k}: {v}" for k, v in alpine_init.items()) + " }"

    return Div(
        Div(
            Div(
                FormLabel("Starting Mode", cls="text-sm"),
                mode_select,
                cls="flex-1",
            ),
            Div(
                simple_rep_input,
                x_show="!advancedMode",
            ),
            cls="flex gap-4 items-end",
        ),
        advanced_toggle,
        advanced_inputs,
        id=form_id,
        x_data=alpine_data,
        cls="space-y-2 p-3 bg-base-200 rounded-lg",
    )


def render_mode_dropdown(hafiz_item_id, current_mode_code):
    """Render mode dropdown for inline mode changes."""
    def mode_option(code, label):
        return fh.Option(label, value=code, selected=code == current_mode_code)

    all_mode_options = [
        (DAILY_REPS_MODE_CODE, "☀️ Daily"),
        (WEEKLY_REPS_MODE_CODE, "📅 Weekly"),
        (FORTNIGHTLY_REPS_MODE_CODE, "📆 Fortnightly"),
        (MONTHLY_REPS_MODE_CODE, "🗓️ Monthly"),
        (FULL_CYCLE_MODE_CODE, "🔄 Full Cycle"),
        (SRS_MODE_CODE, "🧠 SRS"),
    ]

    return fh.Select(
        *[mode_option(code, label) for code, label in all_mode_options],
        name="mode_code",
        cls="select select-bordered select-xs",
        hx_post=f"/profile/quick_change_mode/{hafiz_item_id}",
        hx_trigger="change",
        hx_swap="none",
    )


def render_progress_cell(hafiz_item_id, current_count, threshold):
    """Render progress display with gear icon for threshold editing."""
    return Div(
        Span(f"{current_count} of {threshold}", cls="text-sm"),
        A(
            "⚙️",
            hx_get=f"/profile/configure_reps/{hafiz_item_id}",
            target_id="configure-modal-body",
            data_uk_toggle="target: #configure-modal",
            cls="cursor-pointer hover:opacity-70 ml-2",
            title="Edit thresholds",
        ),
        cls="flex items-center",
    )


def render_graduate_cell(hafiz_item_id, current_mode_code):
    """Render graduate checkbox with target mode dropdown."""
    from app.fixed_reps import REP_MODES_CONFIG

    all_mode_options = [
        (DAILY_REPS_MODE_CODE, "☀️ Daily"),
        (WEEKLY_REPS_MODE_CODE, "📅 Weekly"),
        (FORTNIGHTLY_REPS_MODE_CODE, "📆 Fortnightly"),
        (MONTHLY_REPS_MODE_CODE, "🗓️ Monthly"),
        (FULL_CYCLE_MODE_CODE, "🔄 Full Cycle"),
        (SRS_MODE_CODE, "🧠 SRS"),
    ]

    # Default to next mode in chain
    next_mode = REP_MODES_CONFIG.get(current_mode_code, {}).get("next_mode_code", FULL_CYCLE_MODE_CODE)

    graduate_options = [
        (code, label) for code, label in all_mode_options
        if code != current_mode_code
    ]

    graduate_select = fh.Select(
        *[fh.Option(label, value=code, selected=code == next_mode) for code, label in graduate_options],
        name="target_mode",
        cls="select select-bordered select-xs",
    )

    return Form(
        fh.Input(
            type="checkbox",
            name="confirm",
            cls="checkbox checkbox-xs checkbox-primary",
            hx_post=f"/profile/graduate_item/{hafiz_item_id}",
            hx_include="closest form",
            hx_swap="none",
        ),
        graduate_select,
        cls="flex items-center gap-2",
    )


# Legacy function - kept for compatibility but now just returns mode dropdown
def render_inline_mode_config(hafiz_item_id, current_mode_code, current_count, threshold):
    """Legacy - returns just the mode dropdown. Use individual render functions for new layout."""
    return render_mode_dropdown(hafiz_item_id, current_mode_code)


render_inline_mode_dropdown = render_inline_mode_config


def render_mode_and_reps(hafiz_item, mode_code=None):
    """
    Render mode icon and current rep count for display in tables.

    Args:
        hafiz_item: The hafiz_items record (dict or object)
        mode_code: Override mode code (optional)

    Returns:
        Span with mode icon and rep progress
    """
    if isinstance(hafiz_item, dict):
        item_mode_code = mode_code or hafiz_item.get("mode_code")
        item_id = hafiz_item.get("item_id")
    else:
        item_mode_code = mode_code or hafiz_item.mode_code
        item_id = hafiz_item.item_id

    if not item_mode_code or item_mode_code not in GRADUATABLE_MODES:
        icon = get_mode_icon(item_mode_code) if item_mode_code else ""
        return Span(f"{icon} {get_mode_name(item_mode_code) if item_mode_code else '-'}")

    # Get custom threshold or default
    threshold_columns = {
        DAILY_REPS_MODE_CODE: "custom_daily_threshold",
        WEEKLY_REPS_MODE_CODE: "custom_weekly_threshold",
        FORTNIGHTLY_REPS_MODE_CODE: "custom_fortnightly_threshold",
        MONTHLY_REPS_MODE_CODE: "custom_monthly_threshold",
    }
    column = threshold_columns.get(item_mode_code)

    if isinstance(hafiz_item, dict):
        custom_threshold = hafiz_item.get(column) if column else None
    else:
        custom_threshold = getattr(hafiz_item, column, None) if column else None

    threshold = custom_threshold if custom_threshold is not None else DEFAULT_REP_COUNTS.get(item_mode_code, 7)

    # Get current count
    current_count = get_mode_count(item_id, item_mode_code)
    icon = get_mode_icon(item_mode_code)
    mode_name = get_mode_name(item_mode_code)

    # Show mode name with progress: "☀️ Daily 3/7"
    return Span(f"{icon} {mode_name} {current_count}/{threshold}")


# === Status Helper Functions ===
# Status is derived from memorized + mode_code (no new column needed)


def get_status(hafiz_item) -> str:
    """Derive status from memorized flag and mode_code."""
    if isinstance(hafiz_item, dict):
        memorized = hafiz_item.get("memorized")
        mode_code = hafiz_item.get("mode_code")
    else:
        memorized = hafiz_item.memorized
        mode_code = hafiz_item.mode_code

    if not memorized:
        return STATUS_NOT_MEMORIZED

    if mode_code == NEW_MEMORIZATION_MODE_CODE:
        return STATUS_LEARNING
    elif mode_code in (
        DAILY_REPS_MODE_CODE,
        WEEKLY_REPS_MODE_CODE,
        FORTNIGHTLY_REPS_MODE_CODE,
        MONTHLY_REPS_MODE_CODE,
    ):
        return STATUS_REPS
    elif mode_code == FULL_CYCLE_MODE_CODE:
        return STATUS_SOLID
    elif mode_code == SRS_MODE_CODE:
        return STATUS_STRUGGLING

    return STATUS_NOT_MEMORIZED


def get_status_display(status: str) -> tuple[str, str]:
    """Get (icon, label) for a status."""
    return STATUS_DISPLAY.get(status, ("❓", "Unknown"))


def get_status_counts(hafiz_id: int) -> dict:
    """Get page count for each status for dashboard stats."""
    all_items = hafizs_items(where=f"hafiz_id = {hafiz_id}")

    # Group item_ids by status
    groups = {
        STATUS_NOT_MEMORIZED: [],
        STATUS_LEARNING: [],
        STATUS_REPS: [],
        STATUS_SOLID: [],
        STATUS_STRUGGLING: [],
    }

    for hi in all_items:
        status = get_status(hi)
        if status in groups:
            groups[status].append(hi.item_id)

    # Calculate page count for each group
    return {
        STATUS_NOT_MEMORIZED: get_page_count(item_ids=groups[STATUS_NOT_MEMORIZED]),
        STATUS_LEARNING: get_page_count(item_ids=groups[STATUS_LEARNING]),
        STATUS_REPS: get_page_count(item_ids=groups[STATUS_REPS]),
        STATUS_SOLID: get_page_count(item_ids=groups[STATUS_SOLID]),
        STATUS_STRUGGLING: get_page_count(item_ids=groups[STATUS_STRUGGLING]),
        "total": get_page_count(item_ids=[hi.item_id for hi in all_items]),
    }
