from fasthtml.common import *
from monsterui.all import *
from utils import *
import pandas as pd
from app.users_controller import users_app
from app.revision import revision_app
from app.new_memorization import (
    new_memorization_app,
    update_hafiz_item_for_new_memorization,
)
from app.admin import admin_app
from app.page_details import page_details_app
from app.profile import profile_app
from app.hafiz import hafiz_app
from app.common_function import *
from globals import *
from app.fixed_reps import REP_MODES_CONFIG, update_rep_item
from app.srs_reps import (
    display_srs_pages_recorded_today,
    update_hafiz_item_for_srs,
    start_srs_for_bad_streak_items,
)

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
        Mount("/admin", admin_app, name="admin"),
        Mount("/page_details", page_details_app, name="page_details"),
        Mount("/profile", profile_app, name="profile"),
        Mount("/hafiz", hafiz_app, name="hafiz"),
    ]
)

print("-" * 15, "ROUTES=", app.routes)


def get_revision_data(mode_id: str, revision_date: str):
    """Returns the revision count and revision ID for a specific date and mode ID."""
    records = revisions(
        where=f"mode_id = '{mode_id}' AND revision_date = '{revision_date}'"
    )
    rev_ids = ",".join(str(r.id) for r in records)
    count = get_page_count(records)
    return count, rev_ids


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


def create_stat_table(auth):
    current_date = get_current_date(auth)
    today = current_date
    yesterday = sub_days_to_date(today, 1)
    today_completed_count = get_page_count(
        revisions(where=f"revision_date = '{today}'")
    )
    yesterday_completed_count = get_page_count(
        revisions(where=f"revision_date = '{yesterday}'")
    )
    mode_ids = [mode.id for mode in modes()]

    def render_count(mode_id, revision_date):
        count, item_ids = get_revision_data(mode_id, revision_date)

        if count == 0:
            return "-"

        return create_count_link(count, item_ids)

    def render_stat_rows(current_mode_id):
        return Tr(
            Td(f"{modes[current_mode_id].name}"),
            Td(render_count(current_mode_id, today)),
            Td(render_count(current_mode_id, yesterday)),
            id=f"stat-row-{current_mode_id}",
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
            *map(render_stat_rows, mode_ids),
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


def custom_entry_inputs(auth, plan_id):
    """
    This function is used to retain the input values in the form and display the custom entry inputs
    """
    # Get last added item or start from beginning
    revision_data = revisions(
        where=f"mode_id = {FULL_CYCLE_MODE_ID} AND plan_id = {plan_id}"
    )
    if revision_data:
        last_added_item_id = revision_data[-1].item_id
    else:
        start_page = plans(where=f"hafiz_id = {auth} AND id = {plan_id}")[0].start_page
        # If the user doesn't have a start page, start from beginning
        if start_page is None:
            start_page = 2
        last_added_item_id = items(where=f"page_id = {start_page}")[0].page_id - 1

    next_item_id = find_next_memorized_item_id(last_added_item_id)

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
    return Div(entry_buttons, cls="flex-wrap gap-4 min-w-72", id="custom_entry_link")


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
    plan_id = get_current_plan_id()

    ############################ full Cycle ################################

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
            hx_select="#full_cycle_summary_table",
            hx_target="#full_cycle_summary_table",
            hx_swap="outerHTML",
        )

    total_display_count = (
        get_full_cycle_daily_limit(auth) + update_extra_page_display_count()
    )

    full_cycle_table = make_summary_table(
        mode_ids=[str(FULL_CYCLE_MODE_ID), str(SRS_MODE_ID)],
        route="full_cycle",
        auth=auth,
        total_display_count=total_display_count,
        plan_id=plan_id,
    )
    overall_table = AccordionItem(
        Span(
            modes[1].name,
            id=f"full_cycle-header",
        ),
        full_cycle_table,
        DivHStacked(
            *[create_count_button(count) for count in [1, 2, 3, 5]],
            cls=(FlexT.center, "gap-2"),
        ),
        open=True,
        div_kwargs={"data-testid": "full-cycle-summary-table-area"},
    )
    ############################# END ################################

    daily_reps_table = get_reps_table(
        mode_ids=[NEW_MEMORIZATION_MODE_ID, DAILY_REPS_MODE_ID],
        route="daily_reps",
        auth=auth,
    )
    weekly_reps_table = get_reps_table(
        mode_ids=[WEEKLY_REPS_MODE_ID, FULL_CYCLE_MODE_ID],
        route="weekly_reps",
        auth=auth,
    )
    srs_table = get_reps_table(mode_ids=[SRS_MODE_ID], route="srs", auth=auth)

    mode_tables = [
        (overall_table if plan_id else None),
        daily_reps_table,
        weekly_reps_table,
        srs_table,
    ]

    # if the table has no records then exclude them from the tables list
    mode_tables = [_table for _table in mode_tables if _table is not None]

    # Contains the date and close button
    header = DivLAligned(
        render_current_date(auth),
        Button(
            A(
                "Close Date",
                href="/close_date",
            ),
        ),
    )
    return main_area(
        Div(
            header,
            Accordion(*mode_tables, multiple=True, animation=True),
        ),
        active="Home",
        auth=auth,
    )


