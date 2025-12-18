import json
from fasthtml.common import *
from monsterui.all import *
from utils import *
from constants import *
from app.common_function import *
from database import *


page_details_app, rt = create_app_with_auth()


def render_page_details_tabulator():
    """Render a Tabulator table for the page details list."""
    api_url = "/api/page_details"
    table_id = "page-details-table"

    tabulator_script = Script(f"""
        (function() {{
            function initTable() {{
                if (typeof Tabulator === 'undefined') {{
                    setTimeout(initTable, {TABULATOR_INIT_DELAY_MS});
                    return;
                }}

                var prefsKey = 'tabulator_prefs_page_details';
                var prefs = {{}};
                try {{ prefs = JSON.parse(localStorage.getItem(prefsKey)) || {{}}; }} catch(e) {{}}

                var modeNames = {{
                    'FC': 'Full Cycle',
                    'SR': 'SRS',
                    'DR': 'Daily',
                    'WR': 'Weekly',
                    'FR': 'Fortnightly',
                    'MR': 'Monthly',
                    'NM': 'New Mem'
                }};

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
                    placeholder: "No pages found",
                    columns: [
                        {{
                            title: "Page",
                            field: "page",
                            sorter: "number",
                            headerFilter: "number",
                            width: 70,
                            responsive: 0,
                            formatter: function(cell) {{
                                var data = cell.getRow().getData();
                                return '<a href="/page_details/' + data.item_id + '" class="font-mono font-bold hover:underline">' + cell.getValue() + '</a>';
                            }}
                        }},
                        {{
                            title: "Surah",
                            field: "surah",
                            sorter: "string",
                            headerFilter: "input",
                            minWidth: 100,
                            responsive: 2
                        }},
                        {{
                            title: "Mode",
                            field: "mode_code",
                            width: 80,
                            responsive: 0,
                            formatter: function(cell) {{
                                var code = cell.getValue();
                                return modeNames[code] || code;
                            }}
                        }},
                        {{
                            title: "FC",
                            field: "fc_count",
                            sorter: "number",
                            width: 50,
                            hozAlign: "center",
                            responsive: 1
                        }},
                        {{
                            title: "SR",
                            field: "sr_count",
                            sorter: "number",
                            width: 50,
                            hozAlign: "center",
                            responsive: 1
                        }},
                        {{
                            title: "DR",
                            field: "dr_count",
                            sorter: "number",
                            width: 50,
                            hozAlign: "center",
                            responsive: 2
                        }},
                        {{
                            title: "WR",
                            field: "wr_count",
                            sorter: "number",
                            width: 50,
                            hozAlign: "center",
                            responsive: 2
                        }},
                        {{
                            title: "FR",
                            field: "fr_count",
                            sorter: "number",
                            width: 50,
                            hozAlign: "center",
                            responsive: 2
                        }},
                        {{
                            title: "MR",
                            field: "mr_count",
                            sorter: "number",
                            width: 50,
                            hozAlign: "center",
                            responsive: 2
                        }},
                        {{
                            title: "Total",
                            field: "total_revisions",
                            sorter: "number",
                            width: 60,
                            hozAlign: "center",
                            responsive: 0
                        }},
                        {{
                            title: "",
                            field: "item_id",
                            headerSort: false,
                            width: 80,
                            responsive: 0,
                            formatter: function(cell) {{
                                var id = cell.getValue();
                                return '<a href="/page_details/' + id + '" class="link link-primary text-sm">Details →</a>';
                            }}
                        }}
                    ],
                    initialSort: prefs.sort ? [prefs.sort] : [{{column: "page", dir: "asc"}}]
                }});

                table.on("pageSizeChanged", function(size) {{
                    var p = JSON.parse(localStorage.getItem(prefsKey)) || {{}};
                    p.pageSize = size;
                    localStorage.setItem(prefsKey, JSON.stringify(p));
                }});

                table.on("dataSorted", function(sorters) {{
                    if (sorters.length > 0) {{
                        var p = JSON.parse(localStorage.getItem(prefsKey)) || {{}};
                        p.sort = {{column: sorters[0].field, dir: sorters[0].dir}};
                        localStorage.setItem(prefsKey, JSON.stringify(p));
                    }}
                }});

                window.pageDetailsTable = table;
            }}

            initTable();
        }})();
    """)

    return Div(
        Div(id=table_id, cls="bg-base-100"),
        tabulator_script,
    )


