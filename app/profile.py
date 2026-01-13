from fasthtml.common import *
from monsterui.all import *
from utils import *
from app.common_function import *
from app.fixed_reps import REP_MODES_CONFIG, MODE_TO_THRESHOLD_COLUMN
from database import *

profile_app, rt = create_app_with_auth()


# === Stats Cards Component ===


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


# === Bulk Status Update ===


def _apply_status_to_item(hafiz_item, status, current_date):
    """Apply status changes to a hafiz_item. Returns True if applied."""
    if status == STATUS_NOT_MEMORIZED:
        hafiz_item.memorized = False
        hafiz_item.mode_code = None
        hafiz_item.next_review = None
        hafiz_item.next_interval = None
    elif status == STATUS_LEARNING:
        hafiz_item.memorized = True
        hafiz_item.mode_code = NEW_MEMORIZATION_MODE_CODE
        hafiz_item.next_review = None
        hafiz_item.next_interval = None
    elif status == STATUS_REPS:
        hafiz_item.memorized = True
        hafiz_item.mode_code = DAILY_REPS_MODE_CODE
        config = REP_MODES_CONFIG[DAILY_REPS_MODE_CODE]
        hafiz_item.next_interval = config["interval"]
        hafiz_item.next_review = add_days_to_date(current_date, config["interval"])
    elif status == STATUS_SOLID:
        hafiz_item.memorized = True
        hafiz_item.mode_code = FULL_CYCLE_MODE_CODE
        hafiz_item.next_review = None
        hafiz_item.next_interval = None
    elif status == STATUS_STRUGGLING:
        hafiz_item.memorized = True
        hafiz_item.mode_code = SRS_MODE_CODE
        hafiz_item.next_review = None
        hafiz_item.next_interval = None
    else:
        return False
    return True


@profile_app.post("/bulk/set_status")
async def bulk_set_status(req: Request, auth, sess, status: str, status_filter: str = None):
    """Bulk set status for selected items via HTMX form submission."""
    form_data = await req.form()
    item_ids = [int(id) for id in form_data.getlist("hafiz_item_ids") if id]

    if not item_ids:
        error_toast(sess, "No items selected")
        return _render_profile_table(auth, status_filter)

    current_date = get_current_date(auth)
    updated = 0

    for hafiz_item_id in item_ids:
        try:
            hafiz_item = hafizs_items[hafiz_item_id]
            if hafiz_item.hafiz_id != auth:
                continue

            if _apply_status_to_item(hafiz_item, status, current_date):
                hafizs_items.update(hafiz_item)
                updated += 1
        except (NotFoundError, ValueError):
            continue

    if updated > 0:
        _, status_label = get_status_display(status)
        success_toast(sess, f"Marked {updated} page(s) as {status_label}")
    else:
        error_toast(sess, "No pages were updated")

    return _render_profile_table(auth, status_filter)


# === Profile Table Row Rendering ===


def _get_status_badge(status):
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


def _get_mode_badge(mode_code):
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


def _render_progress_bar(current, total):
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


def _render_profile_row(row_data, status_filter, hafiz_id=None):
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
        progress_cell = Td(_render_progress_bar(current_count, threshold))

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
        Td(_get_status_badge(status)),
        Td(_get_mode_badge(mode_code) if memorized else Span("-", cls="text-gray-400")),
        progress_cell,
        config_cell,
    )


def _render_profile_surah_header(surah_id, juz_number):
    """Render a surah section header row."""
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


