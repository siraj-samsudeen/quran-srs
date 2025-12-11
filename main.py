from fasthtml.common import *
from monsterui.all import *
from utils import *
import pandas as pd
from app.users_controller import users_app
from app.revision import revision_app
from app.revision_model import cycle_full_cycle_plan_if_completed
from app.new_memorization import (
    new_memorization_app,
    update_hafiz_item_for_new_memorization,
)
from app.admin import admin_app
from app.page_details import page_details_app
from app.profile import profile_app
from app.hafiz_controller import hafiz_app
from app.common_function import *
from database import *
from constants import *
from app.fixed_reps import REP_MODES_CONFIG, update_rep_item
from app.srs_reps import (
    update_hafiz_item_for_srs,
    start_srs_for_ok_and_bad_rating,
)
from app.home_view import (
    datewise_summary_table,
    split_page_range,
    update_hafiz_item_for_full_cycle,
)

ADD_EXTRA_ROWS = 1


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


def get_revision_data(mode_code: str, revision_date: str):
    """Returns the revision count and revision ID for a specific date and mode code."""
    records = revisions(
        where=f"mode_code = '{mode_code}' AND revision_date = '{revision_date}'"
    )
    rev_ids = ",".join(str(r.id) for r in records)
    count = get_page_count(records)
    return count, rev_ids


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


def get_full_cycle_revised_length(current_date):
    plan_id = get_current_plan_id()
    revised_records = revisions(
        where=f"revision_date = '{current_date}' AND mode_code = '{FULL_CYCLE_MODE_CODE}' AND plan_id = {plan_id}"
    )
    return get_page_count(records=revised_records)


def get_full_cycle_limit_and_revised_count(auth):
    current_date = get_current_date(auth)
    page_limit = get_full_cycle_daily_limit(auth)
    revised_count = get_full_cycle_revised_length(current_date)
    if revised_count >= page_limit:
        page_limit = revised_count + ADD_EXTRA_ROWS
    return page_limit, revised_count


@rt
def index(auth, sess):

    # Set the full cycle progress, for auto adding extra rows
    page_limit, revised_count = get_full_cycle_limit_and_revised_count(auth)
    sess["full_cycle_progress"] = {
        "limit": page_limit,
        "revised": revised_count,
    }

    # Build panels - each returns (mode_code, panel) tuple
    mode_panels = [
        make_summary_table(FULL_CYCLE_MODE_CODE, auth, total_page_count=page_limit),
        make_summary_table(SRS_MODE_CODE, auth),
        make_summary_table(DAILY_REPS_MODE_CODE, auth),
        make_summary_table(WEEKLY_REPS_MODE_CODE, auth),
    ]
    # Filter to only modes with content
    mode_panels = [(code, panel) for code, panel in mode_panels if panel is not None]

    mode_icons = {
        FULL_CYCLE_MODE_CODE: "🔄",
        SRS_MODE_CODE: "🧠",
        DAILY_REPS_MODE_CODE: "☀️",
        WEEKLY_REPS_MODE_CODE: "📅",
    }

    def make_tab_button(mode_code):
        icon = mode_icons.get(mode_code, "")
        return A(
            f"{icon} {get_mode_name(mode_code)}",
            cls="tab",
            role="tab",
            **{
                "@click": f"activeTab = '{mode_code}'",
                ":class": f"activeTab === '{mode_code}' ? 'tab-active [--tab-bg:oklch(var(--p)/0.1)] [--tab-border-color:oklch(var(--p))]' : ''",
            },
        )

    tab_buttons = [make_tab_button(code) for code, _ in mode_panels]
    tab_contents = [
        Div(content, x_show=f"activeTab === '{code}'")
        for code, content in mode_panels
    ]

    header = DivLAligned(
        render_current_date(auth),
        A(
            Button(
                "Close Date",
                data_testid="close-date-btn",
            ),
            href="/close_date",
        ),
    )

    return main_area(
        Div(
            header,
            Div(*tab_buttons, role="tablist", cls="tabs tabs-lifted mt-4"),
            *tab_contents,
            x_data=f"{{ activeTab: '{FULL_CYCLE_MODE_CODE}' }}",
        ),
        active="Home",
        auth=auth,
    )


def update_hafiz_item_for_full_cycle(rev):
    hafiz_item_details = get_hafizs_items(rev.item_id)
    currrent_date = get_current_date(rev.hafiz_id)
    # when a SRS page is revised in full-cycle mode, we need to move the next review of that page using the current next_interval
    if hafiz_item_details.mode_code == SRS_MODE_CODE:
        hafiz_item_details.next_review = add_days_to_date(
            currrent_date, hafiz_item_details.next_interval
        )

    hafiz_item_details.last_interval = get_actual_interval(rev.item_id)
    hafizs_items.update(hafiz_item_details)


@app.get("/close_date")
def close_date_confirmation_page(auth):
    header = render_current_date(auth)
    action_buttons = DivLAligned(
        Button(
            "Confirm",
            hx_post="close_date",
            hx_target="body",
            hx_push_url="true",
            hx_disabled_elt="this",
            cls=(ButtonT.primary, "p-2"),
            data_testid="confirm-close-btn",
        ),
        Button(
            "Cancel",
            onclick="history.back()",
            cls=(ButtonT.default, "p-2"),
        ),
    )
    return main_area(
        Div(header, create_stat_table(auth), action_buttons, cls="space-y-4"),
        active="Home",
        auth=auth,
    )