def render_page_history_tabulator(item_id: int):
    """Render a Tabulator table for a page's revision history."""
    api_url = f"/api/page_details/{item_id}/history"
    table_id = f"page-history-table-{item_id}"

    tabulator_script = Script(f"""
        (function() {{
            function initTable() {{
                if (typeof Tabulator === 'undefined') {{
                    setTimeout(initTable, {TABULATOR_INIT_DELAY_MS});
                    return;
                }}

                var ratingMap = {{"1": "Good", "0": "Ok", "-1": "Bad"}};
                var ratingColors = {json.dumps(RATING_COLORS)};

                var table = new Tabulator("#{table_id}", {{
                    ajaxURL: "{api_url}",
                    ajaxResponse: function(url, params, response) {{
                        return response.items;
                    }},
                    layout: "fitDataStretch",
                    responsiveLayout: "hide",
                    pagination: true,
                    paginationSize: {TABULATOR_PAGE_SIZE_DESKTOP},
                    paginationSizeSelector: {json.dumps(TABULATOR_PAGE_SIZES)},
                    paginationCounter: "rows",
                    placeholder: "No revision history",
                    columns: [
                        {{
                            title: "#",
                            field: "num",
                            width: 50,
                            hozAlign: "center",
                            responsive: 0
                        }},
                        {{
                            title: "Date",
                            field: "date",
                            width: 120,
                            responsive: 0,
                            formatter: function(cell) {{
                                var date = cell.getValue();
                                if (!date) return "-";
                                var d = new Date(date);
                                return d.toLocaleDateString('en-US', {{month: 'short', day: 'numeric', year: 'numeric'}});
                            }}
                        }},
                        {{
                            title: "Rating",
                            field: "rating",
                            width: 80,
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
                            title: "Mode",
                            field: "mode_name",
                            width: 100,
                            responsive: 1
                        }},
                        {{
                            title: "Interval",
                            field: "interval_since_last",
                            width: 80,
                            hozAlign: "center",
                            responsive: 2,
                            formatter: function(cell) {{
                                var val = cell.getValue();
                                return val !== null ? val + "d" : "-";
                            }}
                        }},
                        {{
                            title: "Next Int.",
                            field: "next_interval",
                            width: 80,
                            hozAlign: "center",
                            responsive: 2,
                            formatter: function(cell) {{
                                var val = cell.getValue();
                                return val !== null ? val + "d" : "-";
                            }}
                        }}
                    ],
                    initialSort: [{{column: "num", dir: "desc"}}]
                }});

                window.pageHistoryTable = table;
            }}

            initTable();
        }})();
    """)

    return Div(
        Div(id=table_id, cls="bg-base-100"),
        tabulator_script,
    )


@page_details_app.get("/")
def page_details_view(auth):
    return main_area(
        Title("Page Details"),
        render_page_details_tabulator(),
        active="Page Details",
        auth=auth,
    )


