"""
Common View Module

UI components and rendering functions.
No business logic - only presentation.
"""

from fasthtml.common import *
import fasthtml.common as fh
from monsterui.all import *
from .globals import items, revisions, RATING_MAP
from .hafiz_model import hafizs
from .common_model import (
    get_surah_name,
    get_current_date,
    get_current_plan_id,
    get_mode_condition,
)
from .utils import date_to_human_readable, get_page_number


def main_area(*args, active=None, hafiz_id=None):
    """Render main application layout with navbar."""
    is_active = lambda x: AT.primary if x == active else None
    title = A("Quran SRS", href="/")
    hafiz_name = A(
        f"{hafizs[hafiz_id].name if hafiz_id is not None else "Select hafiz"}",
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


def get_page_description(
    item_id,
    link: str = None,
    is_link: bool = True,
    is_bold: bool = True,
    custom_text="",
):
    """Render page description with optional link."""
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


def render_rating(rating: int):
    """Render rating as human-readable text."""
    return RATING_MAP.get(str(rating))


def rating_dropdown(
    rating="None",
    name="rating",
    cls="",
    **kwargs,
):
    """Render rating dropdown select component."""
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
    """Render rating radio button group."""
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


def row_background_color(rating):
    """Return CSS class for row background based on rating."""
    if rating is None:
        return
    if rating == 1:  # Good
        bg_color = "bg-green-100"
    elif rating == 0:  # Ok
        bg_color = "bg-yellow-50"
    elif rating == -1:  # Bad
        bg_color = "bg-red-50"
    return bg_color


def create_count_link(count: int, rev_ids: str):
    """Render count as clickable link to bulk edit."""
    if not rev_ids:
        return count
    return A(
        count,
        href=f"/revision/bulk_edit?ids={rev_ids}",
        cls=AT.classic,
    )


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


def render_summary_table(hafiz_id: int, mode_code, item_ids, is_plan_finished):
    """Render the summary table for a mode with item rows."""
    current_date = get_current_date(hafiz_id)
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


def render_current_date(hafiz_id: int):
    """Render the current system date display."""
    current_date = get_current_date(hafiz_id)
    return P(
        Span("System Date: ", cls=TextPresets.bold_lg),
        Span(date_to_human_readable(current_date), data_testid="system-date"),
    )
