"""Home page helpers and view functions.

This module contains:
- Datewise summary table rendering
- Statistics table rendering
- Full Cycle progress tracking helpers
- Update logic for Full Cycle mode
"""

from collections import defaultdict
import json
import pandas as pd
from fasthtml.common import *
from monsterui.all import *
from utils import (
    flatten_list,
    compact_format,
    sub_days_to_date,
    add_days_to_date,
    date_to_human_readable,
)
from app.common_function import (
    get_current_date,
    get_mode_name,
    get_page_count,
    get_page_description,
    create_count_link,
    get_hafizs_items,
    get_actual_interval,
)
from constants import *
from database import (
    db,
    hafizs_items,
    items,
    modes,
    revisions,
)


def get_pages_revised(auth, date: str) -> int:
    """Get page count for a specific date."""
    return get_page_count(revisions(where=f"revision_date = '{date}'"))


def get_today_vs_yesterday_stats(auth):
    """Calculate today vs yesterday page counts and comparison."""
    current_date = get_current_date(auth)
    today = current_date
    yesterday = sub_days_to_date(today, 1)

    today_count = get_pages_revised(auth, today)
    yesterday_count = get_pages_revised(auth, yesterday)

    difference = today_count - yesterday_count

    if difference > 0:
        direction = "up"
        arrow = "↑"
        color = "text-green-600"
    elif difference < 0:
        direction = "down"
        arrow = "↓"
        color = "text-red-600"
    else:
        direction = "same"
        arrow = "="
        color = "text-gray-600"

    return today_count, yesterday_count, difference, direction, arrow, color


def render_pages_revised_indicator(auth):
    """Render compact today vs yesterday pages indicator."""
    today, yesterday, _, _, arrow, color = get_today_vs_yesterday_stats(auth)

    return Span(
        Span(f"{today}", data_testid="pages-today", cls="font-semibold"),
        Span(" vs ", cls="text-gray-500 text-sm"),
        Span(f"{yesterday}", data_testid="pages-yesterday", cls="font-semibold"),
        Span(f" {arrow}", cls=f"{color} font-bold ml-1", data_testid="pages-indicator"),
        id="pages-revised-indicator",
        cls="text-sm whitespace-nowrap",
    )


def get_revision_data(mode_code: str, revision_date: str):
    """Returns the revision count and revision ID for a specific date and mode code."""
    records = revisions(
        where=f"mode_code = '{mode_code}' AND revision_date = '{revision_date}'"
    )
    rev_ids = ",".join(str(r.id) for r in records)
    count = get_page_count(records)
    return count, rev_ids


def split_page_range(page_range: str):
    """Split a page range string like '1-5' into (start, end) tuple."""
    start_id, end_id = (
        page_range.split("-") if "-" in page_range else [page_range, None]
    )
    start_id = int(start_id)
    end_id = int(end_id) if end_id else None
    return start_id, end_id