@page_details_app.get("/{item_id}")
def display_page_level_details(auth, item_id: int):
    # Prevent editing description for inactive items
    is_active_item = bool(items(where=f"id = {item_id} and active != 0"))
    if not is_active_item:
        return Redirect("/page_details")

    mode_code_list, _mode_name_list = get_mode_name_and_code()

    # Avoid showing nav buttons (if the page has is no revision)
    rev_data = revisions(where=f"item_id = {item_id}")
    is_show_nav_btn = bool(rev_data)

    def _render_row(data, columns):
        tds = []
        for col in columns:
            value = data.get(col, "")
            if col == "rating":
                value = RATING_MAP.get(str(value), value)
            if col == "revision_date":
                value = date_to_human_readable(str(value))
            tds.append(Td(value))
        return Tr(*tds)

    def make_mode_title_for_table(mode_code):
        try:
            mode_details = modes[mode_code]
            mode_name, mode_description = (mode_details.name, mode_details.description)
        except NotFoundError:
            mode_name, mode_description = ("", "")
        return H2(mode_name, Subtitle(mode_description))

    is_item_exist = items(where=f"id = {item_id}")
    if is_item_exist:
        page_description = get_page_description(item_id, is_bold=False, is_link=False)
        juz = f"Juz {get_juz_name(item_id=item_id)}"
    else:
        Redirect("/page_details")

    if not mode_code_list:
        memorization_summary = ""
    else:
        ctn = []

        first_revision_data = revisions(
            where=f"item_id = {item_id} and hafiz_id = {auth} and mode_code IN ({", ".join([repr(code) for code in mode_code_list])})",
            order_by="revision_date ASC",
            limit=1,
        )
        if first_revision_data:
            first_revision = first_revision_data[0]
            first_memorized_date = (
                first_revision.revision_date
                if first_revision
                else Redirect("/page_details")
            )
            first_memorized_mode_code = (
                first_revision.mode_code
                if first_revision
                else Redirect("/page_details")
            )
            first_memorized_mode_name, description = make_mode_title_for_table(
                first_memorized_mode_code
            )
            ctn.append(
                P(
                    "This page was added on: ",
                    Span(Strong(date_to_human_readable(first_memorized_date))),
                    " under ",
                    Span(Strong(first_memorized_mode_name)),
                )
            )

            hafiz_items_details = get_hafizs_items(item_id)
            if hafiz_items_details:
                stat_columns = [
                    "srs_start_date",
                    "last_review",
                    "next_review",
                    "memorized",
                    "mode_code",
                    "last_interval",
                    "actual_interval",
                    "next_interval",
                ]
                rename_columns = {
                    "mode_code": "current_mode",
                    "last_interval": "previous_interval",
                }

                # Table View
                def render_stats(col_name: str):
                    if col_name == "actual_interval":
                        value = get_actual_interval(item_id)
                    else:
                        value = hafiz_items_details.__dict__[col_name]
                        if col_name == "mode_code":
                            value = get_mode_name(value)
                        elif col_name == "memorized":
                            value = "Yes" if value else "No"
                        else:
                            value = str(value).capitalize()
                    return Tr(
                        Th(destandardize_text(rename_columns.get(col_name, col_name))),
                        Td(value),
                    )

                stats_table = Table(
                    Tbody(*map(render_stats, stat_columns)),
                    cls=(TableT.sm, TableT.responsive, TableT.justify),
                )
                ctn.append(
                    Div(
                        A(
                            "Refresh stats",
                            hx_get="/hafiz/update_stats_column",
                            hx_vals={"item_id": item_id},
                            hx_target="body",
                            cls=AT.classic,
                        ),
                        stats_table,
                        cls="max-w-80 space-y-1",
                    )
                )

        if ctn:
            memorization_summary = Div(H2("Summary"), Div(*ctn, cls="space-y-3"))
        else:
            memorization_summary = ""

    def build_revision_query(mode_codes, row_alias):
        return f"""
            SELECT
                ROW_NUMBER() OVER (ORDER BY revision_date ASC) AS {row_alias},
                revision_date,
                rating,
                modes.name AS mode_name,
                next_interval,
            CASE
                WHEN LAG(revision_date) OVER (ORDER BY revision_date) IS NULL THEN ''
                ELSE CAST(
                    JULIANDAY(revision_date) - JULIANDAY(LAG(revision_date) OVER (ORDER BY revision_date))
                    AS INTEGER
                )
            END AS intervals_since_last_revision
            FROM revisions
            JOIN modes ON revisions.mode_code = modes.code
            WHERE item_id = {item_id} AND hafiz_id = {auth} AND revisions.mode_code IN ({", ".join(repr(code) for code in mode_codes)})
            ORDER BY revision_date ASC;
        """

    def create_mode_table(mode_codes):
        query = build_revision_query(mode_codes, "s_no")
        data = db.q(query)
        # determine table visibility
        has_data = len(data) > 0
        # This is to render the srs table different from others
        cols = [
            "s_no",
            "revision_date",
            "rating",
            "mode_name",
            "intervals_since_last_revision",
            "next_interval",
        ]

        table = Div(
            Table(
                Thead(*(Th(col.replace("_", " ").title()) for col in cols)),
                Tbody(*[_render_row(row, cols) for row in data]),
            )
        )

        return has_data, table

    has_summary_data, summary_table = create_mode_table(mode_code_list)

    def create_nav_button(item_id, arrow, show_nav):
        return A(
            arrow if item_id and show_nav else "",
            href=f"/page_details/{item_id}" if item_id is not None else "#",
            cls="uk-button uk-button-default",
        )

    def get_prev_next_item_ids(current_item_id):
        def build_nav_query(operator, sort_order):
            return f"""SELECT items.id, pages.page_number FROM revisions
                       LEFT JOIN items ON revisions.item_id = items.id
                       LEFT JOIN pages ON items.page_id = pages.id
                       WHERE revisions.hafiz_id = {auth} AND items.active != 0 AND items.id {operator} {current_item_id}
                       ORDER BY items.id {sort_order} LIMIT 1;"""

        prev_result = db.q(build_nav_query("<", "DESC"))
        next_result = db.q(build_nav_query(">", "ASC"))
        prev_id = prev_result[0]["id"] if prev_result else None
        next_id = next_result[0]["id"] if next_result else None
        return prev_id, next_id

    prev_id, next_id = get_prev_next_item_ids(item_id)
    prev_pg = create_nav_button(prev_id, "⬅️", is_show_nav_btn)
    next_pg = create_nav_button(next_id, "➡️", is_show_nav_btn)

    item_details = items[item_id]
    description = item_details.description
    start_text = item_details.start_text

    edit_description = DivVStacked(
        Table(
            Tr(
                Td("Description: "),
                Td(description, id="description"),
            ),
            Tr(
                Td("Start Text: "),
                Td(start_text, id="start_text", cls=TextT.lg),
            ),
            Tr(
                Td(
                    Div(
                        Button(
                            "Edit",
                            hx_get=f"/page_details/edit/{item_id}",
                            cls=(ButtonT.default, ButtonT.xs),
                        ),
                        id="btns",
                    ),
                    colspan="2",
                ),
                cls="text-center",
            ),
            cls="max-w-xs",
            id="item_description_table",
        ),
    )
    return main_area(
        Div(
            Div(
                DivFullySpaced(
                    prev_pg,
                    Div(
                        DivVStacked(
                            H1(page_description, cls="uk-text-center"),
                        ),
                        id="page-details-header",
                    ),
                    next_pg,
                ),
                Subtitle(Strong(juz), cls="uk-text-center"),
                edit_description,
                cls="space-y-8",
            ),
            Div(
                memorization_summary,
                (
                    Div(H2("Revision History"), render_page_history_tabulator(item_id))
                    if has_summary_data
                    else None
                ),
                cls="space-y-6",
            ),
        ),
        active="Page Details",
        auth=auth,
    )


