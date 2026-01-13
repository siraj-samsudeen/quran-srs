from fasthtml.common import *
import fasthtml.common as fh
from monsterui.all import *
from database import hafizs, modes
from constants import (
    RATING_MAP, 
    REP_MODE_OPTIONS, 
    DEFAULT_REP_COUNTS,
    NEW_MEMORIZATION_MODE_CODE,
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
    SRS_MODE_CODE,
    GRADUATABLE_MODES
)
from app.common_model import get_mode_count, get_mode_name, get_mode_icon, get_surah_name, get_page_number

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
        f"{hafizs[auth].name if auth is not None else 'Select hafiz'}",
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

def get_page_description(
    item_id,
    link: str = None,
    is_link: bool = True,
    is_bold: bool = True,
    custom_text="",
):
    from database import items # Lazy import to avoid circular dependency if any
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
    from collections import defaultdict
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
            cls=f"{'inline-block' if direction == 'horizontal' else None}",
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

def create_count_link(count: int, rev_ids: str):
    if not rev_ids:
        return count
    return A(
        count,
        href=f"/revision/bulk_edit?ids={rev_ids}",
        cls=AT.classic,
    )

def render_rep_config_form(
    form_id="rep-config-form",
    default_mode_code=DAILY_REPS_MODE_CODE,
    show_advanced=False,
    custom_thresholds=None,
):
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

def render_inline_mode_config(hafiz_item_id, current_mode_code, current_count, threshold):
    """Legacy - returns just the mode dropdown. Use individual render functions for new layout."""
    return render_mode_dropdown(hafiz_item_id, current_mode_code)

render_inline_mode_dropdown = render_inline_mode_config

def render_mode_and_reps(hafiz_item, mode_code=None):
    if isinstance(hafiz_item, dict):
        item_mode_code = mode_code or hafiz_item.get("mode_code")
        item_id = hafiz_item.get("item_id")
        hafiz_id = hafiz_item.get("hafiz_id")
    else:
        item_mode_code = mode_code or hafiz_item.mode_code
        item_id = hafiz_item.item_id
        hafiz_id = hafiz_item.hafiz_id

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
    current_count = get_mode_count(item_id, item_mode_code, hafiz_id)
    icon = get_mode_icon(item_mode_code)
    mode_name = get_mode_name(item_mode_code)

    # Show mode name with progress: "☀️ Daily 3/7"
    return Span(f"{icon} {mode_name} {current_count}/{threshold}")
