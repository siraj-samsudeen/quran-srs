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
        "←",
        hx_get=f"/page/{mode_code}?page={prev_page}",
        hx_target=f"#summary_table_{mode_code}",
        hx_swap="outerHTML",
        cls=(ButtonT.secondary, "px-4 py-2"),
        data_testid=f"pagination-prev-{mode_code}",
    ) if not is_first_page else Span()

    next_button = Button(
        "→",
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
# Named predicates for filtering items per mode, extracted for testability


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


def should_include_in_weekly_reps(item: dict, current_date: str) -> bool:
    """Predicate for Weekly Reps mode: must be in WR mode AND (due OR reviewed today with history)."""
    if item["mode_code"] != WEEKLY_REPS_MODE_CODE:
        return False
    return _is_review_due(item, current_date) or (
        _is_reviewed_today(item, current_date) and _has_revisions_in_mode(item)
    )


def should_include_in_srs(item: dict, current_date: str) -> bool:
    """Predicate for SRS mode: due for review OR has revisions today."""
    return _is_review_due(item, current_date) or _has_revisions_today_in_mode(
        item, current_date
    )


def should_include_in_full_cycle(item: dict, current_date: str) -> bool:
    """Predicate for Full Cycle mode: item must be memorized."""
    return _has_memorized(item)


# Mode to predicate mapping
MODE_PREDICATES = {
    DAILY_REPS_MODE_CODE: should_include_in_daily_reps,
    WEEKLY_REPS_MODE_CODE: should_include_in_weekly_reps,
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
        Span(date_to_human_readable(current_date), cls=TextPresets.bold_lg, data_testid="system-date"),
    )