def _get_profile_data(auth, status_filter=None):
    """Get profile data with optional status filter."""
    # Build filter condition
    filter_condition = ""
    if status_filter == STATUS_NOT_MEMORIZED:
        filter_condition = " AND (hafizs_items.memorized = 0 OR hafizs_items.memorized IS NULL)"
    elif status_filter == STATUS_LEARNING:
        filter_condition = f" AND hafizs_items.memorized = 1 AND hafizs_items.mode_code = '{NEW_MEMORIZATION_MODE_CODE}'"
    elif status_filter == STATUS_REPS:
        filter_condition = f" AND hafizs_items.memorized = 1 AND hafizs_items.mode_code IN ('{DAILY_REPS_MODE_CODE}', '{WEEKLY_REPS_MODE_CODE}', '{FORTNIGHTLY_REPS_MODE_CODE}', '{MONTHLY_REPS_MODE_CODE}')"
    elif status_filter == STATUS_SOLID:
        filter_condition = f" AND hafizs_items.memorized = 1 AND hafizs_items.mode_code = '{FULL_CYCLE_MODE_CODE}'"
    elif status_filter == STATUS_STRUGGLING:
        filter_condition = f" AND hafizs_items.memorized = 1 AND hafizs_items.mode_code = '{SRS_MODE_CODE}'"

    qry = f"""
        SELECT items.id as item_id, items.surah_id, pages.page_number, pages.juz_number,
               hafizs_items.id as hafiz_item_id, hafizs_items.memorized, hafizs_items.mode_code,
               hafizs_items.custom_daily_threshold, hafizs_items.custom_weekly_threshold,
               hafizs_items.custom_fortnightly_threshold, hafizs_items.custom_monthly_threshold
        FROM items
        LEFT JOIN pages ON items.page_id = pages.id
        LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
        WHERE items.active != 0 {filter_condition}
        ORDER BY pages.page_number ASC
    """
    return db.q(qry)


def _render_bulk_action_bar(status_filter):
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


def _render_profile_table(auth, status_filter=None, offset=0, items_per_page=25, rows_only=False):
    """Render the profile table with surah grouping and infinite scroll."""
    rows = _get_profile_data(auth, status_filter)
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
            body_rows.append(_render_profile_surah_header(surah_id, juz_number))

        body_rows.append(_render_profile_row(row, status_filter, hafiz_id=auth))

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

    bulk_bar = _render_bulk_action_bar(status_filter)

    # Always add padding at bottom to ensure bulk bar doesn't cover content
    return Div(
        Div(f"{total_items} pages", cls="text-sm text-gray-500 mb-2"),
        table,
        bulk_bar,
        id="profile-table-container",
        x_data="{ count: 0 }",
        cls="pb-20",
    )


@profile_app.get("/table/more")
def load_more_profile_rows(auth, status_filter: str = None, offset: int = 0):
    """Load more rows for infinite scroll."""
    return _render_profile_table(auth, status_filter, offset, rows_only=True)


@profile_app.get("/table")
def show_profile_page(auth, request, status_filter: str = None):
    """Profile page using HTMX table rendering (like home page)."""

    # For HTMX requests, return only the table (e.g., filter changes)
    if request.headers.get("HX-Request"):
        return _render_profile_table(auth, status_filter)

    # Configuration modal (DaisyUI dialog)
    config_modal = Dialog(
        Div(
            Form(
                Button("✕", cls="btn btn-sm btn-circle btn-ghost absolute right-2 top-2", method="dialog"),
                method="dialog",
            ),
            H3("Configure Page", cls="font-bold text-lg mb-4"),
            Div(id="config-modal-content"),
            cls="modal-box",
        ),
        id="config-modal",
        cls="modal",
    )

    return main_area(
        Div(
            render_stats_cards(auth, "table", status_filter),
            _render_profile_table(auth, status_filter),
            config_modal,
            cls="space-y-4 pt-2",
        ),
        auth=auth,
        active="Profile",
    )


# === Rep Configuration Routes ===
# These routes handle the flexible rep mode configuration


