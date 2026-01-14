"""Home page helpers and view functions.

This module contains:
- Datewise summary table rendering
- Statistics table rendering
- Full Cycle progress tracking helpers
- Update logic for Full Cycle mode
- Summary table rendering for home page tabs
- Mode filter predicates
"""

from collections import defaultdict
import pandas as pd
from fasthtml.common import *
import fasthtml.common as fh
from monsterui.all import *
from utils import (
    flatten_list,
    compact_format,
    sub_days_to_date,
    add_days_to_date,
    date_to_human_readable,
    day_diff,
    format_number,
)
from app.common_model import (
    get_current_date,
    get_current_plan_id,
    get_full_review_item_ids,
    get_last_added_full_cycle_page,
    get_hafizs_items,
    get_actual_interval,
    get_earliest_revision_date,
    get_datewise_revisions,
    get_mode_specific_hafizs_items,
    get_mode_name,
    get_page_number,
    get_surah_name,
    get_juz_name,
    get_item_page_portion,
    get_page_part_info,
    get_page_count,
)
from app.components.forms import (
    RatingDropdown,
    BulkSelectCheckbox,
    SelectAllCheckbox,
)
from app.components.tables import (
    SurahHeader,
    PageNumberCell,
    StartTextCell,
)
from app.components.display import (
    PageDescription,
    CountLink,
    TrendIndicator,
)
from app.components.layout import BulkActionBar
from constants import *
from database import (
    hafizs_items,
    items,
    modes,
    pages,
    revisions,
    surahs,
)


def get_today_vs_yesterday_stats(auth):
    """Calculate today vs yesterday page counts and comparison."""
    current_date = get_current_date(auth)
    today = current_date
    yesterday = sub_days_to_date(today, 1)

    today_count = get_page_count(revisions(where=f"revision_date = '{today}'"))
    yesterday_count = get_page_count(revisions(where=f"revision_date = '{yesterday}'"))

    return today_count, yesterday_count


def render_pages_revised_indicator(auth):
    """Render compact today vs yesterday pages indicator."""
    today, yesterday = get_today_vs_yesterday_stats(auth)
    return TrendIndicator(today, yesterday)


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
    earliest_date = get_earliest_revision_date(hafiz_id)
    current_date = get_current_date(hafiz_id)

    date_range = pd.date_range(
        start=(earliest_date or current_date), end=current_date, freq="D"
    )
    date_range = [date.strftime("%Y-%m-%d") for date in date_range][::-1]
    date_range = date_range[:show] if show else date_range

    # Bulk query: fetch all revisions for date range in single query
    all_revisions = get_datewise_revisions(date_range, hafiz_id)

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
                return PageDescription(item_id=item_id, is_link=False)

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
        return CountLink(count, item_ids)

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


# === Summary Table Functions ===


def row_background_color(rating):
    bg_color = ""
    if rating == 1:
        bg_color = "bg-green-100"
    elif rating == 0:
        bg_color = "bg-yellow-50"
    elif rating == -1:
        bg_color = "bg-red-50"
    return bg_color


def get_mode_condition(mode_code: str):
    mode_code_mapping = {
        FULL_CYCLE_MODE_CODE: [f"'{FULL_CYCLE_MODE_CODE}'", f"'{SRS_MODE_CODE}'"],
    }
    retrieved_mode_codes = mode_code_mapping.get(mode_code)
    if retrieved_mode_codes is None:
        mode_condition = f"mode_code = '{mode_code}'"
    else:
        mode_condition = f"mode_code IN ({', '.join(retrieved_mode_codes)})"
    return mode_condition