def datewise_summary_table(show=None, hafiz_id=None):
    """Render a table showing revisions grouped by date and mode."""
    hafiz_condition = f"AND revisions.hafiz_id = {hafiz_id}" if hafiz_id else ""

    qry = f"SELECT MIN(revision_date) AS earliest_date FROM {revisions}"
    qry = (qry + f" WHERE hafiz_id = {hafiz_id}") if hafiz_id else qry
    result = db.q(qry)
    earliest_date = result[0]["earliest_date"]
    current_date = get_current_date(hafiz_id)

    date_range = pd.date_range(
        start=(earliest_date or current_date), end=current_date, freq="D"
    )
    date_range = [date.strftime("%Y-%m-%d") for date in date_range][::-1]
    date_range = date_range[:show] if show else date_range

    # Bulk query: fetch all revisions for date range in single query
    if date_range:
        dates_str = ", ".join(f"'{d}'" for d in date_range)
        bulk_query = f"""
            SELECT revisions.id, revisions.item_id, revisions.revision_date, revisions.mode_code, items.page_id
            FROM {revisions}
            LEFT JOIN {items} ON revisions.item_id = items.id
            WHERE revisions.revision_date IN ({dates_str}) {hafiz_condition}
            ORDER BY revisions.revision_date DESC, revisions.mode_code ASC
        """
        all_revisions = db.q(bulk_query)
    else:
        all_revisions = []

    # Group revisions by date and mode
    revisions_by_date_mode = defaultdict(lambda: defaultdict(list))
    for rev in all_revisions:
        revisions_by_date_mode[rev["revision_date"]][rev["mode_code"]].append(rev)

    def _render_datewise_row(date):
        mode_data = revisions_by_date_mode.get(date, {})
        unique_modes = sorted(mode_data.keys())

        mode_with_ids_and_pages = []
        for mode_code in unique_modes:
            mode_with_ids_and_pages.append(
                {
                    "mode_code": mode_code,
                    "revision_data": mode_data[mode_code],
                }
            )

        def _render_pages_range(revisions_data: list):
            page_ranges = compact_format(sorted([r["page_id"] for r in revisions_data]))

            def _render_page(page):
                item_id = [
                    r["item_id"] for r in revisions_data if r["page_id"] == page
                ][0]
                return get_page_description(item_id=item_id, is_link=False)

            def get_ids_for_page_range(data, min_page, max_page=None):
                result = []
                for item in data:
                    page_id = item["page_id"]
                    if max_page is None:
                        if page_id == min_page:
                            result.append(item["id"])
                    else:
                        if min_page <= page_id <= max_page:
                            result.append(item["id"])
                return list(map(str, sorted(result)))

            ctn = []
            for page_range in page_ranges.split(","):
                start_page, end_page = split_page_range(page_range)
                if end_page:
                    range_desc = (
                        _render_page(start_page),
                        Span(" -> "),
                        _render_page(end_page),
                    )
                else:
                    range_desc = _render_page(start_page)

                ctn.append(
                    Span(
                        A(
                            *range_desc,
                            hx_get=f"/revision/bulk_edit?ids={','.join(get_ids_for_page_range(revisions_data, start_page, end_page))}",
                            hx_push_url="true",
                            hx_target="body",
                            cls=(AT.classic),
                        ),
                        cls="block",
                    )
                )

            return P(
                *ctn,
                cls="space-y-3",
            )

        if not mode_with_ids_and_pages:
            return [
                Tr(
                    Td(date_to_human_readable(date)),
                    Td("-"),
                    Td("-"),
                    Td("-"),
                    Td("-"),
                )
            ]

        rows = [
            Tr(
                *(
                    # Only add the date and total_count for the first row and use rowspan to expand them for the modes breakdown
                    (
                        Td(
                            date_to_human_readable(date),
                            rowspan=f"{len(mode_with_ids_and_pages)}",
                        ),
                        Td(
                            sum(
                                [
                                    len(i["revision_data"])
                                    for i in mode_with_ids_and_pages
                                ]
                            ),
                            rowspan=f"{len(mode_with_ids_and_pages)}",
                        ),
                    )
                    if mode_with_ids_and_pages[0]["mode_code"] == o["mode_code"]
                    else ()
                ),
                Td(get_mode_name(o["mode_code"])),
                Td(len(o["revision_data"])),
                Td(_render_pages_range(o["revision_data"])),
            )
            for o in mode_with_ids_and_pages
        ]
        return rows

    datewise_table = Div(
        Table(
            Thead(
                Tr(
                    Th("Date"),
                    Th("Total Count", cls="uk-table-shrink"),
                    Th("Mode"),
                    Th("Count"),
                    Th("Range"),
                )
            ),
            Tbody(*flatten_list(map(_render_datewise_row, date_range))),
        ),
        cls="uk-overflow-auto",
    )
    return datewise_table