@profile_app.get("/configure_reps/{hafiz_item_id}")
def load_rep_config_modal(hafiz_item_id: int, auth):
    """Load the rep configuration modal for a specific hafiz_item - shows all modes in rows."""
    try:
        hafiz_item = hafizs_items[hafiz_item_id]
    except NotFoundError:
        return P("Item not found", cls="text-red-500")

    if hafiz_item.hafiz_id != auth:
        return P("Unauthorized", cls="text-red-500")

    # Get existing custom thresholds
    threshold_values = {
        DAILY_REPS_MODE_CODE: hafiz_item.custom_daily_threshold or DEFAULT_REP_COUNTS.get(DAILY_REPS_MODE_CODE, 7),
        WEEKLY_REPS_MODE_CODE: hafiz_item.custom_weekly_threshold or DEFAULT_REP_COUNTS.get(WEEKLY_REPS_MODE_CODE, 7),
        FORTNIGHTLY_REPS_MODE_CODE: hafiz_item.custom_fortnightly_threshold or DEFAULT_REP_COUNTS.get(FORTNIGHTLY_REPS_MODE_CODE, 7),
        MONTHLY_REPS_MODE_CODE: hafiz_item.custom_monthly_threshold or DEFAULT_REP_COUNTS.get(MONTHLY_REPS_MODE_CODE, 7),
    }

    current_mode = hafiz_item.mode_code or DAILY_REPS_MODE_CODE
    page_number = hafiz_item.page_number
    surah_name = get_surah_name(item_id=hafiz_item.item_id)

    # Mode options for dropdown with index for ordering
    # Order: DR(0) → WR(1) → FR(2) → MR(3) → FC(4) → SR(5)
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
    for code, label, idx in mode_options[:4]:  # Only graduatable modes (not Full Cycle)
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


@profile_app.post("/configure_reps")
async def configure_reps(req: Request, auth, sess):
    """Handle rep configuration for one or multiple items."""
    form_data = await req.form()

    hafiz_item_ids = form_data.getlist("hafiz_item_id")
    if not hafiz_item_ids:
        hafiz_item_id = form_data.get("hafiz_item_id")
        if hafiz_item_id:
            hafiz_item_ids = [hafiz_item_id]

    mode_code = form_data.get("mode_code")
    rep_count_raw = form_data.get("rep_count")

    # Parse rep_count: empty string -> None, otherwise int (including 0)
    rep_count = None
    if rep_count_raw is not None and rep_count_raw != "":
        try:
            rep_count = int(rep_count_raw)
        except ValueError:
            pass

    # Check for advanced mode rep counts
    # Parse without truthiness: empty string -> None, otherwise int (including 0)
    advanced_rep_counts = {}
    for mode in [DAILY_REPS_MODE_CODE, WEEKLY_REPS_MODE_CODE, FORTNIGHTLY_REPS_MODE_CODE, MONTHLY_REPS_MODE_CODE]:
        count_raw = form_data.get(f"rep_count_{mode}")
        if count_raw is not None and count_raw != "":
            try:
                advanced_rep_counts[mode] = int(count_raw)
            except ValueError:
                pass

    if not hafiz_item_ids or not mode_code:
        error_toast(sess, "Missing required parameters")
        return RedirectResponse("/profile/table", status_code=303)

    current_date = get_current_date(auth)
    updated_count = 0

    for item_id_str in hafiz_item_ids:
        try:
            hafiz_item_id = int(item_id_str)
            hafiz_item = hafizs_items[hafiz_item_id]

            if hafiz_item.hafiz_id != auth:
                continue

            # Update mode code
            hafiz_item.mode_code = mode_code

            # Update custom thresholds
            if advanced_rep_counts:
                # Advanced mode: set all thresholds
                hafiz_item.custom_daily_threshold = advanced_rep_counts.get(DAILY_REPS_MODE_CODE)
                hafiz_item.custom_weekly_threshold = advanced_rep_counts.get(WEEKLY_REPS_MODE_CODE)
                hafiz_item.custom_fortnightly_threshold = advanced_rep_counts.get(FORTNIGHTLY_REPS_MODE_CODE)
                hafiz_item.custom_monthly_threshold = advanced_rep_counts.get(MONTHLY_REPS_MODE_CODE)
            elif rep_count is not None:
                # Simple mode: only set threshold for selected mode (including 0)
                column = MODE_TO_THRESHOLD_COLUMN.get(mode_code)
                if column:
                    setattr(hafiz_item, column, rep_count)

            # Set next_review and next_interval based on mode
            if mode_code in REP_MODES_CONFIG:
                config = REP_MODES_CONFIG[mode_code]
                hafiz_item.next_interval = config["interval"]
                hafiz_item.next_review = add_days_to_date(current_date, config["interval"])
            elif mode_code == FULL_CYCLE_MODE_CODE:
                hafiz_item.next_interval = None
                hafiz_item.next_review = None

            hafizs_items.update(hafiz_item)
            updated_count += 1
        except (ValueError, NotFoundError):
            continue

    if updated_count > 0:
        success_toast(sess, f"Updated configuration for {updated_count} page(s)")
    else:
        error_toast(sess, "No pages were updated")

    return RedirectResponse("/profile/table", status_code=303)