def render_range_row(records, current_date=None, mode_code=None, plan_id=None, hide_start_text=False, loved=False):
    """Render a single table row for an item in the summary table."""
    item_id = records["item"].id
    rating = records["revision"].rating if records["revision"] else None
    row_id = f"row-{mode_code}-{item_id}"

    if rating is None:
        action_link_attr = {"hx_post": f"/add/{item_id}"}
    else:
        rev_id = records["revision"].id
        action_link_attr = {"hx_put": f"/edit/{rev_id}"}

    vals_dict = {"date": current_date, "mode_code": mode_code, "item_id": item_id}
    if plan_id:
        vals_dict["plan_id"] = plan_id

    rating_dropdown_input = RatingDropdown(
        rating=rating,
        id=f"rev-{item_id}",
        data_testid=f"rating-{item_id}",
        **action_link_attr,
        hx_vals=vals_dict,
        hx_trigger="change",
        hx_target=f"#{row_id}",
        hx_swap="outerHTML",
    )

    checkbox_cell = Td(BulkSelectCheckbox(item_id), cls="w-8") if rating is None else Td(cls="w-8")

    heart_icon = Span(
        "❤️" if loved else "🤍",
        cls="cursor-pointer text-sm",
        hx_post=f"/toggle_love/{item_id}",
        hx_target=f"#{row_id}",
        hx_swap="outerHTML",
        hx_vals={"mode_code": mode_code, "date": current_date, "plan_id": plan_id or ""},
        title="Toggle favorite",
    )

    return Tr(
        checkbox_cell,
        PageNumberCell(item_id),
        StartTextCell(records["item"].start_text, hide_text=hide_start_text),
        Td(
            Div(
                heart_icon,
                Form(
                    rating_dropdown_input,
                    Hidden(name="item_id", value=item_id),
                ),
                cls="flex items-center gap-2",
            ),
        ),
        id=row_id,
        cls=row_background_color(rating),
    )


def render_bulk_action_bar(mode_code, current_date, plan_id):
    """Render a sticky bulk action bar for applying ratings to selected items."""
    plan_id_val = plan_id or ""

    def bulk_button(rating_value, label, btn_cls):
        return Button(
            label,
            hx_post="/bulk_rate",
            hx_vals={"rating": rating_value, "mode_code": mode_code, "date": current_date, "plan_id": plan_id_val},
            hx_include=f"#{mode_code}_tbody [name='item_ids']:checked",
            hx_target=f"#summary_table_{mode_code}",
            hx_swap="outerHTML",
            **{"@click": "count = 0"},
            cls=(btn_cls, "px-4 py-2"),
        )

    # Use SelectAllCheckbox component
    select_all_checkbox = Div(
        SelectAllCheckbox(),
        Span("Select All", cls="text-sm ml-2", x_show="count < $root.querySelectorAll('.bulk-select-checkbox').length"),
        Span("Clear All", cls="text-sm ml-2", x_show="count === $root.querySelectorAll('.bulk-select-checkbox').length"),
        Span("|", cls="text-gray-300 mx-2"),
        Span(x_text="count", cls="font-bold"),
        cls="flex items-center",
    )

    spacer = Div(cls="h-16", x_show="count > 0", style="display: none")

    cancel_button = Button(
        "✕",
        cls="btn btn-ghost btn-sm",
        **{"@click": "$root.querySelectorAll('.bulk-select-checkbox').forEach(cb => cb.checked = false); count = 0"},
        title="Cancel selection",
    )

    # Use BulkActionBar component
    bar = BulkActionBar(
        id=f"bulk-bar-{mode_code}",
        children=[
            select_all_checkbox,
            Div(
                bulk_button(1, "Good", ButtonT.primary),
                bulk_button(0, "Ok", ButtonT.secondary),
                bulk_button(-1, "Bad", ButtonT.destructive),
                cancel_button,
                cls="flex gap-2 items-center",
            ),
        ]
    )

    return Div(spacer, bar)


