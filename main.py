from fasthtml.common import *
from monsterui.all import *
from utils import *
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
    create_stat_table,
    datewise_summary_table,
    update_hafiz_item_for_full_cycle,
    render_pages_revised_indicator,
)


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


@rt
def index(auth, sess):
    # Initialize pagination state if not exists
    if "pagination" not in sess:
        sess["pagination"] = {}

    # Get hafiz's page_size setting (fallback to default)
    current_hafiz = hafizs[auth]
    items_per_page = current_hafiz.page_size or ITEMS_PER_PAGE

    # Helper to get current page for a mode
    def get_page(mode_code):
        return sess["pagination"].get(mode_code, 1)

    # Build panels - each returns (mode_code, panel) tuple
    mode_panels = [
        make_new_memorization_table(
            auth,
            page=get_page(NEW_MEMORIZATION_MODE_CODE),
            items_per_page=ITEMS_PER_PAGE,
        ),
        make_summary_table(
            FULL_CYCLE_MODE_CODE,
            auth,
            page=get_page(FULL_CYCLE_MODE_CODE),
            items_per_page=items_per_page,
        ),
        make_summary_table(
            SRS_MODE_CODE,
            auth,
            page=get_page(SRS_MODE_CODE),
            items_per_page=items_per_page,
        ),
        make_summary_table(
            DAILY_REPS_MODE_CODE,
            auth,
            page=get_page(DAILY_REPS_MODE_CODE),
            items_per_page=items_per_page,
        ),
        make_summary_table(
            WEEKLY_REPS_MODE_CODE,
            auth,
            page=get_page(WEEKLY_REPS_MODE_CODE),
            items_per_page=items_per_page,
        ),
        make_summary_table(
            FORTNIGHTLY_REPS_MODE_CODE,
            auth,
            page=get_page(FORTNIGHTLY_REPS_MODE_CODE),
            items_per_page=ITEMS_PER_PAGE,
        ),
        make_summary_table(
            MONTHLY_REPS_MODE_CODE,
            auth,
            page=get_page(MONTHLY_REPS_MODE_CODE),
            items_per_page=ITEMS_PER_PAGE,
        ),
    ]
    # Filter out modes with no items (make_summary_table returns None for empty modes)
    mode_panels = [panel for panel in mode_panels if panel is not None]

    mode_icons = {
        NEW_MEMORIZATION_MODE_CODE: "🆕",
        FULL_CYCLE_MODE_CODE: "🔄",
        SRS_MODE_CODE: "🧠",
        DAILY_REPS_MODE_CODE: "☀️",
        WEEKLY_REPS_MODE_CODE: "📅",
        FORTNIGHTLY_REPS_MODE_CODE: "📆",
        MONTHLY_REPS_MODE_CODE: "🗓️",
    }

    # Short names for mobile display
    mode_short_names = {
        NEW_MEMORIZATION_MODE_CODE: "New",
        FULL_CYCLE_MODE_CODE: "FC",
        SRS_MODE_CODE: "SRS",
        DAILY_REPS_MODE_CODE: "Daily",
        WEEKLY_REPS_MODE_CODE: "Weekly",
        FORTNIGHTLY_REPS_MODE_CODE: "Fortnight",
        MONTHLY_REPS_MODE_CODE: "Monthly",
    }

    def make_tab_button(mode_code):
        icon = mode_icons.get(mode_code, "")
        full_name = get_mode_name(mode_code)
        short_name = mode_short_names.get(mode_code, mode_code)
        return A(
            Span(icon, cls="mr-1"),
            Span(full_name, cls="hidden sm:inline"),  # Full name on desktop
            Span(short_name, cls="sm:hidden"),  # Short name on mobile
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

    header = Div(
        Div(
            render_current_date(auth),
            render_pages_revised_indicator(auth),
            cls="flex items-center gap-2",
        ),
        A(
            Button(
                "Close Date",
                cls="btn-sm rounded-full",
                data_testid="close-date-btn",
            ),
            href="/close_date",
        ),
        cls="flex justify-between items-center",
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


@app.get("/close_date")
def close_date_confirmation_page(auth):
    hafiz_data = hafizs[auth]
    today = current_time()
    days_elapsed = day_diff(hafiz_data.current_date, today)

    header = render_current_date(auth)

    # Show skip option when more than 1 day has elapsed
    skip_section = None
    if days_elapsed > 1:
        min_date = add_days_to_date(hafiz_data.current_date, 1)
        yesterday = add_days_to_date(today, -1)
        # Build date-to-label mapping for Alpine.js
        date_labels = f"'{today}': 'Today', '{yesterday}': 'Yesterday'"
        current_date = hafiz_data.current_date
        skip_section = Div(
            Input(
                type="checkbox",
                name="skip_enabled",
                value="true",
                cls="checkbox checkbox-primary",
                data_testid="skip-to-today-checkbox",
            ),
            Span(
                cls="ml-2",
                x_text="'Skip ' + daysToSkip + ' days to'",
            ),
            Span(
                cls="ml-3 font-semibold text-primary",
                x_text=f"dateLabels[selectedDate] || new Date(selectedDate).toLocaleDateString('en-US', {{weekday: 'short', month: 'short', day: 'numeric'}})",
            ),
            Input(
                type="date",
                name="skip_to_date",
                value=today,
                min=min_date,
                max=today,
                cls="input input-bordered input-sm w-auto ml-3",
                data_testid="skip-to-date-input",
                **{"@change": "selectedDate = $el.value; daysToSkip = Math.round((new Date($el.value) - new Date(currentDate)) / 86400000)"},
            ),
            cls="flex items-center",
            x_data=f"{{ selectedDate: '{today}', currentDate: '{current_date}', daysToSkip: {days_elapsed}, dateLabels: {{ {date_labels} }} }}",
        )

    action_buttons = DivLAligned(
        Button(
            "Confirm",
            hx_post="close_date",
            hx_target="body",
            hx_push_url="true",
            hx_disabled_elt="this",
            hx_include="[name='skip_enabled'], [name='skip_to_date']",
            cls=(ButtonT.primary, "p-2"),
            data_testid="confirm-close-btn",
        ),
        Button(
            "Cancel",
            onclick="history.back()",
            cls=(ButtonT.default, "p-2"),
        ),
    )

    content = [header, create_stat_table(auth)]
    if skip_section:
        content.append(skip_section)
    content.append(action_buttons)

    return main_area(
        Div(*content, cls="space-y-4"),
        active="Home",
        auth=auth,
    )


@app.post("/close_date")
def change_the_current_date(auth, sess, skip_enabled: str = None, skip_to_date: str = None):
    hafiz_data = hafizs[auth]

    # Reset pagination to page 1 for all modes (items change after close date)
    sess["pagination"] = {}

    # Skip to selected date if checkbox is checked
    if skip_enabled == "true" and skip_to_date:
        hafiz_data.current_date = skip_to_date
        hafizs.update(hafiz_data)
        return Redirect("/")

    revision_data = revisions(where=f"revision_date = '{hafiz_data.current_date}'")
    for rev in revision_data:
        if rev.mode_code == FULL_CYCLE_MODE_CODE:
            update_hafiz_item_for_full_cycle(rev)
        elif rev.mode_code == NEW_MEMORIZATION_MODE_CODE:
            update_hafiz_item_for_new_memorization(rev, current_date=hafiz_data.current_date)
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


@app.get("/page/{mode_code}")
def change_page(sess, auth, mode_code: str, page: int = 1, show_loved_only: str = "false"):
    """Handle pagination for mode-specific tables."""
    # Store current page in session
    if "pagination" not in sess:
        sess["pagination"] = {}
    sess["pagination"][mode_code] = page

    # Store loved filter in session
    if "loved_filter" not in sess:
        sess["loved_filter"] = {}
    loved_only = show_loved_only.lower() == "true"
    sess["loved_filter"][mode_code] = loved_only

    # Get hafiz's page_size setting (fallback to default)
    current_hafiz = hafizs[auth]
    items_per_page = current_hafiz.page_size or ITEMS_PER_PAGE

    # Handle NM mode separately (uses different table function)
    if mode_code == NEW_MEMORIZATION_MODE_CODE:
        return make_new_memorization_table(
            auth=auth,
            table_only=True,
            page=page,
            items_per_page=items_per_page,
        )

    return make_summary_table(
        mode_code=mode_code,
        auth=auth,
        table_only=True,
        page=page,
        items_per_page=items_per_page,
        show_loved_only=loved_only,
    )


# This route is responsible for adding and deleting record for all the summary table on the home page
# and update the review dates for that item_id
@app.post("/add/{item_id}")
def update_status_from_index(
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

    # Get item data and current date
    item = items[int(item_id)]
    current_date = get_current_date(auth)

    # Return the updated row AND the updated indicator (out-of-band swap)
    updated_row = render_range_row(
        {
            "item": item,
            "revision": revision,
        },
        current_date,
        mode_code,
        plan_id,
    )

    # Update the pages revised indicator using out-of-band swap
    updated_indicator = Span(
        *render_pages_revised_indicator(auth).children,
        id="pages-revised-indicator",
        cls="text-sm whitespace-nowrap",
        hx_swap_oob="true",
    )

    return updated_row, updated_indicator


@app.put("/edit/{rev_id}")
def update_revision_rating(
    auth,
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
        updated_row = render_range_row(
            records=record, current_date=date, mode_code=mode_code, plan_id=plan_id
        )
    else:
        revision = revisions.update({"rating": int(rating)}, rev_id)
        record["revision"] = revision
        updated_row = render_range_row(records=record)

    # Update the pages revised indicator using out-of-band swap
    updated_indicator = Span(
        *render_pages_revised_indicator(auth).children,
        id="pages-revised-indicator",
        cls="text-sm whitespace-nowrap",
        hx_swap_oob="true",
    )

    return updated_row, updated_indicator


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

    # Get current page from session
    current_page = sess.get("pagination", {}).get(mode_code, 1)

    # Get hafiz's page_size setting (fallback to default)
    current_hafiz = hafizs[auth]
    items_per_page = current_hafiz.page_size or ITEMS_PER_PAGE

    updated_table = make_summary_table(
        mode_code=mode_code,
        auth=auth,
        table_only=True,
        page=current_page,
        items_per_page=items_per_page,
    )

    # Update the pages revised indicator using out-of-band swap
    updated_indicator = Span(
        *render_pages_revised_indicator(auth).children,
        id="pages-revised-indicator",
        cls="text-sm whitespace-nowrap",
        hx_swap_oob="true",
    )

    return updated_table, updated_indicator


@app.post("/toggle_love/{item_id}")
def toggle_love(auth, item_id: int, mode_code: str, date: str, plan_id: str = ""):
    """Toggle the loved status of a page."""
    from app.common_function import get_hafizs_items, render_range_row, get_current_plan_id

    # Get or create hafizs_items record
    hafiz_item = get_hafizs_items(item_id)
    if hafiz_item:
        # Toggle the loved status
        new_loved = 0 if hafiz_item.loved else 1
        hafizs_items.update({"loved": new_loved}, hafiz_item.id)
        is_loved = bool(new_loved)
    else:
        is_loved = False

    # Get the item and revision data
    item = items[item_id]
    plan_id_int = int(plan_id) if plan_id else None
    current_date = date

    # Get today's revision for this item if it exists
    revision_records = revisions(
        where=f"revision_date = '{current_date}' AND item_id = {item_id} AND mode_code = '{mode_code}'"
    )
    revision = revision_records[0] if revision_records else None

    records = {"item": item, "revision": revision}

    return render_range_row(
        records, current_date, mode_code, plan_id_int, hide_start_text=False, loved=is_loved
    )


serve()
