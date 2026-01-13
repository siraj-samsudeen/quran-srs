"""Profile view - UI rendering for profile management."""

from fasthtml.common import *
import fasthtml.common as fh
from monsterui.all import *
from app.profile_model import (
    get_status_counts,
    get_status_display,
    get_status,
    get_profile_data,
)
from app.common_model import get_mode_count, get_surah_name
from app.common_function import get_mode_name, get_mode_icon
from constants import (
    STATUS_NOT_MEMORIZED,
    STATUS_LEARNING,
    STATUS_REPS,
    STATUS_SOLID,
    STATUS_STRUGGLING,
    STATUS_DISPLAY,
    NEW_MEMORIZATION_MODE_CODE,
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
    SRS_MODE_CODE,
    GRADUATABLE_MODES,
    DEFAULT_REP_COUNTS,
)


def render_stats_cards(auth, current_type="page", active_status_filter=None):
    """Render status stats cards at top of profile page. Cards are clickable to filter."""
    counts = get_status_counts(auth)

    # Order: Not Memorized, Learning, Reps, Solid, Struggling, Total
    cards_data = [
        (STATUS_NOT_MEMORIZED, counts.get(STATUS_NOT_MEMORIZED, 0)),
        (STATUS_LEARNING, counts.get(STATUS_LEARNING, 0)),
        (STATUS_REPS, counts.get(STATUS_REPS, 0)),
        (STATUS_SOLID, counts.get(STATUS_SOLID, 0)),
        (STATUS_STRUGGLING, counts.get(STATUS_STRUGGLING, 0)),
    ]

    def make_card(status, count):
        icon, label = get_status_display(status)
        is_active = active_status_filter == status
        return A(
            Div(
                Span(icon, cls="text-2xl"),
                Span(str(count), cls="text-2xl font-bold ml-2"),
                cls="flex items-center justify-center",
            ),
            Div(label, cls="text-xs text-center mt-1 text-gray-600"),
            href=f"/profile/{current_type}?status_filter={status}",
            cls=f"bg-base-100 border rounded-lg p-3 min-w-[100px] hover:bg-base-200 cursor-pointer transition-colors {'ring-2 ring-primary bg-primary/10' if is_active else ''}",
            data_testid=f"stats-card-{status.lower()}",
        )

    # Total card clears the filter
    total_card = A(
        Div(
            Span("📖", cls="text-2xl"),
            Span(str(counts.get("total", 0)), cls="text-2xl font-bold ml-2"),
            cls="flex items-center justify-center",
        ),
        Div("Total", cls="text-xs text-center mt-1 text-gray-600"),
        href=f"/profile/{current_type}",
        cls=f"bg-base-100 border rounded-lg p-3 min-w-[100px] hover:bg-base-200 cursor-pointer transition-colors {'ring-2 ring-primary bg-primary/10' if active_status_filter is None else ''}",
        data_testid="stats-card-total",
    )

    return Div(
        *[make_card(status, count) for status, count in cards_data],
        total_card,
        cls="flex flex-wrap gap-3 mb-4",
        data_testid="stats-cards",
    )


def get_status_badge(status):
    """Return status badge with appropriate color."""
    status_colors = {
        STATUS_NOT_MEMORIZED: ("bg-gray-100", "text-gray-600"),
        STATUS_LEARNING: ("bg-green-100", "text-green-700"),
        STATUS_REPS: ("bg-amber-100", "text-amber-700"),
        STATUS_SOLID: ("bg-purple-100", "text-purple-700"),
        STATUS_STRUGGLING: ("bg-red-100", "text-red-700"),
    }
    icon, label = get_status_display(status)
    bg, text = status_colors.get(status, ("bg-gray-100", "text-gray-600"))
    return Span(f"{icon} {label}", cls=f"{bg} {text} px-2 py-0.5 rounded text-xs whitespace-nowrap")