def render_summary_table(auth, mode_code, item_ids, is_plan_finished, offset=0, items_per_page=None, show_loved_only=False, rows_only=False):
    current_date = get_current_date(auth)
    plan_id = get_current_plan_id()

    total_items = len(item_ids)

    if item_ids:
        total_page_equivalents = sum(get_item_page_portion(item_id) for item_id in item_ids)
    else:
        total_page_equivalents = 0

    if items_per_page and items_per_page > 0:
        start_idx = offset
        end_idx = offset + items_per_page
        paginated_item_ids = item_ids[start_idx:end_idx]
        has_more = end_idx < total_items
    else:
        paginated_item_ids = item_ids
        has_more = False

    plan_condition = f"AND plan_id = {plan_id}" if plan_id else ""
    if paginated_item_ids:
        today_revisions = revisions(
            where=f"revision_date = '{current_date}' AND item_id IN ({', '.join(map(str, paginated_item_ids))}) AND {get_mode_condition(mode_code)} {plan_condition}"
        )
    else:
        today_revisions = []
    revisions_lookup = {rev.item_id: rev for rev in today_revisions}

    if paginated_item_ids:
        hafiz_items_data = hafizs_items(
            where=f"item_id IN ({', '.join(map(str, paginated_item_ids))})"
        )
    else:
        hafiz_items_data = []
    loved_lookup = {hi.item_id: bool(hi.loved) for hi in hafiz_items_data}

    items_with_revisions = [
        {"item": items[item_id], "revision": revisions_lookup.get(item_id)}
        for item_id in paginated_item_ids
    ]

    body_rows = []
    current_surah_id = None
    prev_page_id = None
    for records in items_with_revisions:
        item = records["item"]
        if item.surah_id != current_surah_id:
            current_surah_id = item.surah_id
            juz_number = get_juz_name(item_id=item.id)
            body_rows.append(SurahHeader(current_surah_id, juz_number))
            prev_page_id = None
        is_consecutive = prev_page_id is not None and item.page_id == prev_page_id + 1
        is_loved = loved_lookup.get(item.id, False)
        row = render_range_row(records, current_date, mode_code, plan_id, hide_start_text=is_consecutive, loved=is_loved)
        body_rows.append(row)
        prev_page_id = item.page_id

    if has_more and body_rows:
        for i in range(len(body_rows) - 1, -1, -1):
            row = body_rows[i]
            if hasattr(row, "attrs") and "surah-header" not in row.attrs.get("cls", ""):
                next_offset = offset + items_per_page
                row.attrs.update({
                    "hx-get": f"/page/{mode_code}/more?offset={next_offset}&show_loved_only={'true' if show_loved_only else 'false'}",
                    "hx-trigger": "revealed",
                    "hx-swap": "afterend",
                })
                break

    if rows_only:
        return tuple(body_rows)

    if not body_rows:
        body_rows = [
            Tr(
                Td(
                    "No pages to review on this page.",
                    colspan=4,
                    cls="text-center text-gray-500 py-4",
                )
            )
        ]

    if is_plan_finished:
        body_rows.append(
            Tr(
                Td(
                    Span(
                        "Plan is finished, mark pages in ",
                        A("Profile", href="/profile", cls=AT.classic),
                        " to continue, or a new plan will be created",
                    ),
                    colspan=4,
                    cls="text-center text-lg",
                )
            )
        )

    bulk_bar = render_bulk_action_bar(mode_code, current_date, plan_id)

    filter_toggle = None
    if mode_code == SRS_MODE_CODE:
        filter_toggle = Div(
            Button(
                "❤️ Loved Only" if not show_loved_only else "📋 Show All",
                hx_get=f"/page/{mode_code}?offset=0&show_loved_only={'false' if show_loved_only else 'true'}",
                hx_target=f"#summary_table_{mode_code}",
                hx_swap="outerHTML",
                cls=f"btn btn-sm {'btn-primary' if show_loved_only else 'btn-ghost'}",
                data_testid=f"loved-filter-toggle-{mode_code}",
            ),
            cls="flex justify-end mb-2",
        )

    table_content = []
    if filter_toggle:
        table_content.append(filter_toggle)

    table_content.append(
        Table(
            Tbody(*body_rows, id=f"{mode_code}_tbody"),
            cls=(TableT.middle, TableT.divider, TableT.sm),
        )
    )

    table_content.append(bulk_bar)

    table = Div(
        *table_content,
        id=f"summary_table_{mode_code}",
        x_data="{ count: 0 }",
    )
    return (mode_code, table)


# === Mode Filter Predicates ===


def _is_review_due(item: dict, current_date: str) -> bool:
    """Check if item is due for review today or overdue."""
    return day_diff(item["next_review"], current_date) >= 0


def _is_reviewed_today(item: dict, current_date: str) -> bool:
    """Check if item was reviewed today."""
    return item["last_review"] == current_date


def _has_memorized(item: dict) -> bool:
    """Check if item is marked as memorized."""
    return item["memorized"]


def _has_revisions_in_mode(item: dict) -> bool:
    """Check if item has any revisions in its current mode."""
    item_id = item["item_id"]
    mode_code = item["mode_code"]
    return bool(revisions(where=f"item_id = {item_id} AND mode_code = '{mode_code}'"))


def _has_revisions_today_in_mode(item: dict, current_date: str) -> bool:
    """Check if item has revisions in its current mode today."""
    item_id = item["item_id"]
    mode_code = item["mode_code"]
    return bool(
        revisions(
            where=f"item_id = {item_id} AND mode_code = '{mode_code}' AND revision_date = '{current_date}'"
        )
    )


def _was_newly_memorized_today(item: dict, current_date: str) -> bool:
    """Check if item was newly memorized today (has NM revision today)."""
    item_id = item["item_id"]
    return bool(
        revisions(
            where=f"item_id = {item_id} AND revision_date = '{current_date}' AND mode_code = '{NEW_MEMORIZATION_MODE_CODE}'"
        )
    )


