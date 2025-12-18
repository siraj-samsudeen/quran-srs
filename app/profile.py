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
        memorized = bool(row["memorized"])
        # Hide mode when not memorized - mode is irrelevant in that state
        if not memorized:
            mode_name = "-"
            mode_icon = ""
        else:
            mode_name = get_mode_name(mode_code) if mode_code else "-"
            mode_icon = get_mode_icon(mode_code) if mode_code else ""

        # Calculate progress for graduatable modes (only when memorized)
        progress = "-"
        if memorized and mode_code in GRADUATABLE_MODES:
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


@profile_app.post("/api/bulk/set_status")
async def bulk_set_status(req: Request, auth):
    """Bulk set status for selected items. Handles both memorized flag and mode_code."""
    from starlette.responses import JSONResponse
    import json

    body = await req.body()
    payload = json.loads(body)
    item_ids = payload.get("item_ids", [])
    status = payload.get("status")

    if not item_ids or not status:
        return JSONResponse({"error": "Missing item_ids or status"}, status_code=400)

    current_date = get_current_date(auth)
    updated = 0

    for hafiz_item_id in item_ids:
        if hafiz_item_id is None:
            continue
        try:
            hafiz_item = hafizs_items[hafiz_item_id]
            if hafiz_item.hafiz_id != auth:
                continue

            # Map 5 statuses to database fields
            if status == "NOT_MEMORIZED":
                hafiz_item.memorized = False
                hafiz_item.mode_code = None  # Clear mode - not relevant when not memorized
                hafiz_item.next_review = None
                hafiz_item.next_interval = None
            elif status == "LEARNING":
                hafiz_item.memorized = True
                hafiz_item.mode_code = NEW_MEMORIZATION_MODE_CODE
                hafiz_item.next_review = None
                hafiz_item.next_interval = None
            elif status == "REPS":
                # Default to Daily Reps as starting point
                hafiz_item.memorized = True
                hafiz_item.mode_code = DAILY_REPS_MODE_CODE
                config = REP_MODES_CONFIG[DAILY_REPS_MODE_CODE]
                hafiz_item.next_interval = config["interval"]
                hafiz_item.next_review = add_days_to_date(current_date, config["interval"])
            elif status == "SOLID":
                hafiz_item.memorized = True
                hafiz_item.mode_code = FULL_CYCLE_MODE_CODE
                hafiz_item.next_review = None
                hafiz_item.next_interval = None
            elif status == "STRUGGLING":
                hafiz_item.memorized = True
                hafiz_item.mode_code = SRS_MODE_CODE
                hafiz_item.next_review = None
                hafiz_item.next_interval = None

            hafizs_items.update(hafiz_item)
            updated += 1
        except (NotFoundError, ValueError):
            continue

    return JSONResponse({"updated": updated})


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
                "Reps": "#f59e0b",            // amber - matches rep mode gradient
                "Solid": "#8b5cf6",           // purple
                "Struggling": "#ef4444"       // red
            }};

            // Mode color mapping - progression gradient for reps (yellow → orange)
            var modeColors = {{
                "New Memorization": "#22c55e", // green - matches Learning status
                "Daily Reps": "#eab308",       // yellow - earliest rep stage
                "Weekly Reps": "#f59e0b",      // amber - progressing
                "Fortnightly Reps": "#f97316", // orange - further along
                "Monthly Reps": "#ea580c",     // dark orange - almost graduated
                "Full cycle": "#8b5cf6",       // purple - matches Solid status
                "SRS - Variable Reps": "#ef4444" // red - matches Struggling status
            }};

            var table = new Tabulator("#profile-table", {{
                ajaxURL: "{api_url}",
                layout: "fitDataStretch",
                responsiveLayout: "hide",
                pagination: true,
                paginationSize: 25,
                paginationSizeSelector: [10, 25, 50, 100],
                paginationCounter: "rows",
                movableColumns: true,
                placeholder: "No pages found",
                selectable: true,
                selectableRangeMode: "click",
                columns: [
                    {{
                        title: "",
                        formatter: "rowSelection",
                        titleFormatter: "rowSelection",
                        headerSort: false,
                        width: 40,
                        hozAlign: "center",
                        headerHozAlign: "center",
                        cssClass: "tabulator-row-selection",
                        responsive: 0
                    }},
                    {{title: "Page", field: "page", sorter: "number", headerFilter: "number", width: 70,
                     responsive: 0,
                     formatter: function(cell) {{
                        return "<strong>" + cell.getValue() + "</strong>";
                    }}}},
                    {{title: "Juz", field: "juz", sorter: "number", headerFilter: "number", width: 60,
                     responsive: 3}},
                    {{title: "Surah", field: "surah", sorter: "string", headerFilter: "input", minWidth: 100,
                     responsive: 2}},
                    {{title: "Status", field: "status", sorter: "string", headerFilter: "list",
                     headerFilterParams: {{values: ["Not Memorized", "Learning", "Reps", "Solid", "Struggling"]}},
                     minWidth: 120, responsive: 0,
                     formatter: function(cell) {{
                        var data = cell.getRow().getData();
                        var color = statusColors[data.status] || "#6b7280";
                        return '<span style="background-color: ' + color + '20; color: ' + color + '; padding: 2px 8px; border-radius: 4px; font-size: 12px; white-space: nowrap;">' + data.status_icon + ' ' + data.status + '</span>';
                    }}}},
                    {{title: "Mode", field: "mode", sorter: "string", headerFilter: "list",
                     headerFilterParams: {{values: ["Daily Reps", "Weekly Reps", "Fortnightly Reps", "Monthly Reps", "Full cycle", "SRS - Variable Reps", "-"]}},
                     minWidth: 130, responsive: 1,
                     formatter: function(cell) {{
                        var data = cell.getRow().getData();
                        var color = modeColors[data.mode] || "#6b7280";
                        return '<span style="background-color: ' + color + '20; color: ' + color + '; padding: 2px 8px; border-radius: 4px; font-size: 12px; white-space: nowrap;">' + data.mode_icon + ' ' + data.mode + '</span>';
                    }}}},
                    {{title: "Progress", field: "progress", sorter: "string", headerFilter: false, width: 140,
                     responsive: 2,
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
                            '<span style="font-size: 11px; color: #6b7280; min-width: 40px;">' + value + '</span>' +
                            '</div>';
                    }}}},
                    {{title: "", field: "actions", headerSort: false, width: 45, hozAlign: "center",
                     responsive: 0,
                     formatter: function(cell) {{
                        var data = cell.getRow().getData();
                        // Only show config button for memorized items
                        if (!data.memorized) return "";
                        return '<button class="btn btn-ghost btn-xs config-btn" data-id="' + data.hafiz_item_id + '" title="Configure">⚙️</button>';
                    }},
                     cellClick: function(e, cell) {{
                        var btn = e.target.closest('.config-btn');
                        if (btn) {{
                            var hafizItemId = btn.dataset.id;
                            // Fetch modal content and show it
                            fetch('/profile/configure_reps/' + hafizItemId)
                                .then(function(response) {{ return response.text(); }})
                                .then(function(html) {{
                                    document.getElementById('config-modal-content').innerHTML = html;
                                    UIkit.modal('#config-modal').show();
                                }});
                        }}
                    }}}},
                ],
                initialSort: [
                    {{column: "page", dir: "asc"}}
                ],
            }});

            // Store table reference globally for other interactions
            window.profileTable = table;

            // Row click to open config modal (for mobile where gear icon is hidden)
            table.on("rowClick", function(e, row) {{
                // Don't open modal if clicking checkbox, config button, or within selection column
                if (e.target.closest('.tabulator-row-selection') ||
                    e.target.closest('.config-btn') ||
                    e.target.type === 'checkbox') {{
                    return;
                }}

                var data = row.getData();
                // Only open modal for memorized items
                if (!data.memorized) return;

                var hafizItemId = data.hafiz_item_id;
                fetch('/profile/configure_reps/' + hafizItemId)
                    .then(function(response) {{ return response.text(); }})
                    .then(function(html) {{
                        document.getElementById('config-modal-content').innerHTML = html;
                        UIkit.modal('#config-modal').show();
                    }});
            }});

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

            // Update selection count and show/hide bulk actions bar
            table.on("rowSelectionChanged", function(data, rows) {{
                var count = rows.length;
                var bulkBar = document.getElementById("bulk-actions-bar");

                if (bulkBar) {{
                    bulkBar.style.display = count > 0 ? "flex" : "none";
                    document.getElementById("bulk-count").textContent = count;
                }}

                // Store selected item IDs for bulk operations
                window.selectedItemIds = data.map(function(row) {{ return row.hafiz_item_id; }});
            }});

            // Bulk Set Status - handle clicks on dropdown menu items
            document.querySelectorAll(".status-menu-item").forEach(function(item) {{
                item.addEventListener("click", function() {{
                    var statusValue = this.dataset.status;
                    if (!statusValue || !window.selectedItemIds || window.selectedItemIds.length === 0) return;

                    fetch("/profile/api/bulk/set_status", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ item_ids: window.selectedItemIds, status: statusValue }})
                    }}).then(function(response) {{
                        if (response.ok) {{
                            table.setData("{api_url}");
                            table.deselectRow();
                        }}
                    }});

                    // Close the dropdown
                    document.activeElement.blur();
                }});
            }});
        }});
    """)

    # Floating bulk actions bar (hidden by default)
    bulk_actions_bar = Div(
        Div(
            Span(id="bulk-count", cls="font-bold"),
            " pages selected",
            cls="text-sm",
        ),
        # DaisyUI dropdown menu - 5 statuses only (not individual modes)
        Div(
            Div(
                "Set Status...",
                tabindex="0",
                role="button",
                cls="btn btn-sm btn-outline",
            ),
            Ul(
                Li(A("📚 Not Memorized", data_status="NOT_MEMORIZED", cls="status-menu-item")),
                Li(A("🌱 Learning", data_status="LEARNING", cls="status-menu-item")),
                Li(A("🏋️ Reps", data_status="REPS", cls="status-menu-item")),
                Li(A("💪 Solid", data_status="SOLID", cls="status-menu-item")),
                Li(A("😰 Struggling", data_status="STRUGGLING", cls="status-menu-item")),
                tabindex="0",
                cls="dropdown-content menu bg-base-100 rounded-box z-[100] w-52 p-2 shadow-lg border border-base-300",
            ),
            cls="dropdown dropdown-top dropdown-end",
        ),
        id="bulk-actions-bar",
        cls="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-base-100 border border-base-300 rounded-lg shadow-lg px-4 py-3 flex items-center gap-6 z-50",
        style="display: none;",
    )

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
                    cls="flex items-center gap-2",
                ),
                cls="mb-4",
            ),
            # Tabulator container
            Div(id="profile-table", cls="bg-base-100 rounded-lg shadow-sm"),
            # Floating bulk actions bar
            bulk_actions_bar,
            # Configuration modal (UK modal)
            Div(
                Div(
                    Div(
                        Button(cls="uk-modal-close-default", type="button", **{"uk-close": True}),
                        H3("Configure Page", cls="uk-modal-title"),
                        Div(id="config-modal-content"),
                        cls="uk-modal-header",
                    ),
                    cls="uk-modal-dialog uk-modal-body",
                ),
                id="config-modal",
                **{"uk-modal": True},
                cls="uk-modal",
            ),
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