def update_hafiz_item_for_full_cycle(rev):
    hafiz_item_details = get_hafizs_items(rev.item_id)
    last_review = hafiz_item_details.last_review
    currrent_date = get_current_date(rev.hafiz_id)
    # when a SRS page is revised in full-cycle mode, we need to move the next review of that page using the current next_interval
    if hafiz_item_details.mode_id == SRS_MODE_ID:
        hafiz_item_details.next_review = add_days_to_date(
            currrent_date, hafiz_item_details.next_interval
        )

    hafiz_item_details.last_interval = get_actual_interval(rev.item_id)
    hafizs_items.update(hafiz_item_details)


@app.get("/close_date")
def close_date_confirmation_page(auth):
    header = render_current_date(auth)
    return main_area(
        header,
        create_stat_table(auth),
        DividerLine(),
        display_srs_pages_recorded_today(auth),
        active="Home",
        auth=auth,
    )


@app.post("/close_date")
def change_the_current_date(auth):
    hafiz_data = hafizs[auth]

    revision_data = revisions(where=f"revision_date = '{hafiz_data.current_date}'")
    for rev in revision_data:
        if rev.mode_id == FULL_CYCLE_MODE_ID:
            update_hafiz_item_for_full_cycle(rev)
        elif rev.mode_id == NEW_MEMORIZATION_MODE_ID:
            update_hafiz_item_for_new_memorization(rev)
        elif rev.mode_id in REP_MODES_CONFIG:
            update_rep_item(rev)
        elif rev.mode_id == SRS_MODE_ID:
            update_hafiz_item_for_srs(rev)

        # update all the non-mode specific columns (including the last_review column)
        populate_hafizs_items_stat_columns(item_id=rev.item_id)

    start_srs_for_bad_streak_items(auth)

    # Change the current date to next date
    hafiz_data.current_date = add_days_to_date(hafiz_data.current_date, 1)
    hafizs.update(hafiz_data)

    return Redirect("/")


@app.get("/report")
def datewise_summary_table_view(auth):
    return main_area(datewise_summary_table(hafiz_id=auth), active="Report", auth=auth)


@app.get("/custom")
def custom_full_cycle_entry_view(auth):
    plan_id = get_current_plan_id()

    if plan_id is None:
        items_gaps_with_limit = []
    else:
        current_plan_item_ids = sorted(
            [
                r.item_id
                for r in revisions(
                    where=f"mode_id = '{FULL_CYCLE_MODE_ID}' AND plan_id = '{plan_id}'"
                )
            ]
        )
        memorized_and_srs_item_ids = [
            i.item_id for i in hafizs_items(where="memorized = 1 AND mode_id IN (1, 5)")
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

        next_item_id = find_next_memorized_item_id(last_added_item_id)

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

    return main_area(
        Div(
            H2("Custom Full Cycle Entry"),
            (
                Table(
                    Thead(
                        Tr(
                            Th("Next"),
                            Th("Entry"),
                        )
                    ),
                    Tbody(*map(render_overall_row, items_gaps_with_limit)),
                    id="full_cycle_link_table",
                )
                if len(items_gaps_with_limit) > 0
                else Div(id="full_cycle_link_table")
            ),
            custom_entry_inputs(auth, plan_id),
            cls="space-y-2",
        ),
        active="Custom",
        auth=auth,
    )


# This route is responsible for adding and deleting record for all the summary table on the home page
# and update the review dates for that item_id
@app.post("/add/{item_id}")
def update_status_from_index(
    auth,
    date: str,
    item_id: str,
    mode_id: int,
    rating: int,
    is_checked: bool = False,
    plan_id: int = None,
):
    # Add or update the revision record
    add_revision_record(
        item_id=item_id,
        mode_id=mode_id,
        revision_date=date,
        rating=rating,
        plan_id=plan_id,
    )

    # Determine route name from mode_id
    mode_to_route = {
        FULL_CYCLE_MODE_ID: "full_cycle",
        NEW_MEMORIZATION_MODE_ID: "new_memorization",
        DAILY_REPS_MODE_ID: "daily_reps",
        WEEKLY_REPS_MODE_ID: "weekly_reps",
        SRS_MODE_ID: "srs",
    }
    route = mode_to_route[mode_id]

    # Get item data and current date
    item = items[int(item_id)]
    current_date = get_current_date(auth)

    # Return the updated row
    return render_range_row(item, route, current_date, mode_id, plan_id, rating)


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
