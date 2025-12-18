import json
from fasthtml.common import *
from monsterui.all import *
from utils import *
from constants import *
from app.common_function import *
from database import *


def create_revision_form(type, auth, backlink="/"):
    def _option(obj):
        name = obj.name
        id = obj.id
        return Option(
            f"{id} ({name})",
            value=id,
            # FIXME: Temp condition for selecting siraj, later it should be handled by sess
            # Another caviat is that siraj should be in the top of the list of users
            # or else the edit functionality will not work properly.
            selected=True if "siraj" in name.lower() else False,
        )

    additional_fields = (
        LabelInput(
            "Revision Date",
            name="revision_date",
            type="date",
            value=get_current_date(auth),
            cls="space-y-2 col-span-2",
        ),
    )

    return Form(
        Hidden(name="id"),
        Hidden(name="item_id"),
        Hidden(name="plan_id"),
        # Hide the User selection temporarily
        LabelSelect(
            *map(_option, hafizs()), label="Hafiz Id", name="hafiz_id", cls="hidden"
        ),
        *additional_fields,
        rating_radio(),
        Div(
            Button("Save", name="backlink", value=backlink, cls=ButtonT.primary),
            A(Button("Cancel", type="button", cls=ButtonT.secondary), href=backlink),
            cls="flex justify-around items-center w-full",
        ),
        action=f"/revision/{type}",
        method="POST",
    )


