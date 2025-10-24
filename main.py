from fasthtml.common import *
import fasthtml.common as fh
from monsterui.all import *
from utils import *
import pandas as pd
from collections import defaultdict
from app.users_controller import users_app
from app.revision import revision_app
from app.new_memorization import new_memorization_app
from app.recent_review import recent_review_app
from app.watch_list import watch_list_app
from app.srs import srs_app
from app.admin import admin_app
from app.page_details import page_details_app
from app.profile import profile_app
from app.hafiz import hafiz_app
from app.common_function import *
from globals import *

RATING_MAP = {"1": "✅ Good", "0": "😄 Ok", "-1": "❌ Bad"}
OPTION_MAP = {
    "role": ["hafiz", "parent", "teacher", "parent_hafiz"],
    "age_group": ["child", "teen", "adult"],
    "relationship": ["self", "parent", "teacher", "sibling"],
}

DEFAULT_RATINGS = {
    "new_memorization": 1,
}


app, rt = create_app_with_auth(
    routes=[
        Mount("/users", users_app, name="users"),
        Mount("/revision", revision_app, name="revision"),
        Mount("/new_memorization", new_memorization_app, name="new_memorization"),
        Mount("/recent_review", recent_review_app, name="recent_review"),
        Mount("/watch_list", watch_list_app, name="watch_list"),
        Mount("/srs", srs_app, name="srs"),
        Mount("/admin", admin_app, name="admin"),
        Mount("/page_details", page_details_app, name="page_details"),
        Mount("/profile", profile_app, name="profile"),
        Mount("/hafiz", hafiz_app, name="hafiz"),
    ]
)

print("-" * 15, "ROUTES=", app.routes)


def get_page_count(records: list[Revision] = None, item_ids: list = None) -> float:
    total_count = 0
    if item_ids:
        process_items = item_ids
    elif records:
        process_items = [record.item_id for record in records]
    else:
        return format_number(total_count)

    # Calculate page count
    for item_id in process_items:
        page_no = items[item_id].page_id
        total_parts = items(where=f"page_id = {page_no} and active = 1")
        total_count += 1 / len(total_parts)
    return format_number(total_count)


def get_unique_page_count(recent_review_items):
    return len(set(map(get_page_number, recent_review_items)))


def get_revision_data(mode_id: str, revision_date: str):
    """Returns the revision count and revision ID for a specific date and mode ID."""
    records = revisions(
        where=f"mode_id = '{mode_id}' AND revision_date = '{revision_date}'"
    )
    rev_ids = ",".join(str(r.id) for r in records)
    count = get_page_count(records)
    return count, rev_ids


def create_count_link(count: int, rev_ids: str):
    if not rev_ids:
        return count
    return A(
        count,
        href=f"/revision/bulk_edit?ids={rev_ids}",
        cls=AT.classic,
    )


def render_progress_display(current_count: int, target_count: int, rev_ids: str = ""):
    target_count = format_number(target_count)
    current_count = format_number(current_count)
    base_link = create_count_link(current_count, rev_ids)
    if current_count == 0 and target_count == 0:
        return "-"
    elif current_count == target_count:
        return (base_link, " ✔️")
    elif current_count > target_count:
        return (base_link, f" / {target_count}", " ✔️")
    else:
        return (base_link, f" / {target_count}")


def mode_dropdown(default_mode=1, **kwargs):
    def mk_options(mode):
        id, name = mode.id, mode.name
        is_selected = lambda m: m == default_mode
        return Option(name, value=id, selected=is_selected(id))

    return LabelSelect(
        map(mk_options, modes()),
        label="Mode Id",
        name="mode_id",
        select_kwargs={"name": "mode_id"},
        **kwargs,
    )


def split_page_range(page_range: str):
    start_id, end_id = (
        page_range.split("-") if "-" in page_range else [page_range, None]
    )
    start_id = int(start_id)
    end_id = int(end_id) if end_id else None
    return start_id, end_id


# This is used to dynamically sort them by mode name which contains the sort order
# eg: sorted(mode_ids, key=lambda id: extract_mode_sort_number(id))
def extract_mode_sort_number(mode_id):
    """Extract the number from mode name like '1. full Cycle' -> 1"""
    mode_name = modes[mode_id].name
    return int(mode_name.split(". ")[0])


####################### END #######################