@app.post("/close_date")
def change_the_current_date(auth):
    hafiz_data = hafizs[auth]

    # Check if many days have elapsed - if so, skip directly to today
    today = current_time()
    days_elapsed = day_diff(hafiz_data.current_date, today)

    if days_elapsed > 1:
        # Skip directly to today instead of processing each day
        hafiz_data.current_date = today
        hafizs.update(hafiz_data)
        return Redirect("/")

    revision_data = revisions(where=f"revision_date = '{hafiz_data.current_date}'")
    for rev in revision_data:
        if rev.mode_code == FULL_CYCLE_MODE_CODE:
            update_hafiz_item_for_full_cycle(rev)
        elif rev.mode_code == NEW_MEMORIZATION_MODE_CODE:
            update_hafiz_item_for_new_memorization(rev)
        elif rev.mode_code in REP_MODES_CONFIG:
            update_rep_item(rev)
        elif rev.mode_code == SRS_MODE_CODE:
            update_hafiz_item_for_srs(rev)

        # update all the non-mode specific columns (including the last_review column)
        populate_hafizs_items_stat_columns(item_id=rev.item_id)

    start_srs_for_ok_and_bad_rating(auth)

    # Check if the full cycle plan is completed, if so close and create a new plan
    cycle_full_cycle_plan_if_completed()

    # Change the current date to next date
    hafiz_data.current_date = add_days_to_date(hafiz_data.current_date, 1)
    hafizs.update(hafiz_data)

    return Redirect("/")


@app.get("/report")
def datewise_summary_table_view(auth):
    return main_area(datewise_summary_table(hafiz_id=auth), active="Report", auth=auth)


def update_full_cycle_progress(sess, page_count):
    if sess["full_cycle_progress"]:
        sess["full_cycle_progress"]["revised"] += page_count


def is_full_cycle_limit_reached(sess):
    if "full_cycle_progress" in sess:
        return (
            sess["full_cycle_progress"]["revised"]
            >= sess["full_cycle_progress"]["limit"]
        )
    return False


def get_full_cycle_limit(sess):
    if sess["full_cycle_progress"]:
        return sess["full_cycle_progress"]["limit"]
    else:
        return 0


def increment_full_cycle_limit(sess):
    if sess["full_cycle_progress"]:
        sess["full_cycle_progress"]["limit"] += ADD_EXTRA_ROWS


# This route is responsible for adding and deleting record for all the summary table on the home page
# and update the review dates for that item_id
@app.post("/add/{item_id}")
def update_status_from_index(
    sess,
    auth,
    date: str,
    item_id: str,
    mode_code: str,
    rating: int,
    plan_id: int = None,
):
    # Add or update the revision record
    revision = add_revision_record(
        item_id=item_id,
        mode_code=mode_code,
        revision_date=date,
        rating=rating,
        plan_id=plan_id,
    )

    # Update the full cycle limit details, to auto add more rows
    if mode_code == FULL_CYCLE_MODE_CODE:
        page_count = get_page_count(item_ids=[item_id])
        update_full_cycle_progress(sess, page_count)
        if is_full_cycle_limit_reached(sess):
            increment_full_cycle_limit(sess)
            return make_summary_table(
                mode_code=mode_code,
                auth=auth,
                total_page_count=get_full_cycle_limit(sess),
            ), HtmxResponseHeaders(
                retarget=f"#{mode_code}_tbody",
                reselect=f"#{mode_code}_tbody",
                reswap="outerHTML",
            )

    # Get item data and current date
    item = items[int(item_id)]
    current_date = get_current_date(auth)

    # Return the updated row
    return render_range_row(
        {
            "item": item,
            "revision": revision,
        },
        current_date,
        mode_code,
        plan_id,
    )


@app.put("/edit/{rev_id}")
def update_revision_rating(
    rev_id: int,
    date: str,
    mode_code: str,
    item_id: int,
    rating: str,
    plan_id: int = None,
):
    record = {
        "item": items[item_id],
    }

    # If the `Select rating` options is selected, delete the revision record
    if rating == "None":
        revisions.delete(rev_id)
        record["revision"] = None
        return render_range_row(
            records=record, current_date=date, mode_code=mode_code, plan_id=plan_id
        )
    else:
        revision = revisions.update({"rating": int(rating)}, rev_id)
        record["revision"] = revision
        return render_range_row(records=record)


@app.post("/bulk_rate")
def bulk_rate(
    sess,
    auth,
    # FastHTML automatically parses the form data - when HTMX posts multiple item_ids values 
    # (from checked checkboxes), FastHTML collects them into a list
    item_ids: list[str],
    rating: int,
    mode_code: str,
    date: str,
    plan_id: str = "",
):
    plan_id_int = int(plan_id) if plan_id else None

    # Add revision records for each item
    for item_id in item_ids:
        add_revision_record(
            item_id=item_id,
            mode_code=mode_code,
            revision_date=date,
            rating=rating,
            plan_id=plan_id_int,
        )

    # Update full cycle progress if applicable
    if mode_code == FULL_CYCLE_MODE_CODE:
        page_count = get_page_count(item_ids=item_ids)
        update_full_cycle_progress(sess, page_count)
        if is_full_cycle_limit_reached(sess):
            increment_full_cycle_limit(sess)

    page_limit, _ = get_full_cycle_limit_and_revised_count(auth)

    return make_summary_table(
        mode_code=mode_code,
        auth=auth,
        total_page_count=page_limit if mode_code == FULL_CYCLE_MODE_CODE else 0,
        table_only=True,
    )


serve()