def create_stat_table(auth):
    """Create the statistics table showing today/yesterday revision counts by mode."""
    current_date = get_current_date(auth)
    today = current_date
    yesterday = sub_days_to_date(today, 1)
    today_completed_count = get_page_count(
        revisions(where=f"revision_date = '{today}'")
    )
    yesterday_completed_count = get_page_count(
        revisions(where=f"revision_date = '{yesterday}'")
    )
    mode_codes = [mode.code for mode in modes()]

    def render_count(count, item_ids):
        if count == 0:
            return "-"
        return create_count_link(count, item_ids)

    def render_stat_rows(current_mode_code):
        today_count, today_ids = get_revision_data(current_mode_code, today)
        yesterday_count, yesterday_ids = get_revision_data(current_mode_code, yesterday)

        # Skip modes with no revisions on either day
        if today_count == 0 and yesterday_count == 0:
            return None

        return Tr(
            Td(get_mode_name(current_mode_code)),
            Td(render_count(today_count, today_ids)),
            Td(render_count(yesterday_count, yesterday_ids)),
            id=f"stat-row-{current_mode_code}",
        )

    rows = [row for row in map(render_stat_rows, mode_codes) if row is not None]

    return Table(
        Thead(
            Tr(
                Th("Modes"),
                Th("Today"),
                Th("Yesterday"),
            )
        ),
        Tbody(*rows),
        Tfoot(
            Tr(
                Td("Total"),
                Td(today_completed_count),
                Td(yesterday_completed_count),
                cls="[&>*]:font-bold",
                id="total_row",
            ),
        ),
    )


# Update logic

def update_hafiz_item_for_full_cycle(rev):
    """Update hafiz_items record when a Full Cycle revision is processed on close date."""
    hafiz_item_details = get_hafizs_items(rev.item_id)
    if hafiz_item_details is None:
        return  # Skip if no hafiz_items record exists

    currrent_date = get_current_date(rev.hafiz_id)
    # when a SRS page is revised in full-cycle mode, we need to move the next review of that page using the current next_interval
    if hafiz_item_details.mode_code == SRS_MODE_CODE:
        hafiz_item_details.next_review = add_days_to_date(
            currrent_date, hafiz_item_details.next_interval
        )

    hafiz_item_details.last_interval = get_actual_interval(rev.item_id)
    hafizs_items.update(hafiz_item_details)


# === Tabulator Components for Home Page ===


def _create_column_toggle_item(mode_code: str, column_name: str, label: str):
    """Create a single column toggle checkbox for the column visibility dropdown."""
    return Li(
        Label(
            Input(
                type="checkbox",
                cls="checkbox checkbox-sm",
                checked=True,
                id=f"col-toggle-{column_name}-{mode_code}",
                onchange=f"toggleColumn('{mode_code}', '{column_name}', this.checked)",
            ),
            f" {label}",
            cls="flex items-center gap-2 cursor-pointer",
        ),
    )


def _create_column_toggle_dropdown(mode_code: str, columns: list = None):
    """Create the column visibility toggle dropdown for Tabulator tables.

    Args:
        mode_code: The mode code for unique IDs
        columns: List of (column_name, label) tuples. Defaults to standard 3 columns.
    """
    if columns is None:
        columns = [("surah", "Surah"), ("juz", "Juz"), ("start_text", "Start Text")]

    toggle_items = [_create_column_toggle_item(mode_code, col, label) for col, label in columns]

    return Div(
        Div(
            Button("Columns ▾", cls="btn btn-sm btn-ghost", tabindex="0"),
            Ul(
                *toggle_items,
                cls="dropdown-content menu bg-base-100 rounded-box z-10 w-40 p-2 shadow",
                tabindex="0",
            ),
            cls="dropdown dropdown-end",
        ),
        cls="flex justify-end mb-2",
    )


def _create_bulk_bar_rating(mode_code: str):
    """Create bulk action bar with Good/Ok/Bad rating buttons."""
    return Div(
        Span(
            Span("0", id=f"bulk-count-{mode_code}", cls="font-bold"),
            " selected",
            cls="text-sm"
        ),
        Div(
            Button("Good", cls="btn btn-sm btn-success", onclick=f"handleBulkRate('{mode_code}', '1')"),
            Button("Ok", cls="btn btn-sm btn-warning", onclick=f"handleBulkRate('{mode_code}', '0')"),
            Button("Bad", cls="btn btn-sm btn-error", onclick=f"handleBulkRate('{mode_code}', '-1')"),
            cls="flex gap-2",
        ),
        id=f"bulk-bar-{mode_code}",
        cls="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-base-100 border rounded-lg shadow-lg px-4 py-3 flex items-center gap-6 z-50",
        style="display: none;"
    )


