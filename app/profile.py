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


# === JSON API for Tabulator ===


@profile_app.get("/api/pages")
def get_pages_json(auth, status_filter: str = None):
    """Return page data as JSON for Tabulator table."""
    from starlette.responses import JSONResponse

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
    rows = db.q(qry)

    # Transform to Tabulator-friendly format
    data = []
    for row in rows:
        mode_code = row["mode_code"] or ""
        mode_name = get_mode_name(mode_code) if mode_code else "-"
        mode_icon = get_mode_icon(mode_code) if mode_code else ""

        # Calculate progress for graduatable modes
        progress = "-"
        if mode_code in GRADUATABLE_MODES:
            current_count = get_mode_count(row["item_id"], mode_code)
            threshold = DEFAULT_REP_COUNTS.get(mode_code, 7)
            # Check custom thresholds
            threshold_map = {
                DAILY_REPS_MODE_CODE: row.get("custom_daily_threshold"),
                WEEKLY_REPS_MODE_CODE: row.get("custom_weekly_threshold"),
                FORTNIGHTLY_REPS_MODE_CODE: row.get("custom_fortnightly_threshold"),
                MONTHLY_REPS_MODE_CODE: row.get("custom_monthly_threshold"),
            }
            custom = threshold_map.get(mode_code)
            if custom is not None:
                threshold = custom
            progress = f"{current_count} of {threshold}"

        # Get status
        status = get_status(row)
        status_icon, status_label = get_status_display(status)

        data.append({
            "page": row["page_number"],
            "juz": row["juz_number"],
            "surah": surahs[row["surah_id"]].name if row["surah_id"] else "-",
            "memorized": bool(row["memorized"]),
            "status": status_label,
            "status_icon": status_icon,
            "mode": mode_name,
            "mode_icon": mode_icon,
            "mode_code": mode_code,
            "progress": progress,
            "hafiz_item_id": row["hafiz_item_id"],
            "item_id": row["item_id"],
        })

    return JSONResponse(data)