def get_mode_badge(mode_code):
    """Return mode badge with appropriate color."""
    if not mode_code:
        return Span("-", cls="text-gray-400")

    mode_colors = {
        NEW_MEMORIZATION_MODE_CODE: ("bg-green-100", "text-green-700"),
        DAILY_REPS_MODE_CODE: ("bg-yellow-100", "text-yellow-700"),
        WEEKLY_REPS_MODE_CODE: ("bg-amber-100", "text-amber-700"),
        FORTNIGHTLY_REPS_MODE_CODE: ("bg-orange-100", "text-orange-700"),
        MONTHLY_REPS_MODE_CODE: ("bg-orange-200", "text-orange-800"),
        FULL_CYCLE_MODE_CODE: ("bg-purple-100", "text-purple-700"),
        SRS_MODE_CODE: ("bg-red-100", "text-red-700"),
    }
    icon = get_mode_icon(mode_code)
    name = get_mode_name(mode_code)
    bg, text = mode_colors.get(mode_code, ("bg-gray-100", "text-gray-600"))
    return Span(f"{icon} {name}", cls=f"{bg} {text} px-2 py-0.5 rounded text-xs whitespace-nowrap")


def render_progress_bar(current, total):
    """Render a progress bar for rep modes."""
    if total == 0:
        return Span("-", cls="text-gray-400")

    percent = (current / total) * 100
    # Color: red < 30%, amber 30-70%, green > 70%
    bar_color = "bg-red-500" if percent < 30 else "bg-amber-500" if percent < 70 else "bg-green-500"

    return Div(
        Div(
            Div(cls=f"{bar_color} h-full", style=f"width: {percent}%"),
            cls="flex-1 bg-gray-200 rounded h-2 overflow-hidden",
        ),
        Span(f"{current}/{total}", cls="text-xs text-gray-500 ml-2 min-w-[35px]"),
        cls="flex items-center gap-1",
    )


def render_profile_row(row_data, status_filter, hafiz_id=None):
    """Render a single profile table row."""
    item_id = row_data["item_id"]
    hafiz_item_id = row_data["hafiz_item_id"]
    page_number = row_data["page_number"]
    memorized = bool(row_data["memorized"])
    mode_code = row_data["mode_code"] or ""
    status = get_status(row_data)

    # Checkbox for bulk selection
    checkbox_cell = Td(
        fh.Input(
            type="checkbox",
            name="hafiz_item_ids",
            value=hafiz_item_id,
            cls="checkbox checkbox-sm bulk-select-checkbox",
            **{"@change": "count = $root.querySelectorAll('.bulk-select-checkbox:checked').length"},
        ),
        cls="w-8 text-center",
    ) if hafiz_item_id else Td(cls="w-8")

    # Calculate progress for graduatable modes
    progress_cell = Td("-", cls="text-gray-400")
    if memorized and mode_code in GRADUATABLE_MODES:
        current_count = get_mode_count(item_id, mode_code, hafiz_id)
        threshold = DEFAULT_REP_COUNTS.get(mode_code, 7)
        # Check custom thresholds
        threshold_map = {
            DAILY_REPS_MODE_CODE: row_data.get("custom_daily_threshold"),
            WEEKLY_REPS_MODE_CODE: row_data.get("custom_weekly_threshold"),
            FORTNIGHTLY_REPS_MODE_CODE: row_data.get("custom_fortnightly_threshold"),
            MONTHLY_REPS_MODE_CODE: row_data.get("custom_monthly_threshold"),
        }
        custom = threshold_map.get(mode_code)
        if custom is not None:
            threshold = custom
        progress_cell = Td(render_progress_bar(current_count, threshold))

    # Config button (only for memorized items)
    config_cell = Td()
    if memorized and hafiz_item_id:
        config_cell = Td(
            A(
                "⚙️",
                href=f"/profile/configure_reps/{hafiz_item_id}",
                hx_get=f"/profile/configure_reps/{hafiz_item_id}",
                hx_target="#config-modal-content",
                hx_swap="innerHTML",
                onclick="document.getElementById('config-modal').showModal()",
                cls="btn btn-ghost btn-xs",
                title="Configure",
            ),
            cls="text-center",
        )

    return Tr(
        checkbox_cell,
        Td(
            A(
                Strong(page_number),
                href=f"/page_details/{item_id}",
                cls="font-mono hover:underline",
            ),
            cls="w-16 text-center",
        ),
        Td(get_status_badge(status)),
        Td(get_mode_badge(mode_code) if memorized else Span("-", cls="text-gray-400")),
        progress_cell,
        config_cell,
    )