def _create_bulk_bar_nm():
    """Create bulk action bar for New Memorization with Mark button."""
    return Div(
        Span(
            Span("0", id="bulk-count-NM", cls="font-bold"),
            " selected",
            cls="text-sm"
        ),
        Button("Mark as Memorized", cls="btn btn-sm btn-success", onclick="handleBulkMark()"),
        id="bulk-bar-NM",
        cls="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-base-100 border rounded-lg shadow-lg px-4 py-3 flex items-center gap-6 z-50",
        style="display: none;"
    )


def render_mode_tabulator(mode_code: str, plan_id: int = None):
    """Render a Tabulator table for a mode tab on the home page.

    Uses external JS file (public/js/tabulator-init.js) for all table logic.

    Args:
        mode_code: The mode code (FC, SR, DR, WR, FR, MR)
        plan_id: Current plan ID (for FC mode)
    """
    table_id = f"mode-table-{mode_code}"

    # Configuration passed to external JS
    config = {
        "mode_code": mode_code,
        "table_id": table_id,
        "api_url": f"/api/mode/{mode_code}/items",
        "rate_url": f"/api/mode/{mode_code}/rate",
        "bulk_rate_url": f"/api/mode/{mode_code}/bulk_rate",
        "action_type": "rating",
        "has_juz_column": True,
        "placeholder": "No pages to review",
    }

    # Column visibility toggle dropdown
    column_toggle = _create_column_toggle_dropdown(mode_code)
    columns = ["surah", "juz", "start_text"]

    return Div(
        column_toggle,
        Div(id=table_id, cls="bg-base-100", data_testid=f"tabulator-{mode_code}"),
        _create_bulk_bar_rating(mode_code),
        Script(f"initTabulatorTable({json.dumps(config)});"),
        Script(f"syncColumnToggles('{mode_code}', {json.dumps(columns)});"),
        id=f"summary_table_{mode_code}",
    )


def render_nm_tabulator():
    """Render a Tabulator table for the New Memorization tab.

    Uses external JS file (public/js/tabulator-init.js) for all table logic.
    """
    mode_code = "NM"
    table_id = "mode-table-NM"

    # Configuration passed to external JS
    config = {
        "mode_code": mode_code,
        "table_id": table_id,
        "api_url": "/api/new_memorization/items",
        "toggle_url": "/api/new_memorization/toggle",
        "bulk_mark_url": "/api/new_memorization/bulk_mark",
        "action_type": "checkbox",
        "has_juz_column": False,
        "placeholder": "No pages available for memorization",
    }

    # Column visibility toggle dropdown (NM only has Surah and Start Text)
    nm_columns = [("surah", "Surah"), ("start_text", "Start Text")]
    column_toggle = _create_column_toggle_dropdown(mode_code, nm_columns)
    columns = ["surah", "start_text"]

    return Div(
        column_toggle,
        Div(id=table_id, cls="bg-base-100", data_testid=f"tabulator-{mode_code}"),
        _create_bulk_bar_nm(),
        Script(f"initTabulatorTable({json.dumps(config)});"),
        Script(f"syncColumnToggles('{mode_code}', {json.dumps(columns)});"),
        id=f"summary_table_{mode_code}",
    )


def render_report_tabulator():
    """Render a Tabulator table for the datewise summary report.

    Uses external JS file (public/js/tabulator-init.js) for all table logic.
    """
    table_id = "report-table"

    config = {
        "mode_code": "report",
        "table_id": table_id,
        "api_url": "/api/report",
        "type": "report",
    }

    return Div(
        Div(id=table_id, cls="bg-base-100", data_testid="tabulator-report"),
        Script(f"initTabulatorTable({json.dumps(config)});"),
    )