def render_revision_tabulator():
    """Render a Tabulator table for the revision list."""
    api_url = "/api/revisions"
    table_id = "revisions-table"

    tabulator_script = Script(f"""
        (function() {{
            function initTable() {{
                if (typeof Tabulator === 'undefined') {{
                    setTimeout(initTable, {TABULATOR_INIT_DELAY_MS});
                    return;
                }}

                // Load user preferences from localStorage
                var prefsKey = 'tabulator_prefs_revisions';
                var prefs = {{}};
                try {{
                    prefs = JSON.parse(localStorage.getItem(prefsKey)) || {{}};
                }} catch(e) {{}}

                // Rating display helper
                var ratingMap = {{"1": "✅ Good", "0": "😄 Ok", "-1": "❌ Bad"}};
                var ratingColors = {json.dumps(RATING_COLORS)};

                var table = new Tabulator("#{table_id}", {{
                    ajaxURL: "{api_url}",
                    ajaxResponse: function(url, params, response) {{
                        return response.items;
                    }},
                    layout: "fitDataStretch",
                    responsiveLayout: "hide",
                    pagination: true,
                    paginationSize: prefs.pageSize || (window.innerWidth < {TABULATOR_MOBILE_BREAKPOINT_PX} ? {TABULATOR_PAGE_SIZE_MOBILE} : {TABULATOR_PAGE_SIZE_DESKTOP}),
                    paginationSizeSelector: {json.dumps(TABULATOR_PAGE_SIZES)},
                    paginationCounter: "rows",
                    placeholder: "No revisions found",
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
                            responsive: 0
                        }},
                        {{
                            title: "Page",
                            field: "page",
                            sorter: "number",
                            headerFilter: "number",
                            width: 70,
                            responsive: 0,
                            formatter: function(cell) {{
                                var data = cell.getRow().getData();
                                return '<a href="/revision/edit/' + data.id + '" class="font-mono font-bold hover:underline">' + cell.getValue() + '</a>';
                            }}
                        }},
                        {{
                            title: "Surah",
                            field: "surah",
                            sorter: "string",
                            headerFilter: "input",
                            minWidth: 100,
                            responsive: 2,
                            visible: prefs.columns ? prefs.columns.surah !== false : true
                        }},
                        {{
                            title: "Mode",
                            field: "mode_code",
                            sorter: "string",
                            headerFilter: "list",
                            headerFilterParams: {{values: {{"": "All", "FC": "FC", "NM": "NM", "DR": "DR", "WR": "WR", "FR": "FR", "MR": "MR", "SR": "SR"}}}},
                            width: 70,
                            responsive: 0
                        }},
                        {{
                            title: "Plan",
                            field: "plan_id",
                            sorter: "number",
                            headerFilter: "number",
                            width: 70,
                            responsive: 2
                        }},
                        {{
                            title: "Rating",
                            field: "rating",
                            sorter: "number",
                            width: 90,
                            responsive: 0,
                            formatter: function(cell) {{
                                var rating = cell.getValue();
                                var text = ratingMap[rating.toString()] || "-";
                                var color = ratingColors[rating.toString()] || "";
                                if (color) {{
                                    cell.getElement().style.backgroundColor = color;
                                }}
                                return text;
                            }}
                        }},
                        {{
                            title: "Date",
                            field: "revision_date",
                            sorter: "date",
                            headerFilter: "input",
                            width: 110,
                            responsive: 1,
                            formatter: function(cell) {{
                                var date = cell.getValue();
                                if (!date) return "-";
                                var d = new Date(date);
                                return d.toLocaleDateString('en-US', {{month: 'short', day: 'numeric', year: 'numeric'}});
                            }}
                        }},
                        {{
                            title: "Action",
                            field: "id",
                            headerSort: false,
                            width: 80,
                            responsive: 0,
                            formatter: function(cell) {{
                                var id = cell.getValue();
                                return '<a href="#" class="delete-revision text-red-600 hover:underline" data-id="' + id + '">Delete</a>';
                            }}
                        }}
                    ],
                    initialSort: prefs.sort ? [prefs.sort] : [{{column: "id", dir: "desc"}}]
                }});

                // Save page size preference when changed
                table.on("pageSizeChanged", function(size) {{
                    var p = JSON.parse(localStorage.getItem(prefsKey)) || {{}};
                    p.pageSize = size;
                    localStorage.setItem(prefsKey, JSON.stringify(p));
                }});

                // Save sort preference when changed
                table.on("dataSorted", function(sorters) {{
                    if (sorters.length > 0) {{
                        var p = JSON.parse(localStorage.getItem(prefsKey)) || {{}};
                        p.sort = {{column: sorters[0].field, dir: sorters[0].dir}};
                        localStorage.setItem(prefsKey, JSON.stringify(p));
                    }}
                }});

                window.revisionsTable = table;

                // Update selection count
                table.on("rowSelectionChanged", function(data, rows) {{
                    var count = rows.length;
                    var bulkBar = document.getElementById("bulk-bar-revisions");
                    var countEl = document.getElementById("bulk-count-revisions");
                    if (bulkBar) {{
                        bulkBar.style.display = count > 0 ? "flex" : "none";
                        if (countEl) countEl.textContent = count;
                    }}
                    window.selectedRevisionIds = data.map(function(row) {{ return row.id; }});
                }});

                // Event delegation for delete links
                document.getElementById("{table_id}").addEventListener("click", function(e) {{
                    if (e.target.classList.contains("delete-revision")) {{
                        e.preventDefault();
                        var id = e.target.getAttribute("data-id");
                        if (confirm("Are you sure you want to delete this revision?")) {{
                            fetch("/revision/delete/" + id, {{method: "DELETE"}})
                                .then(function(r) {{
                                    if (r.ok) table.setData("{api_url}");
                                }});
                        }}
                    }}
                }});
            }}

            initTable();
        }})();
    """)

    # Bulk action bar
    bulk_bar = Div(
        Span(
            Span("0", id="bulk-count-revisions", cls="font-bold"),
            " selected",
            cls="text-sm"
        ),
        Div(
            A(
                Button("Bulk Edit", cls="btn btn-sm btn-primary"),
                id="bulk-edit-btn",
                onclick="""
                    if (window.selectedRevisionIds && window.selectedRevisionIds.length > 0) {
                        window.location.href = '/revision/bulk_edit?ids=' + window.selectedRevisionIds.join(',');
                    }
                """
            ),
            Button(
                "Bulk Delete",
                cls="btn btn-sm btn-error",
                onclick="""
                    if (!window.selectedRevisionIds || window.selectedRevisionIds.length === 0) return;
                    if (!confirm('Are you sure you want to delete these revisions?')) return;
                    fetch('/revision/', {
                        method: 'DELETE',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ids: window.selectedRevisionIds})
                    }).then(function(r) {
                        if (r.ok) window.revisionsTable.setData('/api/revisions');
                    });
                """
            ),
            cls="flex gap-2",
        ),
        id="bulk-bar-revisions",
        cls="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-base-100 border rounded-lg shadow-lg px-4 py-3 flex items-center gap-6 z-50",
        style="display: none;"
    )

    # Export button
    export_btn = A(
        Button("Export", type="button", cls="btn btn-sm btn-ghost"),
        href="tables/revisions/export",
    )

    return Div(
        Div(
            export_btn,
            cls="flex justify-end mb-2",
        ),
        Div(id=table_id, cls="bg-base-100"),
        bulk_bar,
        tabulator_script,
    )


def render_revision_table(auth, idx: int | None = 1):
    return main_area(
        render_revision_tabulator(),
        active="Revision",
        auth=auth,
    )