@page_details_app.get("/edit/{item_id}")
def page_description_edit_form(item_id: int):
    item_details = items[item_id]
    description = item_details.description
    start_text = item_details.start_text
    description_field = (
        LabelInput(
            "Description: ",
            name="description",
            value=description,
            id="description",
            hx_swap_oob="true",
            placeholder=description,
        ),
    )
    start_text_field = (
        LabelInput(
            "Start Text: ",
            name="start_text",
            value=start_text,
            id="start_text",
            hx_swap_oob="true",
            placeholder=start_text,
            cls=TextT.lg,
        ),
    )
    buttons = Div(
        Button(
            "Update",
            hx_put=f"/admin/tables/items/{item_id}",
            hx_vals={"redirect_link": f"/page_details/{item_id}"},
            hx_target="#item_description_table",
            hx_select="#item_description_table",
            hx_select_oob="#page-details-header",
            hx_include="#description, #start_text",
            cls=(ButtonT.default, ButtonT.xs),
        ),
        Button(
            "Cancel",
            type="button",
            hx_get=f"/page_details/{item_id}",
            hx_target="#item_description_table",
            hx_select="#item_description_table",
            cls=(ButtonT.default, ButtonT.xs),
        ),
        cls="space-x-4",
        hx_swap_oob="true",
        id="btns",
    )

    return description_field, start_text_field, buttons