def datewise_summary_table(show=None, hafiz_id=None):
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

    def _render_datewise_row(date):
        rev_condition = f"WHERE revisions.revision_date = '{date}'" + (
            f" AND revisions.hafiz_id = {hafiz_id}" if hafiz_id else ""
        )
        unique_modes = db.q(f"SELECT DISTINCT mode_id FROM {revisions} {rev_condition}")
        unique_modes = [m["mode_id"] for m in unique_modes]
        unique_modes = sorted(unique_modes, key=lambda id: extract_mode_sort_number(id))

        mode_with_ids_and_pages = []
        for mode_id in unique_modes:
            rev_query = f"SELECT revisions.id, revisions.item_id, items.page_id FROM {revisions} LEFT JOIN {items} ON revisions.item_id = items.id {rev_condition} AND mode_id = {mode_id}"
            current_date_and_mode_revisions = db.q(rev_query)
            mode_with_ids_and_pages.append(
                {
                    "mode_id": mode_id,
                    "revision_data": current_date_and_mode_revisions,
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
                    if mode_with_ids_and_pages[0]["mode_id"] == o["mode_id"]
                    else ()
                ),
                Td(modes[o["mode_id"]].name),
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


def render_total_ticked_count(auth, target_counts):
    current_date = get_current_date(auth)
    today_completed_count = get_page_count(
        revisions(where=f"revision_date = '{current_date}'")
    )
    overall_target_count = sum(target_counts.values())
    return Span(
        render_progress_display(today_completed_count, overall_target_count),
        id="total-ticked-count-footer",
    )


def render_stats_summary_table(auth, target_counts):
    current_date = get_current_date(auth)
    today = current_date
    yesterday = sub_days_to_date(today, 1)
    today_completed_count = get_page_count(
        revisions(where=f"revision_date = '{today}'")
    )
    yesterday_completed_count = get_page_count(
        revisions(where=f"revision_date = '{yesterday}'")
    )
    current_date_description = P(
        Span("System Date: ", cls=TextPresets.bold_lg),
        Span(date_to_human_readable(current_date), id="current_date_description"),
    )
    mode_ids = [mode.id for mode in modes()]
    sorted_mode_ids = sorted(mode_ids, key=lambda x: extract_mode_sort_number(x))

    def render_count(mode_id, revision_date, is_link=True, show_dash_for_zero=False):
        count, item_ids = get_revision_data(mode_id, revision_date)

        if count == 0:
            if show_dash_for_zero:
                return "-", ""
            else:
                return 0, ""

        if is_link:
            return create_count_link(count, item_ids)
        else:
            return count, item_ids

    def render_stat_rows(current_mode_id):
        today_count, today_item_ids = render_count(
            current_mode_id, today, is_link=False
        )
        today_target = (
            target_counts[current_mode_id]
            if current_mode_id in target_counts.keys()
            else 0
        )
        progress_display = render_progress_display(
            today_count, today_target, today_item_ids
        )
        yesterday_display = render_count(
            current_mode_id, yesterday, is_link=True, show_dash_for_zero=True
        )
        return Tr(
            Td(f"{modes[current_mode_id].name}"),
            Td(progress_display),
            Td(yesterday_display),
            id=f"stat-row-{current_mode_id}",
        )

    overall_target_count = sum(target_counts.values())
    return Div(
        DivLAligned(
            current_date_description,
            Button(
                "Close Date",
                id="close-date-btn",
                hx_get="/close_date",
                hx_target="body",
                hx_push_url="true",
                hx_disabled_elt="#close-date-btn, .bulk-add-checkbox, .add-checkbox, .update-dropdown",  # Disable these elements during the request
                cls=(ButtonT.default, "px-2 py-3 h-0"),
            ),
        ),
        Table(
            Thead(
                Tr(
                    Th("Modes"),
                    Th("Today"),
                    Th("Yesterday"),
                )
            ),
            Tbody(
                *map(render_stat_rows, sorted_mode_ids),
            ),
            Tfoot(
                Tr(
                    Td("Total"),
                    Td(
                        render_progress_display(
                            today_completed_count, overall_target_count
                        )
                    ),
                    Td(yesterday_completed_count),
                    cls="[&>*]:font-bold",
                    id="total_row",
                ),
            ),
        ),
    )


def custom_entry_inputs(auth, plan_id):
    """
    This function is used to retain the input values in the form and display the custom entry inputs
    """
    # Get last added item or start from beginning
    revision_data = revisions(where=f"mode_id = 1 AND plan_id = {plan_id}")
    if revision_data:
        last_added_item_id = revision_data[-1].item_id
    else:
        start_page = plans(where=f"hafiz_id = {auth} AND id = {plan_id}")[0].start_page
        # If the user doesn't have a start page, start from beginning
        if start_page is None:
            start_page = 2
        last_added_item_id = items(where=f"page_id = {start_page}")[0].page_id - 1

    next_item_id = find_next_memorized_srs_item_id(last_added_item_id)

    if next_item_id and revisions(
        where=f"item_id = {next_item_id} AND plan_id = {plan_id}"
    ):
        next_item_id = None

    # Fallback to unrevised items if needed
    if not next_item_id:
        unrevised_item_ids = get_unrevised_memorized_item_ids(auth, plan_id)
        next_item_id = unrevised_item_ids[0] if unrevised_item_ids else None

    next_page = get_next_input_page(next_item_id) if next_item_id else None

    if isinstance(next_page, int) and next_page >= 605:
        next_page = None
    if not next_page:
        unrevised_item_ids = get_unrevised_memorized_item_ids(auth, plan_id)
        next_page = "" if not unrevised_item_ids else None

    entry_buttons = Form(
        P(
            "Custom Page Entry",
            cls=TextPresets.muted_sm,
        ),
        DivLAligned(
            Input(
                type="text",
                placeholder="page",
                cls="w-20",
                id="page",
                value=next_page,
                autocomplete="off",
                # Matches numbers 1 to 999 in format like "1-100" or "1.3-2" (number-range or decimal-suffix), excluding zeros
                pattern=r"^(?!0+(?:\.0*)?$|1(?:\.0*)?(?:-\d+)?$)0*\d{1,3}(?:\.\d+)?(?:-\d+)?$",
                title="Enter from page 2, format like 604, 604.2, or 604.2-3",
                required=True,
            ),
            Hidden(id="plan_id", value=plan_id),
            Button("Bulk", name="type", value="bulk", cls=ButtonT.link),
            Button("Single", name="type", value="single", cls=ButtonT.link),
            cls=("gap-3", FlexT.wrap),
        ),
        action="/revision/entry",
        method="POST",
    )
    return Div(
        entry_buttons, cls="flex-wrap gap-4 min-w-72 m-4", id="custom_entry_link"
    )


def get_next_input_page(next_item_id):
    if next_item_id:
        item_details = items[next_item_id]
        next_page = item_details.page_id

        if item_details.item_type == "page-part":
            page_len = len(items(where=f"page_id = {next_page} AND active != 0"))
            # Handle page parts with decimal increments to fill the page input
            # based on the last added record to start from the next part
            if "1" in item_details.part:
                next_page += 0.1
            elif page_len >= 2 and "2" in item_details.part:
                next_page += 0.2
            elif page_len >= 3 and "3" in item_details.part:
                next_page += 0.3
    else:
        next_page = None
    return next_page


############################ End Custom Single and Bulk Entry ################################


@rt
def index(auth, sess, full_cycle_display_count: int = None):
    current_date = get_current_date(auth)
    ################### Overall summary ###################
    seq_id = "1"

    unique_seq_plan_id = [
        i.id for i in plans(where="completed <> 1", order_by="id DESC")
    ]

    if unique_seq_plan_id and not len(unique_seq_plan_id) > 1:
        plan_id = unique_seq_plan_id[0]
    else:
        plan_id = None

    if plan_id is None:
        items_gaps_with_limit = []
    else:
        current_plan_item_ids = sorted(
            [
                r.item_id
                for r in revisions(
                    where=f"mode_id = '{seq_id}' AND plan_id = '{unique_seq_plan_id[0]}'"
                )
            ]
        )
        memorized_and_srs_item_ids = [
            i.item_id for i in hafizs_items(where="status_id IN (1, 5)")
        ]
        # this will return the gap of the current_plan_item_ids based on the master(items_id)
        items_gaps_with_limit = find_gaps(
            current_plan_item_ids, memorized_and_srs_item_ids
        )

    def render_overall_row(o: tuple):
        last_added_item_id, upper_limit = o
        # This is to set a upper limit for the bulk entry, if there are gaps in between
        # to avoid adding records for already added items
        upper_limit = get_last_item_id() if upper_limit is None else upper_limit

        next_item_id = find_next_memorized_srs_item_id(last_added_item_id)

        if next_item_id is None:
            next_page = "No further page"
            action_buttons = None
        else:
            next_page = get_page_description(next_item_id)
            action_buttons = DivLAligned(
                Button(
                    "Bulk",
                    hx_get=f"revision/bulk_add?item_id={next_item_id}&plan_id={plan_id}&max_item_id={get_last_item_id() if upper_limit is None else upper_limit}",
                    hx_target="body",
                    hx_push_url="true",
                    cls=(ButtonT.default, "p-2"),
                ),
                Button(
                    "Single",
                    hx_get=f"revision/add?item_id={next_item_id}&plan_id={plan_id}",
                    hx_target="body",
                    hx_push_url="true",
                    cls=(ButtonT.default, "p-2"),
                ),
                cls=("gap-3", FlexT.wrap),
            )

        return Tr(
            Td(next_page),
            Td(action_buttons),
        )

    if plan_id:
        current_plans_revision_date = revisions(
            where=f"plan_id = {plan_id} AND mode_id = {seq_id}",
            order_by="revision_date ASC",
        )

        if current_plans_revision_date:
            unique_pages = list(
                set([get_page_number(i.item_id) for i in current_plans_revision_date])
            )
            total_pages = len(unique_pages)

            first_date = current_plans_revision_date[0].revision_date

            # When adding a record for the first time, total_days will be 0
            if first_date == current_date:
                total_days = 1
            else:
                total_days = calculate_days_difference(first_date, current_date)

            average_pages = total_pages / total_days
            average_pages = (
                int(average_pages)
                if average_pages.is_integer()
                else round(average_pages, 1)
            )

            description = P(
                f"{total_pages} pages in {total_days} days => ",
                Span(average_pages, cls=TextT.bold),
                " pages per day",
                cls=TextPresets.muted_sm,
            )

        else:
            description = None
    else:
        description = None
    ############################ Monthly Cycle ################################

    def get_monthly_target_and_progress():
        current_date = get_current_date(auth)
        monthly_review_target = get_daily_capacity(auth) // 2
        monthly_reviews_completed_today = get_page_count(
            revisions(where=f"mode_id = '1' and revision_date='{current_date}'")
        )
        return monthly_review_target, monthly_reviews_completed_today

    def get_extra_page_display_count(sess, auth, current_date):
        sess_data = sess.get("full_cycle_display_count_details", {})
        # Check if session data is valid for current user and date
        if (
            sess_data.get("auth") == auth
            and sess_data.get("current_date") == current_date
        ):
            return sess_data.get("extra_no_of_pages", 0)
        # For new user/date reset to default value
        return 0

    def update_extra_page_display_count():
        current_extra = get_extra_page_display_count(sess, auth, current_date)
        new_extra = current_extra + (full_cycle_display_count or 0)

        sess["full_cycle_display_count_details"] = {
            "auth": auth,
            "extra_no_of_pages": new_extra,
            "current_date": current_date,
        }
        return new_extra

    def create_count_button(count):
        return Button(
            f"+{count}",
            hx_get=f"/?full_cycle_display_count={count}",
            hx_select="#monthly_cycle_summary_table",
            hx_target="#monthly_cycle_summary_table",
            hx_swap="outerHTML",
        )

    total_display_count = get_display_count(auth) + update_extra_page_display_count()

    monthly_cycle_table, monthly_cycle_items = make_summary_table(
        mode_ids=["1", "5"],
        route="monthly_cycle",
        auth=auth,
        total_display_count=total_display_count,
        plan_id=plan_id,
    )
    monthly_review_target, monthly_reviews_completed_today = (
        get_monthly_target_and_progress()
    )
    monthly_progress_display = render_progress_display(
        monthly_reviews_completed_today, monthly_review_target
    )
    overall_table = AccordionItem(
        Span(
            f"{modes[1].name} - ",
            monthly_progress_display,
            id=f"monthly_cycle-header",
        ),
        monthly_cycle_table,
        DivHStacked(
            *[create_count_button(count) for count in [1, 2, 3, 5]],
            cls=(FlexT.center, "gap-2"),
        ),
        Div(
            description,
            (
                Table(
                    Thead(
                        Tr(
                            Th("Next"),
                            Th("Entry"),
                        )
                    ),
                    Tbody(*map(render_overall_row, items_gaps_with_limit)),
                    id="monthly_cycle_link_table",
                )
                if len(items_gaps_with_limit) > 0
                else Div(id="monthly_cycle_link_table")
            ),
            custom_entry_inputs(auth, plan_id) if plan_id else None,
        ),
        open=True,
        div_kwargs={"data-testid": "monthly-cycle-summary-table-area"},
    )
    ############################# END ################################

    recent_review_table, recent_review_items = make_summary_table(
        mode_ids=["2", "3"], route="recent_review", auth=auth
    )

    recent_review_target = get_page_count(item_ids=recent_review_items)

    # Include mode_id=1 as well so that graduated watch list items are included
    watch_list_table, watch_list_items = make_summary_table(
        mode_ids=["4", "1"], route="watch_list", auth=auth
    )
    watch_list_target = get_page_count(item_ids=watch_list_items)

    new_memorization_table, new_memorization_items = (
        make_new_memorization_summary_table(
            mode_ids=["2"], route="new_memorization", auth=auth
        )
    )
    new_memorization_target = get_page_count(item_ids=new_memorization_items)

    srs_table, srs_items = make_summary_table(mode_ids=["5"], route="srs", auth=auth)

    srs_target = get_page_count(item_ids=srs_items)

    modal = ModalContainer(
        ModalDialog(
            ModalHeader(
                ModalTitle(id="modal-title"),
                P(cls=TextPresets.muted_sm, id="modal-description"),
                ModalCloseButton(),
                cls="space-y-3",
            ),
            ModalBody(
                Div(id="modal-body"),
                data_uk_overflow_auto=True,
            ),
            ModalFooter(),
            cls="uk-margin-auto-vertical",
        ),
        id="modal",
    )

    tables_dict = {
        modes[1].name: overall_table if not (plan_id is None) else None,
        modes[2].name: new_memorization_table,
        modes[3].name: recent_review_table,
        modes[4].name: watch_list_table,
        modes[5].name: srs_table,
    }

    # Dynamically sort the table order based on the mode name
    tables_dict = dict(
        sorted(tables_dict.items(), key=lambda x: int(x[0].split(". ")[0]))
    )

    tables = tables_dict.values()
    # if the table has no records then exclude them from the tables list
    tables = [_table for _table in tables if _table is not None]
    target_counts = {
        1: monthly_review_target,
        2: new_memorization_target,
        3: recent_review_target,
        4: watch_list_target,
        5: srs_target,
    }

    stat_table = render_stats_summary_table(auth=auth, target_counts=target_counts)
    total_ticked_count = render_total_ticked_count(
        auth=auth, target_counts=target_counts
    )
    return main_area(
        Div(stat_table, Divider(), Accordion(*tables, multiple=True, animation=True)),
        Div(modal),
        active="Home",
        auth=auth,
        additional_info=total_ticked_count,
    )


def update_hafiz_item_for_full_cycle(rev):
    hafiz_item_details = get_hafizs_items(rev.item_id)
    last_review = hafiz_item_details.last_review
    currrent_date = get_current_date(rev.hafiz_id)
    # when a SRS page is revised in full-cycle mode, we need to move the next review of that page using the current next_interval
    if hafiz_item_details.mode_id == 5:
        hafiz_item_details.next_review = add_days_to_date(
            currrent_date, hafiz_item_details.next_interval
        )

    hafiz_item_details.last_interval = calculate_days_difference(
        last_review, currrent_date
    )
    hafizs_items.update(hafiz_item_details)


def update_hafiz_item_for_new_memorization(rev):
    hafiz_item_details = get_hafizs_items(rev.item_id)
    hafiz_item_details.mode_id = 2
    hafiz_item_details.status_id = 4
    hafizs_items.update(hafiz_item_details)


def update_hafiz_item_for_daily(rev):
    hafiz_item_details = get_hafizs_items(rev.item_id)
    current_date = get_current_date(rev.hafiz_id)

    if get_mode_count(item_id=rev.item_id, mode_id=rev.mode_id) < 7:
        next_interval = 1
    else:
        # If the reps are more than 7 then move it to Weekly reps
        next_interval = 7
        hafiz_item_details.mode_id = 4

    # This is one time process, when the page gets recorded in the daily reps for the first time
    # As it got entered as the `newly memorized`.
    if hafiz_item_details.mode_id == 2:
        hafiz_item_details.mode_id = 3
    hafiz_item_details.last_interval = hafiz_item_details.next_interval
    hafiz_item_details.next_interval = next_interval
    hafiz_item_details.next_review = add_days_to_date(current_date, next_interval)
    hafizs_items.update(hafiz_item_details)


def update_hafiz_item_for_weekly(rev):
    hafiz_item_details = get_hafizs_items(rev.item_id)
    current_date = get_current_date(rev.hafiz_id)

    if get_mode_count(item_id=rev.item_id, mode_id=rev.mode_id) < 7:
        next_interval = 7
        hafiz_item_details.last_interval = hafiz_item_details.next_interval
        hafiz_item_details.next_interval = next_interval
        hafiz_item_details.next_review = add_days_to_date(current_date, next_interval)
    else:
        # If the reps are more than 7 then move it to full cycle
        hafiz_item_details.mode_id = 1
        hafiz_item_details.status_id = 1
        hafiz_item_details.last_interval = hafiz_item_details.next_interval
        hafiz_item_details.next_interval = None
        hafiz_item_details.next_review = None
        hafiz_item_details.watch_list_graduation_date = current_date

    hafizs_items.update(hafiz_item_details)


def update_hafiz_item_for_srs(rev):
    hafiz_items_details = get_hafizs_items(rev.item_id)
    current_date = get_current_date(rev.hafiz_id)
    end_interval = srs_booster_pack[
        hafiz_items_details.srs_booster_pack_id
    ].end_interval
    next_interval = get_next_interval(item_id=rev.item_id, rating=rev.rating)

    hafiz_items_details.last_interval = hafiz_items_details.next_interval
    if end_interval > next_interval:
        hafiz_items_details.next_interval = next_interval
        hafiz_items_details.next_review = add_days_to_date(current_date, next_interval)
    else:
        hafiz_items_details.mode_id = 1
        hafiz_items_details.status_id = 1
        hafiz_items_details.last_interval = calculate_days_difference(
            hafiz_items_details.last_review, current_date
        )
        hafiz_items_details.next_interval = None
        hafiz_items_details.next_review = None
        hafiz_items_details.srs_booster_pack_id = None
        hafiz_items_details.srs_start_date = None

    hafizs_items.update(hafiz_items_details)

    # Update the next_interval of the revision record
    rev.next_interval = next_interval
    revisions.update(rev, rev.id)


@app.get("/close_date")
def confirmation_page_for_close_date(auth):
    current_date = get_current_date(auth)

    # List all the records that are recorded today with the interval details as a table
    srs_records = db.q(
        f"""
    SELECT revisions.item_id, hafizs_items.next_interval as previous_interval,
    revisions.rating, hafizs_items.srs_booster_pack_id as pack_id FROM revisions 
    LEFT JOIN hafizs_items ON hafizs_items.item_id = revisions.item_id AND hafizs_items.hafiz_id = revisions.hafiz_id
    WHERE revisions.revision_date = '{current_date}' AND revisions.mode_id = 5
    """
    )

    def render_srs_records(srs_record):
        pack_details = srs_booster_pack[srs_record["pack_id"]]
        end_interval = pack_details.end_interval
        next_interval = get_next_interval(srs_record["item_id"], srs_record["rating"])
        if next_interval > end_interval:
            next_interval = "Graduation"
        return Tr(
            Td(get_page_description(srs_record["item_id"])),
            Td(srs_record["previous_interval"]),
            Td(get_actual_interval(srs_record["item_id"])),
            Td(next_interval),
            Td(render_rating(srs_record["rating"])),
        )

    srs_records_table = Table(
        Thead(
            Tr(
                Th("Item Id"),
                Th("Last Interval"),
                Th("Actual Interval"),
                Th("Next Interval"),
                Th("Rating"),
            )
        ),
        Tbody(*map(render_srs_records, srs_records)),
    )

    # Confirmation and cancel buttons
    action_buttons = DivLAligned(
        Button(
            "Confirm",
            hx_post="close_date",
            hx_target="body",
            hx_push_url="true",
            hx_disabled_elt="this",
            cls=(ButtonT.primary, "p-2"),
        ),
        Button(
            "Cancel",
            onclick="history.back()",
            cls=(ButtonT.default, "p-2"),
        ),
    )

    header = Div(
        Strong("Current Date: "),
        Span(render_date(current_date)),
    )
    body = Div(
        H2("SRS Records"),
        srs_records_table,
        cls="uk-overflow-auto space-y-2",
    )
    footer = action_buttons

    return main_area(
        Div(header, body, footer, cls="space-y-4"),
        active="Home",
        auth=auth,
    )


@app.post("/close_date")
def change_the_current_date(auth):
    hafiz_data = hafizs[auth]

    revision_data = revisions(where=f"revision_date = '{hafiz_data.current_date}'")
    for rev in revision_data:
        if rev.mode_id == 1:
            update_hafiz_item_for_full_cycle(rev)
        elif rev.mode_id == 2:
            update_hafiz_item_for_new_memorization(rev)
        elif rev.mode_id == 3:
            update_hafiz_item_for_daily(rev)
        elif rev.mode_id == 4:
            update_hafiz_item_for_weekly(rev)
        elif rev.mode_id == 5:
            update_hafiz_item_for_srs(rev)

        # update all the non-mode specific columns (including the last_review column)
        populate_hafizs_items_stat_columns(item_id=rev.item_id)

    # TODO: The page should enter into SRS mode before or after updating the current_date?
    # Get the full-cycle today revised pages which have 2 or more bad streak
    qry = f"""
        SELECT revisions.item_id FROM revisions
        LEFT JOIN hafizs_items ON revisions.item_id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
        WHERE hafizs_items.bad_streak >= 2 AND revisions.mode_id = 1 AND revisions.hafiz_id = {auth} AND revisions.revision_date = '{hafiz_data.current_date}'
    """
    for items in db.q(qry):
        start_srs(items["item_id"], auth)

    # Change the current date to next date
    hafiz_data.current_date = add_days_to_date(hafiz_data.current_date, 1)
    hafizs.update(hafiz_data)

    return Redirect("/")


@app.get("/report")
def datewise_summary_table_view(auth):
    return main_area(datewise_summary_table(hafiz_id=auth), active="Report", auth=auth)


def make_new_memorization_summary_table(auth: str, mode_ids: list[str], route: str):
    current_date = get_current_date(auth)

    def get_last_memorized_item_id():
        result = revisions(
            where=f"hafiz_id = {auth} AND mode_id = 2",
            order_by="revision_date DESC, id DESC",
            limit=1,
        )
        return result[0].item_id if result else 0

    def get_last_newly_memorized_page_for_today():
        qry = f"""
            SELECT items.page_id AS page_number FROM revisions
            JOIN items ON revisions.item_id = items.id 
            WHERE revisions.hafiz_id = {auth} AND revisions.mode_id = 2 AND revisions.revision_date = '{current_date}'
            ORDER BY revisions.id DESC;
        """
        result = db.q(qry)
        return result[0]["page_number"] if result else None

    def get_not_memorized_item_ids(page_id):
        result = hafizs_items(where=f"page_number = {page_id} AND status_id = 6")
        return [i.item_id for i in result]

    def get_next_unmemorized_page_items(item_id):
        qry = f"""
            SELECT items.id AS item_id, items.page_id AS page_number FROM items
            LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
            WHERE hafizs_items.status_id = 6 AND items.active != 0 AND items.id > {item_id}
       """
        ct = db.q(qry)
        grouped = group_by_type(ct, "page")
        if not grouped:
            return []
        first_page = next(iter(grouped))
        return [i["item_id"] for i in grouped[first_page] if i]

    def get_today_memorized_item_ids():
        result = revisions(where=f"mode_id = 2 AND revision_date = '{current_date}'")
        return [i.item_id for i in result]

    today_page_id = get_last_newly_memorized_page_for_today()
    # If there are no newly memorized revisions for today, then get the closest unmemorized items to display
    if today_page_id:
        unmemorized_items = get_not_memorized_item_ids(today_page_id)
    else:
        last_newly_memorized_item_id = get_last_memorized_item_id()
        unmemorized_items = get_next_unmemorized_page_items(
            last_newly_memorized_item_id
        )
    recent_newly_memorized_items = get_today_memorized_item_ids()

    new_memorization_items = sorted(
        set(unmemorized_items + recent_newly_memorized_items)
    )
    return (
        render_summary_table(
            route=route,
            auth=auth,
            mode_ids=mode_ids,
            item_ids=new_memorization_items,
        ),
        new_memorization_items,
    )


def make_summary_table(
    mode_ids: list[str],
    route: str,
    auth: str,
    total_display_count=0,
    plan_id=None,
):
    current_date = get_current_date(auth)

    def is_review_due(item: dict) -> bool:
        """Check if item is due for review today or overdue."""
        return day_diff(item["next_review"], current_date) >= 0

    def is_reviewed_today(item: dict) -> bool:
        return item["last_review"] == current_date

    def has_recent_mode_id(item: dict) -> bool:
        return item["mode_id"] == 3

    def has_watchlist_mode_id(item: dict) -> bool:
        return item["mode_id"] == 4

    def has_memorized(item: dict) -> bool:
        return item["status_id"] == 1

    def is_srs(item: dict) -> bool:
        return item["status_id"] == 5

    def has_revisions(item: dict) -> bool:
        """Check if item has revisions for current mode."""
        return bool(
            revisions(
                where=f"item_id = {item['item_id']} AND mode_id = {item['mode_id']}"
            )
        )

    def has_revisions_today(item: dict) -> bool:
        """Check if item has revisions for current mode today."""
        return bool(
            revisions(
                where=f"item_id = {item['item_id']} AND mode_id = {item['mode_id']} AND revision_date = '{current_date}'"
            )
        )

    def has_newly_memorized_for_today(item: dict) -> bool:
        newly_memorized_record = revisions(
            where=f"item_id = {item['item_id']} AND revision_date = '{current_date}' AND mode_id = 2"
        )
        return len(newly_memorized_record) == 1

    qry = f"""
        SELECT hafizs_items.item_id, items.surah_name, hafizs_items.next_review, hafizs_items.last_review, hafizs_items.watch_list_graduation_date, hafizs_items.mode_id, hafizs_items.status_id FROM hafizs_items
        LEFT JOIN items on hafizs_items.item_id = items.id 
        WHERE hafizs_items.mode_id IN ({", ".join(mode_ids)}) AND hafizs_items.hafiz_id = {auth}
        ORDER BY hafizs_items.item_id ASC
    """
    ct = db.q(qry)

    # Route-specific condition builders
    route_conditions = {
        "recent_review": lambda item: (
            (is_review_due(item) and not has_newly_memorized_for_today(item))
            or (is_reviewed_today(item) and has_recent_mode_id(item))
        ),
        "watch_list": lambda item: (
            item["watch_list_graduation_date"] == current_date
            or (
                has_watchlist_mode_id(item)
                and (
                    is_review_due(item)
                    or (is_reviewed_today(item) and has_revisions(item))
                )
            )
        ),
        "srs": lambda item: (is_review_due(item) or has_revisions_today(item)),
        "monthly_cycle": lambda item: (has_memorized(item) or is_srs(item)),
    }

    item_ids = list(
        dict.fromkeys(i["item_id"] for i in ct if route_conditions[route](i))
    )
    if route == "monthly_cycle":
        item_ids = get_monthly_review_item_ids(
            auth=auth,
            total_display_count=total_display_count,
            ct=ct,
            item_ids=item_ids,
            current_plan_id=plan_id,
        )

    if route == "srs":
        srs_limit = get_srs_limit(auth)
        item_ids = item_ids[:srs_limit]

    return (
        render_summary_table(
            route=route,
            auth=auth,
            mode_ids=mode_ids,
            item_ids=item_ids,
            plan_id=plan_id,
        ),
        item_ids,
    )


def get_monthly_review_item_ids(
    auth, total_display_count, ct, item_ids, current_plan_id
):
    current_date = get_current_date(auth)

    def has_revisions_today(item: dict) -> bool:
        """Check if item has revised today for current mode."""
        return bool(
            revisions(
                where=f"item_id = {item['item_id']} AND revision_date = '{current_date}' AND mode_id = {item['mode_id']}"
            )
        )

    def get_next_item_range_from_item_id(item_ids, start_item_id, no_of_next_items):
        """Get items from a list starting from a specific number."""
        try:
            start_idx = item_ids.index(start_item_id)
            end_idx = min(start_idx + no_of_next_items, len(item_ids))
            return item_ids[start_idx:end_idx]
        except ValueError:
            return []

    def has_monthly_cycle_mode_id(item: dict) -> bool:
        return item["mode_id"] == 1

    if current_plan_id is not None:
        # eliminate items that are already revisioned in the current plan_id
        eligible_item_ids = [
            i
            for i in item_ids
            if not revisions(
                where=f"item_id = {i} AND mode_id = 1 AND plan_id = {current_plan_id} AND revision_date != '{current_date}'"
            )
        ]
        # TODO: handle the new user that not have any revision/plan_id
        last_added_revision = revisions(
            where=f"revision_date <> '{current_date}' AND mode_id = 1 AND plan_id = {current_plan_id}",
            order_by="revision_date DESC, id DESC",
            limit=1,
        )
        last_added_item_id = (
            last_added_revision[0].item_id if last_added_revision else 0
        )

        next_item_id = find_next_greater(eligible_item_ids, last_added_item_id)
    else:
        eligible_item_ids = []
        next_item_id = 0

    item_ids = get_next_item_range_from_item_id(
        eligible_item_ids, next_item_id, total_display_count
    )

    # take today revision data that are not in today's target (item_ids)
    display_conditions = {
        "monthly_cycle": lambda item: (
            has_monthly_cycle_mode_id(item)
            and has_revisions_today(item)
            and item["item_id"] not in item_ids
        )
    }
    today_revisioned_items = list(
        dict.fromkeys(
            i["item_id"] for i in ct if display_conditions["monthly_cycle"](i)
        )
    )

    item_ids = sorted(item_ids + today_revisioned_items)
    return item_ids


def render_summary_table(auth, route, mode_ids, item_ids, plan_id=None):
    is_accordion = route != "monthly_cycle"
    mode_id_mapping = {
        "monthly_cycle": 1,
        "new_memorization": 2,
        "recent_review": 3,
        "watch_list": 4,
        "srs": 5,
    }
    mode_id = mode_id_mapping[route]
    is_newly_memorized = mode_id == 2
    is_monthly_review = mode_id == 1
    is_srs = mode_id == 5
    current_date = get_current_date(auth)
    # This list is to close the accordian, if all the checkboxes are selected
    is_all_selected = []

    # Sort the item_ids by not revised(top) and revised(bottom)
    # records = db.q(
    #     f"""
    #     SELECT hafizs_items.item_id FROM hafizs_items
    #     LEFT JOIN revisions on hafizs_items.item_id = revisions.item_id AND hafizs_items.hafiz_id = revisions.hafiz_id AND revisions.revision_date = '{current_date}'
    #     WHERE hafizs_items.hafiz_id = {auth} AND hafizs_items.item_id IN ({", ".join(map(str, item_ids))})
    #     ORDER BY revisions.item_id, hafizs_items.item_id ASC
    # """
    # )
    # item_ids = [r["item_id"] for r in records]

    def render_range_row(item_id: str):
        row_id = f"{route}-row-{item_id}"
        plan_condition = f"AND plan_id = {plan_id}" if is_monthly_review else ""
        current_revision_data = revisions(
            where=f"revision_date = '{current_date}' AND item_id = {item_id} AND mode_id IN ({", ".join(mode_ids)}) {plan_condition}"
        )
        is_checked = len(current_revision_data) != 0
        is_all_selected.append(is_checked)
        checkbox_hx_attrs = {
            "hx_post": f"/add/{item_id}",
            "hx_select": f"#{row_id}",
            # TODO: make the monthly cycle to only rerender on monthly summary table
            "hx_select_oob": f"#stat-row-{mode_id}, #total_row, #total-ticked-count-footer, #{route}-header"
            + (", #monthly_cycle_link_table, #page" if is_monthly_review else ""),
            "hx_target": f"#{row_id}",
            "hx_swap": "outerHTML",
        }
        vals_dict = {"date": current_date, "mode_id": mode_id}
        if is_monthly_review:
            vals_dict["plan_id"] = plan_id
        record_btn = CheckboxX(
            name=f"is_checked",
            value="1",
            **checkbox_hx_attrs,
            hx_vals=vals_dict,
            hx_include=f"#rev-{item_id}",
            checked=is_checked,
            cls=(
                f"{route}_ids",
                "add-checkbox",  # This class-name is used to disable the checkbox when closing the date to prevent it from being updated
                "disabled:opacity-50",
            ),
            _at_click="handleCheckboxClick($event)",  # To handle `shift+click` selection
            data_testid=f"{item_id}-checkbox",
        )

        if current_revision_data:
            current_rev_data = current_revision_data[0]
            default_rating = current_rev_data.rating
            change_rating_hx_attrs = {
                "hx_put": f"/revision/{current_rev_data.id}",
                "hx_swap": "none",
            }
        else:
            default_rating = 1
            change_rating_hx_attrs = checkbox_hx_attrs
            change_rating_hx_attrs["hx_vals"] = {
                "date": current_date,
                "mode_id": mode_id,
                "is_checked": True,
            }
            if is_monthly_review:
                change_rating_hx_attrs["hx_vals"]["plan_id"] = plan_id

        rating_dropdown_input = rating_dropdown(
            default_mode=str(default_rating),
            is_label=False,
            id=f"rev-{item_id}",
            cls="update-dropdown",  # This class-name is used to disable the dropdown when closing the date to prevent it from being updated
            hx_trigger="change",
            **change_rating_hx_attrs,
        )

        revs = revisions(where=f"item_id = {item_id} AND mode_id = {mode_id}")
        if mode_id == 5:
            rep_denominator = len(get_srs_interval_list(item_id))
        else:
            rep_denominator = 7
        progress = P(Strong(len(revs)), Span(f"/{rep_denominator}"))

        if is_srs:
            hafiz_item_details = get_hafizs_items(item_id)
            actual_interval = get_actual_interval(item_id)
            extra_srs_columns = (
                Td(hafiz_item_details.next_interval),
                Td(actual_interval),
            )
        else:
            extra_srs_columns = ()

        return Tr(
            Td(get_page_description(item_id)),
            Td(
                get_start_text(item_id),
                cls=TextT.lg,
            ),
            (
                Td(progress)
                if not (is_newly_memorized or is_monthly_review or is_srs)
                else None
            ),
            *extra_srs_columns,
            Td(record_btn),
            Td(
                Form(
                    rating_dropdown_input,
                    Hidden(name="item_id", value=item_id),
                    Hidden(name="is_checked", value=f"{is_checked}"),
                    id=f"{route}_ratings",
                )
            ),
            id=row_id,
            cls="bg-green-100" if is_checked else None,
        )

    body_rows = list(map(render_range_row, item_ids))
    target_page_count = get_page_count(item_ids=item_ids)
    progress_page_count = get_page_count(
        revisions(where=f"mode_id = {mode_id} and revision_date = '{current_date}'")
    )
    summary_count = render_progress_display(progress_page_count, target_page_count)
    if not body_rows:
        return None

    select_all_vals = {
        "mode_id": mode_id,
        "date": current_date,
    }
    if is_monthly_review:
        select_all_vals["plan_id"] = plan_id

    render_output = (
        Div(
            Div(
                (
                    A(
                        "Record",
                        href=f"/{route}",
                        hx_boost="false",
                        cls=(AT.classic, TextPresets.bold_sm, "float-right"),
                    )
                    if route != "monthly_cycle"
                    else None
                ),
                cls="w-full",
            ),
            Table(
                Thead(
                    Tr(
                        Th("Page", cls="min-w-24"),
                        Th("Start Text", cls="min-w-24"),
                        (
                            Th("Reps")
                            if not (is_newly_memorized or is_monthly_review or is_srs)
                            else None
                        ),
                        ((Th("Next"), Th("Actual")) if is_srs else None),
                        Th(
                            CheckboxX(
                                name="is_select_all",
                                hx_vals=select_all_vals,
                                hx_post="/bulk_add",
                                hx_trigger="change",
                                hx_include=f"#{route}_ratings",
                                hx_select=f"#{route}_tbody",
                                hx_select_oob=f"#stat-row-{mode_id}, #total_row, #total-ticked-count-footer, #{route}-header"
                                + (
                                    ", #monthly_cycle_link_table, #page"
                                    if is_monthly_review
                                    else ""
                                ),
                                hx_target=f"#{route}_tbody",
                                hx_swap="outerHTML",
                                checked=all(is_all_selected),
                                cls=(
                                    "select_all",
                                    "bulk-add-checkbox",  # This class-name is used to disable the checkbox when closing the date to prevent it from being updated
                                    "disabled:opacity-50",
                                    ("hidden" if mode_id == 5 else None),
                                ),
                                x_model="selectAll",  # To update the current status of the checkbox (checked or unchecked)
                            )
                        ),
                        Th("Rating", cls="min-w-24"),
                    )
                ),
                Tbody(*body_rows, id=f"{route}_tbody", data_testid=f"{route}_tbody"),
                id=f"{route}_summary_table",
                x_data=select_all_with_shift_click_for_summary_table(
                    class_name=f"{route}_ids"
                ),
                # initializing the updateSelectAll function to select the selectAll checkboxe.
                # if all the below checkboxes are selected.
                x_init="updateSelectAll()",
                # This is responsible for preserving the scroll position when hx-swap happens, to prevent scroll jump.
                hx_on__before_request="sessionStorage.setItem('scroll', window.scrollY)",
                hx_on__after_swap="window.scrollTo(0, sessionStorage.getItem('scroll'))",
            ),
        ),
    )
    return (
        AccordionItem(
            Span(f"{modes[mode_id].name} - ", summary_count, id=f"{route}-header"),
            render_output,
            open=(not all(is_all_selected)),
        )
        if is_accordion
        else render_output
    )


# This route is responsible for adding and deleting record for all the summary table on the home page
# and update the review dates for that item_id
@app.post("/add/{item_id}")
def update_status_from_index(
    date: str,
    item_id: str,
    mode_id: int,
    rating: int,
    is_checked: bool = False,
    plan_id: int = None,
):
    if is_checked:
        add_revision_record(
            item_id=item_id,
            mode_id=mode_id,
            revision_date=date,
            rating=rating,
            plan_id=plan_id,
        )
    else:
        remove_revision_record(item_id=item_id, mode_id=mode_id, date=date)

    return RedirectResponse("/", status_code=303)


@app.post("/bulk_add")
def update_multiple_items_from_index(
    mode_id: int,
    date: str,
    item_id: list[int],
    rating: list[int],
    is_checked: list[bool],
    plan_id: str = None,
    is_select_all: bool = False,
):
    for o in zip(item_id, rating, is_checked):
        current_item_id, current_rating, current_is_checked = o
        if not is_select_all:
            remove_revision_record(item_id=current_item_id, mode_id=mode_id, date=date)
        elif not current_is_checked:
            add_revision_record(
                item_id=current_item_id,
                mode_id=mode_id,
                revision_date=date,
                rating=current_rating,
                plan_id=plan_id,
            )

    return RedirectResponse("/", status_code=303)


serve()