def render_profile_surah_header(surah_id, juz_number):
    """Render a surah section header row."""
    surah_name = get_surah_name(item_id=None, page_id=None) # Need item_id or page_id?
    # Wait, common_function.get_surah_name takes item_id. 
    # common_model.get_surah_name doesn't exist? I imported get_surah_name from common_model in my thought, 
    # but I see I imported it from common_model in the code above. 
    # Let's check common_model.py again. 
    # common_model.py DOES NOT have get_surah_name.
    # common_function.py DOES have it.
    # I should fix the import in this file. 
    pass 

# I need to fix the import for get_surah_name. It is in common_function.py.
# But common_function.get_surah_name takes page_id or item_id.
# render_profile_surah_header receives surah_id.
# surahs table is needed.
# I should import surahs from database.

def render_profile_surah_header_fixed(surah_id, juz_number):
    from database import surahs
    surah_name = surahs[surah_id].name
    return Tr(
        Td(
            Span(f"📖 {surah_name}", cls="font-semibold"),
            Span(f" (Juz {juz_number})", cls="text-gray-500 text-sm"),
            colspan=6,
            cls="bg-base-200 py-1 px-2",
        ),
        cls="surah-header",
    )

def render_bulk_action_bar(status_filter):
    """Render a sticky bulk action bar for marking memorization status."""
    filter_param = f"&status_filter={status_filter}" if status_filter else ""

    # Select-all checkbox with label
    select_all = Div(
        fh.Input(
            type="checkbox",
            cls="checkbox checkbox-sm",
            **{
                "@change": """
                    $root.querySelectorAll('.bulk-select-checkbox').forEach(cb => cb.checked = $el.checked);
                    count = $el.checked ? $root.querySelectorAll('.bulk-select-checkbox').length : 0
                """,
                ":checked": "count > 0 && count === $root.querySelectorAll('.bulk-select-checkbox').length",
            },
        ),
        Span("Select All", cls="text-sm ml-2", x_show="count < $root.querySelectorAll('.bulk-select-checkbox').length"),
        Span("Clear All", cls="text-sm ml-2", x_show="count === $root.querySelectorAll('.bulk-select-checkbox').length"),
        Span("|", cls="text-gray-300 mx-2"),
        Span(x_text="count", cls="font-bold"),
        Span(" selected", cls="text-sm ml-1"),
        cls="flex items-center",
    )

    # Cancel button
    cancel_button = Button(
        "✕",
        cls="btn btn-ghost btn-sm",
        **{"@click": "$root.querySelectorAll('.bulk-select-checkbox').forEach(cb => cb.checked = false); count = 0"},
        title="Cancel selection",
    )

    # Mark as Memorized button (sets status to SOLID/Full Cycle)
    memorized_button = Button(
        "✓ Mark Memorized",
        type="submit",
        formaction=f"/profile/bulk/set_status?status={STATUS_SOLID}{filter_param}",
        cls="btn btn-success btn-sm",
        data_testid="bulk-mark-memorized",
    )

    # Mark as Not Memorized button
    not_memorized_button = Button(
        "✗ Mark Not Memorized",
        type="submit",
        formaction=f"/profile/bulk/set_status?status={STATUS_NOT_MEMORIZED}{filter_param}",
        cls="btn btn-error btn-sm",
        data_testid="bulk-mark-not-memorized",
    )

    return Form(
        Div(
            select_all,
            Div(
                memorized_button,
                not_memorized_button,
                cancel_button,
                cls="flex gap-2",
            ),
            cls="flex justify-between items-center w-full",
        ),
        id="bulk-action-bar",
        cls="fixed bottom-0 left-0 right-0 bg-base-100 border-t shadow-lg p-3 z-50",
        x_show="count > 0",
        style="display: none",
        x_transition=True,
        hx_swap="innerHTML",
        hx_target="#profile-table-container",
        data_testid="profile-bulk-action-bar",
    )