def _create_standard_rep_mode_predicate(mode_code: str):
    """Factory function to create predicates for standard rep modes."""
    def predicate(item: dict, current_date: str) -> bool:
        if item["mode_code"] != mode_code:
            return False
        return _is_review_due(item, current_date) or (
            _is_reviewed_today(item, current_date) and _has_revisions_in_mode(item)
        )
    return predicate


def should_include_in_daily_reps(item: dict, current_date: str) -> bool:
    """Predicate for Daily Reps mode: due for review OR reviewed today (unless just memorized)."""
    is_due = _is_review_due(item, current_date) and not _was_newly_memorized_today(
        item, current_date
    )
    reviewed_in_mode = (
        _is_reviewed_today(item, current_date)
        and item["mode_code"] == DAILY_REPS_MODE_CODE
    )
    return is_due or reviewed_in_mode


should_include_in_weekly_reps = _create_standard_rep_mode_predicate(WEEKLY_REPS_MODE_CODE)
should_include_in_fortnightly_reps = _create_standard_rep_mode_predicate(FORTNIGHTLY_REPS_MODE_CODE)
should_include_in_monthly_reps = _create_standard_rep_mode_predicate(MONTHLY_REPS_MODE_CODE)


def should_include_in_srs(item: dict, current_date: str) -> bool:
    """Predicate for SRS mode: due for review OR has revisions today."""
    return _is_review_due(item, current_date) or _has_revisions_today_in_mode(
        item, current_date
    )


def should_include_in_full_cycle(item: dict, current_date: str) -> bool:
    """Predicate for Full Cycle mode: item must be memorized."""
    return _has_memorized(item)


MODE_PREDICATES = {
    DAILY_REPS_MODE_CODE: should_include_in_daily_reps,
    WEEKLY_REPS_MODE_CODE: should_include_in_weekly_reps,
    FORTNIGHTLY_REPS_MODE_CODE: should_include_in_fortnightly_reps,
    MONTHLY_REPS_MODE_CODE: should_include_in_monthly_reps,
    SRS_MODE_CODE: should_include_in_srs,
    FULL_CYCLE_MODE_CODE: should_include_in_full_cycle,
}


def make_summary_table(
    mode_code: str,
    auth: str,
    table_only=False,
    offset=0,
    items_per_page=None,
    show_loved_only=False,
    rows_only=False,
):
    current_date = get_current_date(auth)

    mode_condition = get_mode_condition(mode_code)
    mode_specific_hafizs_items_records = get_mode_specific_hafizs_items(auth, mode_condition)

    predicate = MODE_PREDICATES[mode_code]
    filtered_records = [
        item
        for item in mode_specific_hafizs_items_records
        if predicate(item, current_date)
    ]

    def get_unique_item_ids(records):
        return list(dict.fromkeys(record["item_id"] for record in records))

    if mode_code == SRS_MODE_CODE:
        exclude_start_page = get_last_added_full_cycle_page(auth)

        if exclude_start_page is not None:
            SRS_EXCLUSION_ZONE = 60
            exclude_end_page = exclude_start_page + SRS_EXCLUSION_ZONE

            filtered_records = [
                record
                for record in filtered_records
                if record["page_number"] < exclude_start_page
                or record["page_number"] > exclude_end_page
            ]

        if show_loved_only:
            filtered_records = [
                record for record in filtered_records if record.get("loved")
            ]

    item_ids = get_unique_item_ids(filtered_records)

    if mode_code == FULL_CYCLE_MODE_CODE:
        is_plan_finished, item_ids = get_full_review_item_ids(
            auth=auth,
            mode_specific_hafizs_items_records=mode_specific_hafizs_items_records,
            item_ids=item_ids,
        )
    else:
        is_plan_finished = False

    if not item_ids:
        return None

    result = render_summary_table(
        auth=auth,
        mode_code=mode_code,
        item_ids=item_ids,
        is_plan_finished=is_plan_finished,
        offset=offset,
        items_per_page=items_per_page,
        show_loved_only=show_loved_only,
        rows_only=rows_only,
    )
    if rows_only:
        return result
    if table_only:
        return result[1]
    return result


def render_current_date(auth):
    current_date = get_current_date(auth)
    return P(
        Span(date_to_human_readable(current_date), cls=TextPresets.bold_lg, data_testid="system-date"),
    )