"""Home page helpers and view functions.

This module contains:
- Datewise summary table rendering
- Statistics table rendering
- Full Cycle progress tracking helpers
- Update logic for Full Cycle mode
"""

from collections import defaultdict
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


def get_today_vs_yesterday_stats(auth):
    """Calculate today vs yesterday page counts and comparison."""
    current_date = get_current_date(auth)
    today = current_date
    yesterday = sub_days_to_date(today, 1)

    today_count = get_page_count(revisions(where=f"revision_date = '{today}'"))
    yesterday_count = get_page_count(revisions(where=f"revision_date = '{yesterday}'"))

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

    def render_count(mode_code, revision_date):
        count, item_ids = get_revision_data(mode_code, revision_date)

        if count == 0:
            return "-"

        return create_count_link(count, item_ids)

    def render_stat_rows(current_mode_code):
        return Tr(
            Td(get_mode_name(current_mode_code)),
            Td(render_count(current_mode_code, today)),
            Td(render_count(current_mode_code, yesterday)),
            id=f"stat-row-{current_mode_code}",
        )

    return Table(
        Thead(
            Tr(
                Th("Modes"),
                Th("Today"),
                Th("Yesterday"),
            )
        ),
        Tbody(
            *map(render_stat_rows, mode_codes),
        ),
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