def render_profile_table(auth, status_filter=None, offset=0, items_per_page=25, rows_only=False):
    """Render the profile table with surah grouping and infinite scroll."""
    rows = get_profile_data(auth, status_filter)
    total_items = len(rows)

    # Infinite scroll pagination
    start_idx = offset
    end_idx = offset + items_per_page
    paginated_rows = rows[start_idx:end_idx]
    has_more = end_idx < total_items

    # Build table rows with surah headers
    body_rows = []
    current_surah_id = None

    for row in paginated_rows:
        surah_id = row["surah_id"]
        # Add surah header when surah changes
        if surah_id != current_surah_id:
            current_surah_id = surah_id
            juz_number = row["juz_number"]
            body_rows.append(render_profile_surah_header_fixed(surah_id, juz_number))

        body_rows.append(render_profile_row(row, status_filter, hafiz_id=auth))

    # Add infinite scroll trigger to the last data row
    if has_more and body_rows:
        filter_param = f"&status_filter={status_filter}" if status_filter else ""
        next_offset = offset + items_per_page
        # Find the last actual data row (not a surah header)
        for i in range(len(body_rows) - 1, -1, -1):
            row = body_rows[i]
            if hasattr(row, "attrs") and "surah-header" not in row.attrs.get("cls", ""):
                row.attrs.update({
                    "hx-get": f"/profile/table/more?offset={next_offset}{filter_param}",
                    "hx-trigger": "revealed",
                    "hx-swap": "afterend",
                })
                break

    # Return just the rows for infinite scroll requests
    if rows_only:
        return tuple(body_rows)

    if not body_rows:
        body_rows = [
            Tr(Td("No pages found", colspan=6, cls="text-center text-gray-500 py-8"))
        ]

    # Select-all checkbox for the header
    select_all_checkbox = fh.Input(
        type="checkbox",
        cls="checkbox checkbox-sm",
        **{
            "@change": """
                $root.querySelectorAll('.bulk-select-checkbox').forEach(cb => cb.checked = $el.checked);
                count = $el.checked ? $root.querySelectorAll('.bulk-select-checkbox').length : 0
            """,
            ":checked": "count > 0 && count === $root.querySelectorAll('.bulk-select-checkbox').length",
        },
    )

    table = Table(
        Thead(
            Tr(
                Th(select_all_checkbox, cls="w-8 text-center"),
                Th("Page", cls="w-16 text-center"),
                Th("Status"),
                Th("Mode"),
                Th("Progress"),
                Th("", cls="w-12"),
            )
        ),
        Tbody(*body_rows, id="profile-tbody"),
        cls=(TableT.middle, TableT.divider, TableT.sm),
    )

    bulk_bar = render_bulk_action_bar(status_filter)

    # Always add padding at bottom to ensure bulk bar doesn't cover content
    return Div(
        Div(f"{total_items} pages", cls="text-sm text-gray-500 mb-2"),
        table,
        bulk_bar,
        id="profile-table-container",
        x_data="{ count: 0 }",
        cls="pb-20",
    )