@profile_app.get("/table")
def show_tabulator_page(auth, status_filter: str = None):
    """Profile page using Tabulator for interactive table."""

    # Build API URL with filter
    api_url = "/profile/api/pages"
    if status_filter:
        api_url += f"?status_filter={status_filter}"

    # Tabulator initialization script with enhanced formatters
    tabulator_init = Script(f"""
        document.addEventListener('DOMContentLoaded', function() {{
            // Status color mapping
            var statusColors = {{
                "Not Memorized": "#6b7280",  // gray
                "Learning": "#22c55e",        // green
                "Reps": "#3b82f6",            // blue
                "Solid": "#8b5cf6",           // purple
                "Struggling": "#ef4444"       // red
            }};

            // Mode color mapping
            var modeColors = {{
                "Daily Reps": "#f59e0b",      // amber
                "Weekly Reps": "#3b82f6",     // blue
                "Fortnightly Reps": "#8b5cf6", // purple
                "Monthly Reps": "#ec4899",    // pink
                "Full cycle": "#22c55e",      // green
                "SRS - Variable Reps": "#ef4444" // red
            }};

            var table = new Tabulator("#profile-table", {{
                ajaxURL: "{api_url}",
                layout: "fitColumns",
                responsiveLayout: "collapse",
                pagination: true,
                paginationSize: 25,
                paginationSizeSelector: [10, 25, 50, 100],
                paginationCounter: "rows",
                movableColumns: true,
                placeholder: "No pages found",
                selectable: true,
                selectableRangeMode: "click",
                columns: [
                    {{title: "Page", field: "page", sorter: "number", headerFilter: "number", width: 80,
                     formatter: function(cell) {{
                        return "<strong>" + cell.getValue() + "</strong>";
                    }}}},
                    {{title: "Juz", field: "juz", sorter: "number", headerFilter: "number", width: 70}},
                    {{title: "Surah", field: "surah", sorter: "string", headerFilter: "input"}},
                    {{title: "Status", field: "status", sorter: "string", headerFilter: "list",
                     headerFilterParams: {{values: ["Not Memorized", "Learning", "Reps", "Solid", "Struggling"]}},
                     formatter: function(cell) {{
                        var data = cell.getRow().getData();
                        var color = statusColors[data.status] || "#6b7280";
                        return '<span style="background-color: ' + color + '20; color: ' + color + '; padding: 2px 8px; border-radius: 4px; font-size: 12px;">' + data.status_icon + ' ' + data.status + '</span>';
                    }}}},
                    {{title: "Mode", field: "mode", sorter: "string", headerFilter: "list",
                     headerFilterParams: {{values: ["Daily Reps", "Weekly Reps", "Fortnightly Reps", "Monthly Reps", "Full cycle", "SRS - Variable Reps", "-"]}},
                     formatter: function(cell) {{
                        var data = cell.getRow().getData();
                        var color = modeColors[data.mode] || "#6b7280";
                        return '<span style="background-color: ' + color + '20; color: ' + color + '; padding: 2px 8px; border-radius: 4px; font-size: 12px;">' + data.mode_icon + ' ' + data.mode + '</span>';
                    }}}},
                    {{title: "Progress", field: "progress", sorter: "string", headerFilter: false, width: 150,
                     formatter: function(cell) {{
                        var value = cell.getValue();
                        if (value === "-") return "-";

                        // Parse "0 of 7" format
                        var parts = value.split(" of ");
                        if (parts.length !== 2) return value;

                        var current = parseInt(parts[0]);
                        var total = parseInt(parts[1]);
                        var percent = (current / total) * 100;

                        // Color based on progress
                        var barColor = percent < 30 ? "#ef4444" : percent < 70 ? "#f59e0b" : "#22c55e";

                        return '<div style="display: flex; align-items: center; gap: 8px;">' +
                            '<div style="flex: 1; background: #e5e7eb; border-radius: 4px; height: 8px; overflow: hidden;">' +
                            '<div style="width: ' + percent + '%; height: 100%; background: ' + barColor + '; transition: width 0.3s;"></div>' +
                            '</div>' +
                            '<span style="font-size: 11px; color: #6b7280; min-width: 45px;">' + value + '</span>' +
                            '</div>';
                    }}}},
                ],
                initialSort: [
                    {{column: "page", dir: "asc"}}
                ],
            }});

            // Store table reference globally for other interactions
            window.profileTable = table;

            // Global search
            document.getElementById("search-input").addEventListener("keyup", function() {{
                var value = this.value.toLowerCase();
                table.setFilter(function(data) {{
                    return String(data.page).includes(value) ||
                           data.surah.toLowerCase().includes(value) ||
                           data.status.toLowerCase().includes(value) ||
                           data.mode.toLowerCase().includes(value);
                }});
            }});

            // Clear filters button
            document.getElementById("clear-filters").addEventListener("click", function() {{
                table.clearFilter(true);
                table.clearHeaderFilter();
                document.getElementById("search-input").value = "";
            }});

            // Update selection count
            table.on("rowSelectionChanged", function(data, rows) {{
                var count = rows.length;
                var badge = document.getElementById("selection-count");
                if (badge) {{
                    badge.textContent = count > 0 ? count + " selected" : "";
                    badge.style.display = count > 0 ? "inline-block" : "none";
                }}
            }});
        }});
    """)

    return main_area(
        Div(
            render_stats_cards(auth, "table", status_filter),
            # Search and controls
            Div(
                Div(
                    Input(
                        type="text",
                        id="search-input",
                        placeholder="Search pages, surahs, modes...",
                        cls="input input-bordered input-sm w-64",
                    ),
                    Button(
                        "Clear Filters",
                        id="clear-filters",
                        cls="btn btn-sm btn-ghost",
                    ),
                    Span(
                        id="selection-count",
                        cls="badge badge-primary ml-2",
                        style="display: none;",
                    ),
                    cls="flex items-center gap-2",
                ),
                A(
                    "← Back to old view",
                    href="/profile/page",
                    cls="text-sm text-gray-500 hover:underline",
                ),
                cls="flex justify-between items-center mb-4",
            ),
            # Tabulator container
            Div(id="profile-table", cls="bg-base-100 rounded-lg shadow-sm"),
            tabulator_init,
            cls="space-y-4 pt-2",
        ),
        auth=auth,
        active="Memorization Status",
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
        return RedirectResponse("/profile/surah", status_code=303)

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

    return RedirectResponse("/profile/surah", status_code=303)


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


def memorized_checkbox(items):
    if not items:
        status = False
    else:
        num_memorized = sum(item.get("memorized", 0) for item in items)
        total_items = len(items)

        if num_memorized == total_items:
            status = True
        elif num_memorized == 0:
            status = False
        else:
            status = None  # Indeterminate

    return CheckboxX(
        name="selected_memorized_status",
        checked=status,
        cls=(
            "bg-[image:var(--uk-form-checkbox-image-indeterminate)]"
            if status is None
            else ""
        ),
    )


def render_type_description(list, _type=""):
    first_description = list[0]
    last_description = list[-1]

    if _type == "Surah":
        _type = ""
        first_description = surahs[first_description].name
        last_description = surahs[last_description].name

    if len(list) == 1:
        return f"{_type} {first_description}"
    return (
        f"{_type}{"" if _type == "" else "s"} {first_description} – {last_description}"
    )


# === Mode Management Section ===
# NOTE: These routes MUST be defined before the /{current_type} catch-all route


def get_items_by_mode(auth, mode_code):
    """Query hafizs_items grouped by mode_code for mode management."""
    qry = f"""
        SELECT hafizs_items.id, hafizs_items.item_id, hafizs_items.mode_code,
               hafizs_items.next_interval, hafizs_items.next_review,
               items.surah_id, pages.page_number, pages.juz_number
        FROM hafizs_items
        JOIN items ON hafizs_items.item_id = items.id
        JOIN pages ON items.page_id = pages.id
        WHERE hafizs_items.hafiz_id = {auth}
          AND hafizs_items.mode_code = '{mode_code}'
        ORDER BY pages.page_number ASC
    """
    return db.q(qry)


@profile_app.get("/mode_management")
def show_mode_management(auth):
    """Display pages grouped by their current mode with graduation options."""

    def render_mode_group(mode_code):
        config = REP_MODES_CONFIG.get(mode_code)
        if not config:
            return None

        items_in_mode = get_items_by_mode(auth, mode_code)
        if not items_in_mode:
            return None

        next_mode_code = config["next_mode_code"]
        mode_name = get_mode_name(mode_code)
        next_mode_name = get_mode_name(next_mode_code)
        mode_icon = get_mode_icon(mode_code)
        next_icon = get_mode_icon(next_mode_code)
        interval = config["interval"]

        page_numbers = compact_format([item["page_number"] for item in items_in_mode])

        return Div(
            DivFullySpaced(
                Div(
                    Span(f"{mode_icon} {mode_name}", cls="font-semibold text-lg"),
                    Span(f" ({interval}-day interval)", cls="text-gray-500"),
                ),
                Span(f"{len(items_in_mode)} pages", cls="badge badge-neutral"),
            ),
            P(f"Pages: {page_numbers}", cls="text-sm text-gray-600 mt-1"),
            Div(
                Button(
                    f"Graduate to {next_icon} {next_mode_name} →",
                    hx_get=f"/profile/mode_management/confirm/{mode_code}",
                    target_id="graduation-modal-body",
                    data_uk_toggle="target: #graduation-modal",
                    cls=(ButtonT.primary, "mt-2"),
                    data_testid=f"graduate-{mode_code}-button",
                ),
                cls="mt-2",
            ),
            cls="p-4 border rounded-lg bg-base-100 mb-4",
            data_testid=f"mode-group-{mode_code}",
        )

    mode_groups = [
        render_mode_group(mode_code) for mode_code in GRADUATABLE_MODES
    ]
    # Filter out None values (modes with no items)
    mode_groups = [g for g in mode_groups if g is not None]

    if not mode_groups:
        empty_state = Div(
            P("No pages in rep modes (Daily, Weekly, Fortnightly, Monthly)."),
            P("Pages graduate through these modes automatically via regular reviews."),
            cls="text-center text-gray-500 py-8",
        )
        mode_groups = [empty_state]

    # Modal for graduation confirmation
    modal = Div(
        ModalContainer(
            ModalDialog(
                ModalHeader(
                    ModalTitle("Confirm Graduation", id="graduation-modal-title"),
                    ModalCloseButton(),
                ),
                ModalBody(
                    Div(id="graduation-modal-body"),
                ),
                cls="uk-margin-auto-vertical",
            ),
            id="graduation-modal",
        ),
    )

    return main_area(
        Div(
            H2("Mode Management", cls="text-2xl font-bold mb-4"),
            P(
                "Manually advance pages through the rep mode chain. ",
                "Normally pages graduate automatically after 7 reviews in each mode.",
                cls=TextPresets.muted_sm + " mb-6",
            ),
            *mode_groups,
            modal,
            cls="space-y-4 pt-2",
        ),
        auth=auth,
        active="Memorization Status",
    )


@profile_app.get("/mode_management/confirm/{mode_code}")
def confirm_graduation(mode_code: str, auth):
    """Load the graduation confirmation modal content."""
    config = REP_MODES_CONFIG.get(mode_code)
    if not config:
        return P("Invalid mode", cls="text-red-500")

    items_in_mode = get_items_by_mode(auth, mode_code)
    if not items_in_mode:
        return P("No items to graduate", cls="text-gray-500")

    next_mode_code = config["next_mode_code"]
    mode_name = get_mode_name(mode_code)
    next_mode_name = get_mode_name(next_mode_code)
    mode_icon = get_mode_icon(mode_code)
    next_icon = get_mode_icon(next_mode_code)

    def render_item_row(item):
        return Tr(
            Td(
                CheckboxX(
                    name="item_ids",
                    value=str(item["id"]),
                    checked=True,
                    cls="graduation-checkbox",
                ),
            ),
            Td(item["page_number"], cls="font-mono"),
            Td(surahs[item["surah_id"]].name),
            Td(f"Juz {item['juz_number']}"),
        )

    return Div(
        P(
            f"Graduate {len(items_in_mode)} pages from ",
            Span(f"{mode_icon} {mode_name}", cls="font-semibold"),
            " to ",
            Span(f"{next_icon} {next_mode_name}", cls="font-semibold"),
            "?",
            cls="text-lg mb-4",
        ),
        Form(
            Div(
                Table(
                    Thead(
                        Tr(
                            Th(
                                CheckboxX(
                                    cls="select-all-graduation",
                                    x_model="selectAll",
                                    _at_change="toggleAll()",
                                )
                            ),
                            Th("Page"),
                            Th("Surah"),
                            Th("Juz"),
                        )
                    ),
                    Tbody(*[render_item_row(item) for item in items_in_mode]),
                    cls=(TableT.middle, TableT.divider, TableT.sm),
                    x_data=select_all_checkbox_x_data(
                        class_name="graduation-checkbox", is_select_all="true"
                    ),
                    x_init="updateSelectAll()",
                ),
                cls="max-h-64 overflow-auto",
            ),
            Hidden(name="mode_code", value=mode_code),
            Div(
                Button(
                    f"Graduate Selected to {next_mode_name}",
                    type="submit",
                    cls=(ButtonT.primary, "uk-modal-close"),
                    data_testid="confirm-graduation-button",
                ),
                Button(
                    "Cancel",
                    type="button",
                    cls=(ButtonT.secondary, "uk-modal-close"),
                ),
                cls="flex gap-2 mt-4 justify-end",
            ),
            hx_post="/profile/mode_management/graduate",
            hx_target="body",
        ),
    )


@profile_app.post("/mode_management/graduate")
async def graduate_items(req: Request, auth, sess):
    """Process manual graduation of selected items."""
    form_data = await req.form()
    mode_code = form_data.get("mode_code")
    item_ids = form_data.getlist("item_ids")

    if not mode_code or not item_ids:
        error_toast(sess, "No items selected for graduation")
        return RedirectResponse("/profile/mode_management", status_code=303)

    config = REP_MODES_CONFIG.get(mode_code)
    if not config:
        error_toast(sess, "Invalid mode")
        return RedirectResponse("/profile/mode_management", status_code=303)

    next_mode_code = config["next_mode_code"]
    current_date = get_current_date(auth)
    graduated_count = 0

    for item_id in item_ids:
        try:
            hafiz_item_id = int(item_id)
            hafiz_item = hafizs_items[hafiz_item_id]

            # Verify item belongs to current hafiz and is in the expected mode
            if hafiz_item.hafiz_id != auth or hafiz_item.mode_code != mode_code:
                continue

            # Graduate to next mode
            hafiz_item.mode_code = next_mode_code

            if next_mode_code == FULL_CYCLE_MODE_CODE:
                # Final graduation: clear scheduling fields
                hafiz_item.memorized = True
                hafiz_item.next_interval = None
                hafiz_item.next_review = None
            else:
                # Graduate to next rep mode: use that mode's interval
                next_config = REP_MODES_CONFIG[next_mode_code]
                hafiz_item.next_interval = next_config["interval"]
                hafiz_item.next_review = add_days_to_date(
                    current_date, next_config["interval"]
                )

            hafizs_items.update(hafiz_item)
            graduated_count += 1
        except (ValueError, NotFoundError):
            continue

    if graduated_count > 0:
        next_mode_name = get_mode_name(next_mode_code)
        success_toast(sess, f"Graduated {graduated_count} pages to {next_mode_name}")
    else:
        error_toast(sess, "No pages were graduated")

    return RedirectResponse("/profile/mode_management", status_code=303)


# === Memorization Status Section ===
# NOTE: The /{current_type} route MUST be defined after mode_management routes


@profile_app.get("/{current_type}")
def show_page_status(current_type: str, auth, status: str = "", status_filter: str = None, sort: str = None, dir: str = "asc"):
    memorized_filter = None  # Initially we didn't apply filter
    if status == "memorized":
        memorized_filter = True
    elif status == "not_memorized":
        memorized_filter = False

    # Map status_filter to mode_code conditions for SQL query
    status_filter_condition = None
    if status_filter == STATUS_NOT_MEMORIZED:
        status_filter_condition = "(hafizs_items.memorized = 0 OR hafizs_items.memorized IS NULL)"
    elif status_filter == STATUS_LEARNING:
        status_filter_condition = f"(hafizs_items.memorized = 1 AND hafizs_items.mode_code = '{NEW_MEMORIZATION_MODE_CODE}')"
    elif status_filter == STATUS_REPS:
        status_filter_condition = f"(hafizs_items.memorized = 1 AND hafizs_items.mode_code IN ('{DAILY_REPS_MODE_CODE}', '{WEEKLY_REPS_MODE_CODE}', '{FORTNIGHTLY_REPS_MODE_CODE}', '{MONTHLY_REPS_MODE_CODE}'))"
    elif status_filter == STATUS_SOLID:
        status_filter_condition = f"(hafizs_items.memorized = 1 AND hafizs_items.mode_code = '{FULL_CYCLE_MODE_CODE}')"
    elif status_filter == STATUS_STRUGGLING:
        status_filter_condition = f"(hafizs_items.memorized = 1 AND hafizs_items.mode_code = '{SRS_MODE_CODE}')"

    # Sorting configuration
    # Mode order: NM(0) → DR(1) → WR(2) → FR(3) → MR(4) → FC(5) → SR(6)
    mode_order_case = f"""
        CASE hafizs_items.mode_code
            WHEN '{NEW_MEMORIZATION_MODE_CODE}' THEN 0
            WHEN '{DAILY_REPS_MODE_CODE}' THEN 1
            WHEN '{WEEKLY_REPS_MODE_CODE}' THEN 2
            WHEN '{FORTNIGHTLY_REPS_MODE_CODE}' THEN 3
            WHEN '{MONTHLY_REPS_MODE_CODE}' THEN 4
            WHEN '{FULL_CYCLE_MODE_CODE}' THEN 5
            WHEN '{SRS_MODE_CODE}' THEN 6
            ELSE 99
        END
    """
    sort_direction = "DESC" if dir == "desc" else "ASC"
    order_clause = "ORDER BY pages.page_number ASC"  # Default
    if sort == "mode":
        order_clause = f"ORDER BY {mode_order_case} {sort_direction}, pages.page_number ASC"
    elif sort == "page":
        order_clause = f"ORDER BY pages.page_number {sort_direction}"

    def render_row_based_on_type(type_number: str, records: list, current_type):
        memorized_value = records[0]["memorized"]
        if memorized_filter is not None and memorized_filter != memorized_value:
            return None

        _surahs = sorted({r["surah_id"] for r in records})
        _pages = sorted([r["page_number"] for r in records])
        _juzs = sorted({r["juz_number"] for r in records})

        surah_range = render_type_description(_surahs, "Surah")
        page_range = render_type_description(_pages, "Page")
        juz_range = render_type_description(_juzs, "Juz")

        if current_type == "juz":
            details = [surah_range, page_range]
            details_str = f"{surah_range} ({page_range})"
        elif current_type == "surah":
            details = [juz_range, page_range]
            details_str = f"{juz_range} ({page_range})"
        elif current_type == "page":
            details = [juz_range, surah_range]
            details_str = f"{juz_range} | {surah_range}"

        title = (
            f"{current_type.capitalize()} {type_number}"
            if current_type != "surah"
            else surahs[type_number].name
        )
        item_length = 1

        memorized_filter_str = f"memorized = {memorized_value}"

        if current_type == "page":
            where_clause = f"page_number={type_number} and hafiz_id={auth}"
            if status:
                where_clause += f" and {memorized_filter_str}"
            item_length = len(hafizs_items(where=where_clause) or [])

        elif current_type in ("surah", "juz"):
            item_ids = grouped.get(type_number, [])
            if item_ids:
                if len(item_ids) > 1:
                    item_id_list = ",".join(str(i["id"]) for i in item_ids)
                    where_clause = f"item_id IN ({item_id_list}) and hafiz_id={auth}"
                    if status:
                        where_clause += f" and {memorized_filter_str}"
                    item_length = len(hafizs_items(where=where_clause) or [])

        show_customize_button = item_length > 1

        # Three columns for page view: Mode, Progress, Graduate
        mode_cell = None
        progress_cell = None
        graduate_cell = None
        if current_type == "page" and len(records) == 1:
            record = records[0]
            mode_code = record.get("mode_code")
            hafiz_item_id = record.get("hafiz_item_id")
            item_id = record.get("item_id") or record.get("id")
            if memorized_value and mode_code and hafiz_item_id:
                # Mode dropdown
                mode_cell = Td(render_mode_dropdown(hafiz_item_id, mode_code))

                # Progress and Graduate only for graduatable modes
                if mode_code in GRADUATABLE_MODES:
                    current_count = get_mode_count(item_id, mode_code)
                    threshold = DEFAULT_REP_COUNTS.get(mode_code, 7)
                    # Check for custom threshold
                    threshold_columns = {
                        DAILY_REPS_MODE_CODE: "custom_daily_threshold",
                        WEEKLY_REPS_MODE_CODE: "custom_weekly_threshold",
                        FORTNIGHTLY_REPS_MODE_CODE: "custom_fortnightly_threshold",
                        MONTHLY_REPS_MODE_CODE: "custom_monthly_threshold",
                    }
                    if mode_code in threshold_columns:
                        custom = record.get(threshold_columns[mode_code])
                        if custom is not None:
                            threshold = custom

                    progress_cell = Td(render_progress_cell(hafiz_item_id, current_count, threshold))
                    graduate_cell = Td(render_graduate_cell(hafiz_item_id, mode_code))
                else:
                    # Non-graduatable modes (Full Cycle, SRS)
                    progress_cell = Td("-")
                    graduate_cell = Td("-")
            else:
                mode_cell = Td("-")
                progress_cell = Td("-")
                graduate_cell = Td("-")

        row_cells = [
            Td(title),
            Td(details[0]),
            Td(details[1]),
            Td(
                Form(
                    Hidden(name="filter_status", value=status),
                    memorized_checkbox(records),
                    hx_post=f"/profile/update_status/{current_type}/{type_number}",
                    hx_target=f"#{current_type}-{type_number}",
                    hx_select=f"#{current_type}-{type_number}",
                    hx_select_oob="#stats_info",
                    hx_swap="outerHTML",
                    hx_trigger="change",
                )
            ),
        ]

        # Add Mode, Progress, Graduate columns for page view
        if current_type == "page":
            if mode_cell:
                row_cells.append(mode_cell)
            if progress_cell:
                row_cells.append(progress_cell)
            if graduate_cell:
                row_cells.append(graduate_cell)

        # Customize button (for multi-item rows)
        row_cells.append(
            Td(
                A("Customize ➡️"),
                cls=(AT.classic, "text-right"),
                hx_get=f"/profile/custom_status_update/{current_type}/{type_number}"
                + (f"?status={status}" if status else ""),
                hx_vals={
                    "title": title,
                    "description": details_str,
                    "filter_status": status,
                },
                target_id="my-modal-body",
                data_uk_toggle="target: #my-modal",
            )
            if show_customize_button
            else Td("")
        )

        return Tr(
            *row_cells,
            id=f"{current_type}-{type_number}",
            data_testid=f"{current_type}-{type_number}-row",
        )

    if not current_type:
        current_type = "juz"

    def render_navigation_item(_type: str):
        # Build query params preserving both status and status_filter
        params = []
        if status:
            params.append(f"status={status}")
        if status_filter:
            params.append(f"status_filter={status_filter}")
        query_str = "?" + "&".join(params) if params else ""
        return Li(
            A(
                f"by {_type}",
                href=f"/profile/{_type}{query_str}",
            ),
            cls=("uk-active" if _type == current_type else None),
        )

    # Include mode_code and custom thresholds for Mode & Reps display in page view
    qry = f"""SELECT items.id, items.surah_id, pages.page_number, pages.juz_number,
                     hafizs_items.id as hafiz_item_id, hafizs_items.memorized, hafizs_items.mode_code, hafizs_items.item_id,
                     hafizs_items.custom_daily_threshold, hafizs_items.custom_weekly_threshold,
                     hafizs_items.custom_fortnightly_threshold, hafizs_items.custom_monthly_threshold
              FROM items
              LEFT JOIN pages ON items.page_id = pages.id
              LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
              WHERE items.active != 0"""

    # Build filter conditions
    filter_conditions = []
    if status in ["memorized", "not_memorized"]:
        filter_conditions.append(f"hafizs_items.memorized = {memorized_filter}")
    if status_filter_condition:
        filter_conditions.append(status_filter_condition)

    if filter_conditions:
        qry += f" AND {' AND '.join(filter_conditions)}"

    # Add ORDER BY clause (only for page view where sorting makes sense)
    if current_type == "page":
        qry += f" {order_clause}"

    qry_data = db.q(qry)

    # Preserve SQL ORDER BY when sorting is active
    grouped = group_by_type(qry_data, current_type, preserve_order=bool(sort))
    rows = [
        render_row_based_on_type(type_number, records, current_type)
        for type_number, records in grouped.items()
    ]

    def render_filter_btn(text):
        return Label(
            text,
            hx_get=f"/profile/{current_type}?status={standardize_column(text)}",
            hx_target="body",
            hx_push_url="true",
            cls=(
                "cursor-pointer",
                (
                    LabelT.primary
                    if status == standardize_column(text)
                    else LabelT.secondary
                ),
            ),
        )

    filter_btns = DivLAligned(
        P("Status Filter:", cls=TextPresets.muted_sm),
        *map(
            render_filter_btn,
            ["Memorized", "Not Memorized"],
        ),
        (
            Label(
                "X",
                hx_get=f"/profile/{current_type}",
                hx_target="body",
                hx_push_url="true",
                cls=(
                    "cursor-pointer",
                    TextT.xs,
                    LabelT.destructive,
                    (None if status else "invisible"),
                ),
            )
        ),
        # Spacer to push mode management link to the right
        Div(cls="flex-grow"),
        A(
            "⚙️ Mode Management",
            href="/profile/mode_management",
            cls="text-sm text-primary hover:underline",
            data_testid="mode-management-link",
        ),
    )

    modal = Div(
        ModalContainer(
            ModalDialog(
                ModalHeader(
                    ModalTitle(id="my-modal-title"),
                    P(cls=TextPresets.muted_sm, id="my-modal-description"),
                    ModalCloseButton(),
                    cls="space-y-3",
                ),
                Form(
                    ModalBody(
                        Div(id="my-modal-body"),
                        data_uk_overflow_auto=True,
                    ),
                    ModalFooter(
                        Div(id="my-modal-footer"),
                    ),
                    Div(id="my-modal-link"),
                ),
                cls="uk-margin-auto-vertical",
            ),
            id="my-modal",
        ),
        id="modal-container",
    )

    type_details = {
        "page": ["Juz", "Surah"],
        "surah": ["Juz", "Page"],
        "juz": ["Surah", "Page"],
    }

    details = type_details.get(current_type, ["", ""])

    # Helper to build sortable header link
    def sortable_th(label, sort_key):
        # Build URL preserving existing params
        params = []
        if status:
            params.append(f"status={status}")
        if status_filter:
            params.append(f"status_filter={status_filter}")
        # Toggle direction if clicking same column
        new_dir = "desc" if sort == sort_key and dir == "asc" else "asc"
        params.append(f"sort={sort_key}")
        params.append(f"dir={new_dir}")
        url = f"/profile/{current_type}?" + "&".join(params)

        # Show sort indicator
        indicator = ""
        if sort == sort_key:
            indicator = " ▲" if dir == "asc" else " ▼"

        return Th(
            A(f"{label}{indicator}", href=url, cls="hover:underline cursor-pointer"),
        )

    # Build table headers - add Mode, Progress, Graduate columns for page view
    header_cells = [
        sortable_th("Page", "page") if current_type == "page" else Th(current_type.title()),
        *map(Th, details),
        Th("Status"),
    ]
    if current_type == "page":
        header_cells.extend([sortable_th("Mode", "mode"), Th("Progress"), Th("Graduate to")])
    header_cells.append(Th(""))  # Customize column

    # Configure modal for rep configuration (used in page view)
    configure_modal = ModalContainer(
        ModalDialog(
            ModalHeader(
                ModalTitle("Configure Repetitions", id="configure-modal-title"),
                ModalCloseButton(),
            ),
            ModalBody(
                Div(id="configure-modal-body"),
            ),
            cls="uk-margin-auto-vertical",
        ),
        id="configure-modal",
    )

    return main_area(
        Div(
            render_stats_cards(auth, current_type, status_filter),
            DivFullySpaced(
                filter_btns,
            ),
            Div(
                TabContainer(
                    *map(render_navigation_item, ["juz", "surah", "page"]),
                ),
                Div(
                    Table(
                        Thead(Tr(*header_cells)),
                        Tbody(*rows),
                        x_data=select_all_checkbox_x_data(
                            class_name="profile_rows", is_select_all="false"
                        ),
                        x_init="updateSelectAll()",
                    ),
                    cls="h-[75vh] overflow-auto uk-overflow-auto",
                ),
                cls="space-y-5",
            ),
            Div(modal),
            configure_modal,
            cls="space-y-5 pt-2",
        ),
        auth=auth,
        active="Memorization Status",
    )


@profile_app.get("/custom_status_update/{current_type}/{type_number}")
def load_descendant_items_for_profile(
    current_type: str,
    type_number: int,
    title: str,
    description: str,
    filter_status: str,
    auth,
    status: str = None,
):
    memorized_filter = None
    if status == "memorized":
        memorized_filter = True
    elif status == "not_memorized":
        memorized_filter = False

    if current_type == "juz":
        condition = f"pages.juz_number = {type_number}"
    elif current_type == "surah":
        condition = f"items.surah_id = {type_number}"
    elif current_type == "page":
        condition = f"pages.page_number = {type_number}"
    else:
        return "Invalid current_type"
    # Include mode_code and custom thresholds for Mode & Reps display
    qry = f"""SELECT items.id, items.surah_id, pages.page_number, pages.juz_number,
                     hafizs_items.id as hafiz_item_id, hafizs_items.memorized, hafizs_items.mode_code, hafizs_items.item_id,
                     hafizs_items.custom_daily_threshold, hafizs_items.custom_weekly_threshold,
                     hafizs_items.custom_fortnightly_threshold, hafizs_items.custom_monthly_threshold
              FROM items
              LEFT JOIN pages ON items.page_id = pages.id
              LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
              WHERE items.active != 0 AND {condition};"""

    if memorized_filter is not None:
        qry = qry.replace(";", f" AND hafizs_items.memorized = {memorized_filter};")
    ct = db.q(qry)

    def render_row(record):
        current_memorized_status = record["memorized"]
        current_id = record["id"]
        hafiz_item_id = record["hafiz_item_id"]
        mode_code = record["mode_code"]

        # Render mode and reps info for memorized items
        mode_reps_cell = Td("-")
        configure_cell = Td("")
        if current_memorized_status and mode_code:
            mode_reps_cell = Td(render_mode_and_reps(record, mode_code))
            # Only show Configure for items in graduatable modes
            if hafiz_item_id and mode_code in GRADUATABLE_MODES:
                configure_cell = Td(
                    A(
                        "⚙️",
                        hx_get=f"/profile/configure_reps/{hafiz_item_id}",
                        target_id="configure-modal-body",
                        data_uk_toggle="target: #configure-modal",
                        cls="cursor-pointer hover:opacity-70",
                        title="Configure reps",
                    )
                )

        return Tr(
            Td(
                # This hidden input is to send the id to the backend even if it is unchecked
                Hidden(name=f"id-{current_id}", value="0"),
                CheckboxX(
                    name=f"id-{current_id}",
                    value="1",
                    checked=current_memorized_status,
                    cls="partial_rows",  # Alpine js reference
                    _at_click="handleCheckboxClick($event)",
                ),
            ),
            Td(record["page_number"]),
            Td(surahs[record["surah_id"]].name),
            Td(f"Juz {record['juz_number']}"),
            Td("Memorized" if current_memorized_status else "Not Memorized"),
            mode_reps_cell,
            configure_cell,
        )

    # Modal for configure reps
    configure_modal = ModalContainer(
        ModalDialog(
            ModalHeader(
                ModalTitle("Configure Repetitions", id="configure-modal-title"),
                ModalCloseButton(),
            ),
            ModalBody(
                Div(id="configure-modal-body"),
            ),
            cls="uk-margin-auto-vertical",
        ),
        id="configure-modal",
    )

    table = Table(
        Thead(
            Tr(
                Th(
                    CheckboxX(
                        cls="select_all",
                        x_model="selectAll",
                        _at_change="toggleAll()",
                    )
                ),
                Th("Page"),
                Th("Surah"),
                Th("Juz"),
                Th("Status"),
                Th("Mode & Reps"),
                Th(""),
            )
        ),
        Tbody(*map(render_row, ct)),
        x_data=select_all_checkbox_x_data(
            class_name="partial_rows", is_select_all="false"
        ),
        x_init="updateSelectAll()",
        id="filtered-table",
    )
    base = f"/profile/custom_status_update/{current_type}"
    if type_number is not None:
        base += f"/{type_number}"
    query = f"?status={status}&" if status else "?"
    query += f"title={title}&description={description}&filter_status={filter_status}"

    link = base + query

    def update_button(label, value, hx_select_id, hx_select_oob_id="", cls=""):
        return Button(
            label,
            hx_post=link,
            hx_select=hx_select_id,
            hx_target=hx_select_id,
            hx_swap="outerHTML",
            hx_select_oob=hx_select_oob_id,
            name="action",
            value=value,
            cls=("bg-green-600 text-white", cls),
        )

    return (
        Div(table, configure_modal),
        ModalTitle(
            "" if title == "" else f"{title} - Select Memorized Page",
            id="my-modal-title",
            hx_swap_oob="true",
        ),
        P(
            description,
            id="my-modal-description",
            hx_swap_oob="true",
            cls=TextPresets.muted_lg,
        ),
        Div(
            update_button(
                label="Update and Close",
                value="close",
                hx_select_id=f"#{current_type}-{type_number}",
                hx_select_oob_id=f"#stats_info",
                cls="uk-modal-close",
            ),
            update_button(
                label="Update and Stay",
                value="stay",
                hx_select_id="#filtered-table",
                hx_select_oob_id="#filtered-table",
            ),
            Button("Cancel", cls=("bg-red-600 text-white", "uk-modal-close")),
            id="my-modal-footer",
            hx_swap_oob="true",
            cls=("space-x-2", "space-y-2"),
        ),
    )


@profile_app.post("/update_status/{current_type}/{type_number}")
def profile_page_status_update(
    current_type: str,
    type_number: int,
    req: Request,
    auth,
    selected_memorized_status: str = "off",
):
    selected_memorized_status = selected_memorized_status == "on"
    qry = f"""SELECT items.id, items.surah_id, pages.page_number, pages.juz_number FROM items 
                          LEFT JOIN pages ON items.page_id = pages.id
                          WHERE items.active != 0;"""
    ct = db.q(qry)
    is_newly_memorized = selected_memorized_status == False
    grouped = group_by_type(ct, current_type, feild="id")

    for item_id in grouped[type_number]:
        current_item = hafizs_items(where=f"item_id = {item_id} and hafiz_id = {auth}")
        current_item = current_item[0]
        hafizs_items.update({"memorized": selected_memorized_status}, current_item.id)
    referer = req.headers.get("referer", "/")
    return RedirectResponse(referer, status_code=303)


@profile_app.post("/custom_status_update/{current_type}/{type_number}")
async def profile_page_custom_status_update(
    current_type: str,
    type_number: int,
    req: Request,
    title: str,
    description: str,
    filter_status: str,
    action: str,
    auth,
    status: str = None,
):
    form_data = await req.form()

    item_statuses = {}
    for key in form_data:
        if key.startswith("id-"):
            try:
                item_id = int(key.split("-")[1])
                status_val = form_data.get(key) == "1"
                item_statuses[item_id] = status_val
            except (IndexError, ValueError):
                continue

    for item_id, new_memorized_status in item_statuses.items():
        current_item_list = hafizs_items(
            where=f"item_id = {item_id} and hafiz_id = {auth}"
        )

        current_memorized_status = None
        hafiz_item_id = None
        if current_item_list:
            current_item = current_item_list[0]
            current_memorized_status = current_item.memorized
            hafiz_item_id = current_item.id

        if new_memorized_status == current_memorized_status:
            continue  # No change

        if hafiz_item_id is None:
            # It doesn't exist, so we should create it.
            hafizs_items.insert(
                item_id=item_id, hafiz_id=auth, memorized=new_memorized_status
            )
        else:
            hafizs_items.update({"memorized": new_memorized_status}, hafiz_item_id)

    query_string = f"?status={status}&" if status else "?"
    query_string += (
        f"title={title}&description={description}&filter_status={filter_status}"
    )
    stay_url = (
        f"/profile/custom_status_update/{current_type}/{type_number}{query_string}"
    )
    close_url = f"/profile/{current_type}{query_string}"
    if action == "stay":
        return RedirectResponse(stay_url, status_code=303)
    elif action == "close":
        return RedirectResponse(close_url, status_code=303)
    else:
        return Redirect(close_url)