@profile_app.post("/quick_change_mode/{hafiz_item_id}")
def quick_change_mode(hafiz_item_id: int, mode_code: str, auth, sess):
    """Quick inline mode change from the profile page dropdown."""
    try:
        hafiz_item = hafizs_items[hafiz_item_id]
    except NotFoundError:
        error_toast(sess, "Item not found")
        return Response(status_code=204)

    if hafiz_item.hafiz_id != auth:
        error_toast(sess, "Unauthorized")
        return Response(status_code=204)

    current_date = get_current_date(auth)

    # Update mode code
    hafiz_item.mode_code = mode_code

    # Set next_review and next_interval based on mode
    if mode_code in REP_MODES_CONFIG:
        config = REP_MODES_CONFIG[mode_code]
        hafiz_item.next_interval = config["interval"]
        hafiz_item.next_review = add_days_to_date(current_date, config["interval"])
    elif mode_code == FULL_CYCLE_MODE_CODE:
        hafiz_item.next_interval = None
        hafiz_item.next_review = None

    hafizs_items.update(hafiz_item)
    success_toast(sess, f"Mode changed to {get_mode_name(mode_code)}")
    return Response(status_code=204)


@profile_app.post("/update_threshold/{hafiz_item_id}")
def update_threshold(hafiz_item_id: int, threshold: int, auth, sess):
    """Update the threshold for the current mode inline."""
    try:
        hafiz_item = hafizs_items[hafiz_item_id]
    except NotFoundError:
        error_toast(sess, "Item not found")
        return Response(status_code=204)

    if hafiz_item.hafiz_id != auth:
        error_toast(sess, "Unauthorized")
        return Response(status_code=204)

    # Set custom threshold for current mode
    mode_code = hafiz_item.mode_code
    if mode_code in MODE_TO_THRESHOLD_COLUMN:
        column = MODE_TO_THRESHOLD_COLUMN[mode_code]
        setattr(hafiz_item, column, threshold)
        hafizs_items.update(hafiz_item)
        success_toast(sess, f"Threshold updated to {threshold}")
    else:
        error_toast(sess, "Cannot set threshold for this mode")

    return Response(status_code=204)


@profile_app.post("/graduate_item/{hafiz_item_id}")
def graduate_item(hafiz_item_id: int, target_mode: str, auth, sess):
    """Graduate an item to a target mode."""
    try:
        hafiz_item = hafizs_items[hafiz_item_id]
    except NotFoundError:
        error_toast(sess, "Item not found")
        return Response(status_code=204)

    if hafiz_item.hafiz_id != auth:
        error_toast(sess, "Unauthorized")
        return Response(status_code=204)

    current_date = get_current_date(auth)
    old_mode = hafiz_item.mode_code

    # Update mode code
    hafiz_item.mode_code = target_mode

    # Set next_review and next_interval based on target mode
    if target_mode in REP_MODES_CONFIG:
        config = REP_MODES_CONFIG[target_mode]
        hafiz_item.next_interval = config["interval"]
        hafiz_item.next_review = add_days_to_date(current_date, config["interval"])
    elif target_mode == FULL_CYCLE_MODE_CODE:
        hafiz_item.memorized = True
        hafiz_item.next_interval = None
        hafiz_item.next_review = None

    hafizs_items.update(hafiz_item)
    success_toast(sess, f"Graduated from {get_mode_name(old_mode)} to {get_mode_name(target_mode)}")
    return Response(status_code=204)