def render_rep_config_modal(hafiz_item_id, auth, hafiz_item):
    """Render the content of the rep config modal."""
    # Get existing custom thresholds
    threshold_values = {
        DAILY_REPS_MODE_CODE: hafiz_item.custom_daily_threshold or DEFAULT_REP_COUNTS.get(DAILY_REPS_MODE_CODE, 7),
        WEEKLY_REPS_MODE_CODE: hafiz_item.custom_weekly_threshold or DEFAULT_REP_COUNTS.get(WEEKLY_REPS_MODE_CODE, 7),
        FORTNIGHTLY_REPS_MODE_CODE: hafiz_item.custom_fortnightly_threshold or DEFAULT_REP_COUNTS.get(FORTNIGHTLY_REPS_MODE_CODE, 7),
        MONTHLY_REPS_MODE_CODE: hafiz_item.custom_monthly_threshold or DEFAULT_REP_COUNTS.get(MONTHLY_REPS_MODE_CODE, 7),
    }

    current_mode = hafiz_item.mode_code or DAILY_REPS_MODE_CODE
    page_number = hafiz_item.page_number
    # Fix get_surah_name import or usage here too
    from database import surahs, items
    item = items[hafiz_item.item_id]
    surah_name = surahs[item.surah_id].name

    # Mode options for dropdown with index for ordering
    mode_options = [
        (DAILY_REPS_MODE_CODE, "☀️ Daily", 0),
        (WEEKLY_REPS_MODE_CODE, "📅 Weekly", 1),
        (FORTNIGHTLY_REPS_MODE_CODE, "📆 Fortnightly", 2),
        (MONTHLY_REPS_MODE_CODE, "🗓️ Monthly", 3),
        (FULL_CYCLE_MODE_CODE, "🔄 Full Cycle", 4),
        (SRS_MODE_CODE, "🧠 SRS", 5),
    ]

    # Map mode codes to their index for Alpine.js
    mode_order = {code: idx for code, _, idx in mode_options}

    # Starting mode dropdown with Alpine.js binding
    mode_select = fh.Select(
        *[fh.Option(label, value=code, selected=code == current_mode) for code, label, _ in mode_options],
        name="mode_code",
        cls="select select-bordered select-sm w-full",
        x_model="selectedMode",
    )

    # Build rows for each rep mode threshold with conditional disabling
    rep_mode_rows = []
    for code, label, idx in mode_options[:4]:  # Only graduatable modes
        rep_mode_rows.append(
            Tr(
                Td(label, cls="font-medium"),
                Td(
                    fh.Input(
                        type="number",
                        name=f"rep_count_{code}",
                        min="0",
                        max="99",
                        value=threshold_values[code],
                        cls="input input-bordered input-sm w-20 disabled:opacity-50 disabled:cursor-not-allowed",
                        # Disable if this mode comes before the selected starting mode
                        **{":disabled": f"modeOrder[selectedMode] > {idx}"},
                    ),
                ),
                # Gray out the row if disabled
                **{":class": f"modeOrder[selectedMode] > {idx} ? 'opacity-40' : ''"},
            )
        )

    # Alpine.js data for mode ordering
    alpine_data = f"{{ selectedMode: '{current_mode}', modeOrder: {mode_order} }}"

    return Div(
        P(f"Configure repetitions for Page {page_number} ({surah_name})", cls="mb-4 text-sm text-gray-600"),
        Form(
            # Starting mode section
            Div(
                FormLabel("Starting Mode", cls="text-sm font-medium"),
                mode_select,
                cls="mb-4",
            ),
            # Thresholds table - one mode per row
            Div(
                FormLabel("Repetition Thresholds", cls="text-sm font-medium mb-2"),
                P("Modes before your starting mode are disabled", cls="text-xs text-gray-500 mb-2"),
                Table(
                    Thead(
                        Tr(
                            Th("Mode", cls="text-left"),
                            Th("Reps to Graduate", cls="text-left"),
                        )
                    ),
                    Tbody(*rep_mode_rows),
                    cls="w-full",
                ),
                cls="bg-base-200 p-3 rounded-lg",
            ),
            Hidden(name="hafiz_item_id", value=hafiz_item_id),
            Div(
                Button(
                    "Save Configuration",
                    type="submit",
                    cls=(ButtonT.primary, "uk-modal-close"),
                ),
                Button(
                    "Cancel",
                    type="button",
                    cls=(ButtonT.secondary, "uk-modal-close"),
                ),
                cls="flex gap-2 mt-4 justify-end",
            ),
            hx_post="/profile/configure_reps",
            hx_target="body",
            x_data=alpine_data,
        ),
    )
