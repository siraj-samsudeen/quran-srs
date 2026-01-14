"""Profile view - UI rendering for profile management."""

from fasthtml.common import *
import fasthtml.common as fh
from monsterui.all import *
from app.profile_model import (
    get_status_counts,
    get_status,
    get_profile_data,
    get_tab_counts,
)
from app.common_model import get_mode_count
from constants import (
    STATUS_NOT_MEMORIZED,
    STATUS_SOLID,
    GRADUATABLE_MODES,
    DEFAULT_REP_COUNTS,
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
)

from app.components.layout import StatsCards, BulkActionBar, TabFilter
from app.components.display import StatusBadge, ModeBadge
from app.components.tables import ProgressCell, SurahHeader, JuzHeader
from app.components.forms import BulkSelectCheckbox, SelectAllCheckbox, RepConfigForm

def render_stats_cards(auth, current_type="page", active_status_filter=None):
    """Render status stats cards at top of profile page."""
    return StatsCards(auth, current_type, active_status_filter)


def render_tab_filter(auth, status_filter=None, hx_swap_oob=False):
    """Render tab filter for All/Memorized/Unmemorized.
    
    Args:
        auth: hafiz_id
        status_filter: current filter value
        hx_swap_oob: if True, add hx-swap-oob for out-of-band update
    """
    tab_counts = get_tab_counts(auth)
    active_tab = status_filter if status_filter in ("memorized", "unmemorized") else "all"
    tabs = TabFilter(tab_counts, active_tab)
    if hx_swap_oob:
        tabs.attrs["hx-swap-oob"] = "true"
    return tabs


def render_profile_row(row_data, status_filter, hafiz_id=None):
    """Render a single profile table row."""
    item_id = row_data["item_id"]
    hafiz_item_id = row_data["hafiz_item_id"]
    page_number = row_data["page_number"]
    juz_number = row_data["juz_number"]
    surah_id = row_data["surah_id"]
    memorized = bool(row_data["memorized"])
    mode_code = row_data["mode_code"] or ""
    status = get_status(row_data)

    # Checkbox for bulk selection
    if hafiz_item_id:
        checkbox_cell = Td(
            BulkSelectCheckbox(hafiz_item_id, name="hafiz_item_ids", cls="checkbox-sm", **{
                "data-juz": str(juz_number),
                "data-surah": str(surah_id),
            }),
            cls="w-8 text-center",
        )
    else:
        checkbox_cell = Td(cls="w-8")

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
        progress_cell = Td(ProgressCell(current_count, threshold))

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
        Td(StatusBadge(status)),
        Td(ModeBadge(mode_code) if memorized else Span("-", cls="text-gray-400")),
        progress_cell,
        config_cell,
        **{
            "data-juz": str(juz_number),
            "data-surah": str(surah_id),
        },
    )


def render_bulk_action_bar(status_filter):
    """Render a sticky bulk action bar for marking memorization status."""
    filter_param = f"&status_filter={status_filter}" if status_filter else ""

    # Select-all checkbox with label
    select_all = Div(
        SelectAllCheckbox(cls="checkbox checkbox-sm"),
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
        type="button",
        hx_post=f"/profile/bulk/set_status?status={STATUS_SOLID}{filter_param}",
        hx_target="#profile-table-container",
        hx_swap="innerHTML",
        hx_include="[name='hafiz_item_ids']",
        cls="btn btn-success btn-sm",
        data_testid="bulk-mark-memorized",
    )

    # Mark as Not Memorized button
    not_memorized_button = Button(
        "✗ Mark Not Memorized",
        type="button",
        hx_post=f"/profile/bulk/set_status?status={STATUS_NOT_MEMORIZED}{filter_param}",
        hx_target="#profile-table-container",
        hx_swap="innerHTML",
        hx_include="[name='hafiz_item_ids']",
        cls="btn btn-error btn-sm",
        data_testid="bulk-mark-not-memorized",
    )

    return BulkActionBar(
        children=[
            select_all,
            Div(
                memorized_button,
                not_memorized_button,
                cancel_button,
                cls="flex gap-2",
            ),
        ],
        cls="w-full",
        id="bulk-action-bar",
        data_testid="profile-bulk-action-bar",
    )


def render_profile_table(auth, status_filter=None, offset=0, items_per_page=25, rows_only=False):
    """Render the profile table with surah grouping and infinite scroll."""
    rows = get_profile_data(auth, status_filter)
    # Convert item count to page count for display
    from app.common_model import get_page_count
    item_ids = [row["item_id"] for row in rows]
    total_pages = get_page_count(item_ids=item_ids)
    total_items = len(rows)

    # Infinite scroll pagination
    start_idx = offset
    end_idx = offset + items_per_page
    paginated_rows = rows[start_idx:end_idx]
    has_more = end_idx < total_items

    # Build table rows with juz and surah headers
    body_rows = []
    current_juz_number = None
    current_surah_id = None

    for row in paginated_rows:
        juz_number = row["juz_number"]
        surah_id = row["surah_id"]
        
        # Add juz header when juz changes
        if juz_number != current_juz_number:
            current_juz_number = juz_number
            body_rows.append(JuzHeader(juz_number, colspan=6))
            current_surah_id = None  # Reset surah when juz changes
        
        # Add surah header when surah changes
        if surah_id != current_surah_id:
            current_surah_id = surah_id
            body_rows.append(SurahHeader(surah_id, juz_number, colspan=6))

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
    select_all_checkbox = SelectAllCheckbox(cls="checkbox checkbox-sm")

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
    # Wrap table and bulk bar in a Form so checkboxes are submitted with the buttons
    return Form(
        Div(f"{total_pages} pages", cls="text-sm text-gray-500 mb-2"),
        table,
        bulk_bar,
        id="profile-table-container",
        x_data="{ count: 0 }",
        cls="pb-20",
        method="post",
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
    
    # We need surah name.
    # In the original profile_view.py, it was trying to import get_surah_name from database?
    # Actually it imported items and surahs.
    from database import items, surahs
    item = items[hafiz_item.item_id]
    surah_name = surahs[item.surah_id].name

    form_content = RepConfigForm(
        default_mode_code=current_mode,
        custom_thresholds=threshold_values,
        show_advanced=False
    )

    return Div(
        P(f"Configure repetitions for Page {page_number} ({surah_name})", cls="mb-4 text-sm text-gray-600"),
        Form(
            form_content,
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
        ),
    )