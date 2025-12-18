import json
from starlette.responses import JSONResponse

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
    render_mode_tabulator,
    render_nm_tabulator,
    render_report_tabulator,
    get_pages_revised,
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
def index(auth):
    # Build mode panels using Tabulator - each returns (mode_code, panel) tuple
    # Tabulator loads data via AJAX and shows placeholder when empty
    mode_panels = [
        (NEW_MEMORIZATION_MODE_CODE, render_nm_tabulator()),
        (FULL_CYCLE_MODE_CODE, render_mode_tabulator(FULL_CYCLE_MODE_CODE)),
        (SRS_MODE_CODE, render_mode_tabulator(SRS_MODE_CODE)),
        (DAILY_REPS_MODE_CODE, render_mode_tabulator(DAILY_REPS_MODE_CODE)),
        (WEEKLY_REPS_MODE_CODE, render_mode_tabulator(WEEKLY_REPS_MODE_CODE)),
        (FORTNIGHTLY_REPS_MODE_CODE, render_mode_tabulator(FORTNIGHTLY_REPS_MODE_CODE)),
        (MONTHLY_REPS_MODE_CODE, render_mode_tabulator(MONTHLY_REPS_MODE_CODE)),
    ]

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

    header = DivLAligned(
        Div(
            render_current_date(auth),
            render_pages_revised_indicator(auth),
            cls="flex flex-col sm:flex-row sm:gap-4 sm:items-center",
        ),
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
def change_the_current_date(auth, skip_enabled: str = None, skip_to_date: str = None):
    hafiz_data = hafizs[auth]

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
    return main_area(render_report_tabulator(), active="Report", auth=auth)


# === JSON API for Tabulator ===


@app.get("/api/mode/{mode_code}/items")
def get_mode_items_json(auth, mode_code: str):
    """Return mode items as JSON for Tabulator table.

    Supports: FC, SR, DR, WR, FR, MR modes.
    NM mode has separate API at /api/new_memorization/items
    """
    # Validate mode_code - NM has separate handling
    if mode_code not in MODE_PREDICATES:
        return JSONResponse(
            {"error": f"Invalid mode_code: {mode_code}. Use /api/new_memorization/items for NM mode."},
            status_code=400
        )

    current_date = get_current_date(auth)
    plan_id = get_current_plan_id()

    # Query items using existing mode filtering logic
    qry = f"""
        SELECT hafizs_items.item_id, items.surah_name, items.surah_id, items.start_text, items.page_id,
               hafizs_items.next_review, hafizs_items.last_review, hafizs_items.mode_code,
               hafizs_items.memorized, hafizs_items.page_number
        FROM hafizs_items
        LEFT JOIN items on hafizs_items.item_id = items.id
        WHERE {get_mode_condition(mode_code)} AND hafizs_items.hafiz_id = {auth}
        ORDER BY hafizs_items.item_id ASC
    """
    mode_specific_records = db.q(qry)

    # Filter using named predicates
    predicate = MODE_PREDICATES[mode_code]
    filtered_records = [
        item for item in mode_specific_records
        if predicate(item, current_date)
    ]

    # Get unique item_ids
    item_ids = list(dict.fromkeys(record["item_id"] for record in filtered_records))

    # Handle Full Cycle mode special case
    is_plan_finished = False
    if mode_code == FULL_CYCLE_MODE_CODE:
        is_plan_finished, item_ids = get_full_review_item_ids(
            auth=auth,
            mode_specific_hafizs_items_records=mode_specific_records,
            item_ids=item_ids,
        )

    # Handle SRS exclusion zone
    if mode_code == SRS_MODE_CODE:
        exclude_start_page = get_last_added_full_cycle_page(auth)
        if exclude_start_page is not None:
            exclude_end_page = exclude_start_page + SRS_EXCLUSION_ZONE_PAGES
            filtered_records = [
                r for r in filtered_records
                if r["page_number"] < exclude_start_page or r["page_number"] > exclude_end_page
            ]
            item_ids = list(dict.fromkeys(r["item_id"] for r in filtered_records))

    # Query today's revisions for these items
    plan_condition = f"AND plan_id = {plan_id}" if plan_id else ""
    if item_ids:
        today_revisions = revisions(
            where=f"revision_date = '{current_date}' AND item_id IN ({', '.join(map(str, item_ids))}) AND {get_mode_condition(mode_code)} {plan_condition}"
        )
    else:
        today_revisions = []
    revisions_lookup = {rev.item_id: rev for rev in today_revisions}

    # Build response data with consecutive page tracking
    data = []
    prev_page_id = None
    current_surah_id = None

    for item_id in item_ids:
        item = items[item_id]
        revision = revisions_lookup.get(item_id)

        # Track consecutive pages for hiding start text
        is_consecutive = prev_page_id is not None and item.page_id == prev_page_id + 1
        # Reset on surah change
        if item.surah_id != current_surah_id:
            current_surah_id = item.surah_id
            is_consecutive = False

        data.append({
            "item_id": item_id,
            "page": get_page_number(item_id),
            "surah": item.surah_name,
            "surah_id": item.surah_id,
            "juz": get_juz_name(item_id=item_id),
            "start_text": item.start_text or "-",
            "rating": revision.rating if revision else None,
            "revision_id": revision.id if revision else None,
            "is_consecutive": is_consecutive,
        })
        prev_page_id = item.page_id

    return JSONResponse({
        "items": data,
        "total": len(data),
        "plan_id": plan_id,
        "current_date": current_date,
        "is_plan_finished": is_plan_finished,
    })


@app.post("/api/mode/{mode_code}/rate")
async def rate_item_json(req: Request, auth, mode_code: str):
    """Rate a single item via JSON API for Tabulator.

    When rating is null/None, deletes the existing revision (unrate).
    Otherwise, adds or updates the revision record.
    """
    payload, error = await parse_json_body(req, required_fields=["item_id"])
    if error:
        return error

    item_id = payload["item_id"]
    rating = payload.get("rating")  # Can be None for unrating
    plan_id = payload.get("plan_id")

    current_date = get_current_date(auth)

    if rating is None:
        # Unrate: delete the existing revision for this item/date/mode/plan
        plan_condition = f"AND plan_id = {plan_id}" if plan_id else ""
        existing_revisions = revisions(
            where=f"item_id = {item_id} AND mode_code = '{mode_code}' AND revision_date = '{current_date}' {plan_condition}"
        )
        for rev in existing_revisions:
            revisions.delete(rev.id)

        stats = get_pages_revised_stats(auth, current_date)
        return JSONResponse({
            "success": True,
            "revision_id": None,
            "rating": None,
            **stats,
        })

    # Add or update the revision record
    revision = add_revision_record(
        item_id=item_id,
        mode_code=mode_code,
        revision_date=current_date,
        rating=rating,
        plan_id=plan_id,
    )

    stats = get_pages_revised_stats(auth, current_date)
    return JSONResponse({
        "success": True,
        "revision_id": revision.id,
        "rating": revision.rating,
        **stats,
    })


@app.post("/api/mode/{mode_code}/bulk_rate")
async def bulk_rate_items_json(req: Request, auth, mode_code: str):
    """Bulk rate multiple items via JSON API for Tabulator."""
    payload, error = await parse_json_body(req, required_fields=["rating"])
    if error:
        return error

    item_ids = payload.get("item_ids", [])
    rating = payload["rating"]
    plan_id = payload.get("plan_id")

    if not item_ids:
        return api_error_response("Missing item_ids")

    current_date = get_current_date(auth)
    rated_count = 0

    for item_id in item_ids:
        add_revision_record(
            item_id=item_id,
            mode_code=mode_code,
            revision_date=current_date,
            rating=rating,
            plan_id=plan_id,
        )
        rated_count += 1

    stats = get_pages_revised_stats(auth, current_date)
    return JSONResponse({
        "success": True,
        "rated_count": rated_count,
        **stats,
    })


@app.get("/api/new_memorization/items")
def get_nm_items_json(auth):
    """Return New Memorization items as JSON for Tabulator table."""
    current_date = get_current_date(auth)

    # Query non-memorized items
    qry = f"""
        SELECT hafizs_items.item_id, items.surah_name, items.surah_id, items.start_text, items.page_id,
               hafizs_items.page_number, hafizs_items.memorized
        FROM hafizs_items
        LEFT JOIN items on hafizs_items.item_id = items.id
        WHERE (hafizs_items.memorized = 0 OR hafizs_items.memorized IS NULL)
              AND hafizs_items.hafiz_id = {auth}
        ORDER BY hafizs_items.item_id ASC
    """
    records = db.q(qry)

    # Get unique item_ids
    item_ids = list(dict.fromkeys(record["item_id"] for record in records))

    # Query today's NM revisions (items marked as memorized today)
    if item_ids:
        today_revisions = revisions(
            where=f"revision_date = '{current_date}' AND item_id IN ({', '.join(map(str, item_ids))}) AND mode_code = '{NEW_MEMORIZATION_MODE_CODE}'"
        )
    else:
        today_revisions = []
    revisions_lookup = {rev.item_id: rev for rev in today_revisions}

    # Build response data
    data = []
    prev_page_id = None
    current_surah_id = None

    for item_id in item_ids:
        item = items[item_id]
        revision = revisions_lookup.get(item_id)

        # Track consecutive pages
        is_consecutive = prev_page_id is not None and item.page_id == prev_page_id + 1
        if item.surah_id != current_surah_id:
            current_surah_id = item.surah_id
            is_consecutive = False

        data.append({
            "item_id": item_id,
            "page": get_page_number(item_id),
            "surah": item.surah_name,
            "surah_id": item.surah_id,
            "juz": get_juz_name(item_id=item_id),
            "start_text": item.start_text or "-",
            "is_memorized_today": revision is not None,
            "revision_id": revision.id if revision else None,
            "is_consecutive": is_consecutive,
        })
        prev_page_id = item.page_id

    return JSONResponse({
        "items": data,
        "total": len(data),
        "current_date": current_date,
    })


@app.post("/api/new_memorization/toggle")
async def toggle_nm_item_json(req: Request, auth):
    """Toggle memorization status for a single NM item via JSON API."""
    payload, error = await parse_json_body(req, required_fields=["item_id"])
    if error:
        return error

    item_id = payload["item_id"]

    current_date = get_current_date(auth)

    # Check if revision exists
    existing = revisions(
        where=f"item_id = {item_id} AND mode_code = '{NEW_MEMORIZATION_MODE_CODE}' AND revision_date = '{current_date}' AND hafiz_id = {auth}"
    )

    if existing:
        # Uncheck: delete the revision
        revisions.delete(existing[0].id)
        is_memorized_today = False
        revision_id = None
    else:
        # Check: create revision with rating=1 (Good)
        rev = revisions.insert(
            hafiz_id=auth,
            item_id=item_id,
            revision_date=current_date,
            rating=1,
            mode_code=NEW_MEMORIZATION_MODE_CODE,
        )
        is_memorized_today = True
        revision_id = rev.id

    return JSONResponse({
        "success": True,
        "item_id": item_id,
        "is_memorized_today": is_memorized_today,
        "revision_id": revision_id,
    })


@app.post("/api/new_memorization/bulk_mark")
async def bulk_mark_nm_items_json(req: Request, auth):
    """Bulk mark items as newly memorized via JSON API."""
    payload, error = await parse_json_body(req)
    if error:
        return error

    item_ids = payload.get("item_ids", [])
    if not item_ids:
        return api_error_response("Missing item_ids")

    current_date = get_current_date(auth)
    marked_count = 0

    for item_id in item_ids:
        # Only create revision if it doesn't exist
        existing = revisions(
            where=f"item_id = {item_id} AND mode_code = '{NEW_MEMORIZATION_MODE_CODE}' AND revision_date = '{current_date}' AND hafiz_id = {auth}"
        )
        if not existing:
            revisions.insert(
                hafiz_id=auth,
                item_id=int(item_id),
                revision_date=current_date,
                rating=1,
                mode_code=NEW_MEMORIZATION_MODE_CODE,
            )
            marked_count += 1

    return JSONResponse({
        "success": True,
        "marked_count": marked_count,
    })


# === Revisions API ===

@app.get("/api/revisions")
def get_revisions_json(auth, mode_code: str = None, date_from: str = None, date_to: str = None):
    """Return revisions as JSON for Tabulator table with optional filters."""
    # Build where clause with filters
    where_parts = [f"hafiz_id = {auth}"]
    if mode_code:
        where_parts.append(f"mode_code = '{mode_code}'")
    if date_from:
        where_parts.append(f"revision_date >= '{date_from}'")
    if date_to:
        where_parts.append(f"revision_date <= '{date_to}'")

    where_clause = " AND ".join(where_parts)

    # Query revisions with item details
    qry = f"""
        SELECT revisions.id, revisions.item_id, revisions.mode_code, revisions.plan_id,
               revisions.rating, revisions.revision_date, items.page_id, items.surah_name
        FROM revisions
        LEFT JOIN items ON revisions.item_id = items.id
        WHERE {where_clause}
        ORDER BY revisions.id DESC
    """
    records = db.q(qry)

    data = []
    for rec in records:
        data.append({
            "id": rec["id"],
            "item_id": rec["item_id"],
            "page": rec["page_id"],
            "surah": rec["surah_name"],
            "mode_code": rec["mode_code"],
            "plan_id": rec["plan_id"],
            "rating": rec["rating"],
            "revision_date": rec["revision_date"],
        })

    return JSONResponse({
        "items": data,
        "total": len(data),
    })


# === Datewise Report API ===

@app.get("/api/report")
def get_report_json(auth):
    """Return datewise revision summary as JSON for Tabulator table."""
    from collections import defaultdict
    from utils import compact_format

    # Get all revisions grouped by date and mode
    qry = f"""
        SELECT revisions.id, revisions.revision_date, revisions.mode_code,
               items.page_id, items.surah_name
        FROM revisions
        LEFT JOIN items ON revisions.item_id = items.id
        WHERE revisions.hafiz_id = {auth}
        ORDER BY revisions.revision_date DESC, revisions.mode_code ASC
    """
    records = db.q(qry)

    # Group by date and mode
    grouped = defaultdict(lambda: defaultdict(list))
    for rec in records:
        grouped[rec["revision_date"]][rec["mode_code"]].append(rec)

    # Flatten into rows for Tabulator
    data = []
    for date in sorted(grouped.keys(), reverse=True):
        date_total = sum(len(pages) for pages in grouped[date].values())
        for mode_code in sorted(grouped[date].keys()):
            mode_revisions = grouped[date][mode_code]
            page_ids = sorted(set(r["page_id"] for r in mode_revisions))
            page_range = compact_format(page_ids)
            revision_ids = [r["id"] for r in mode_revisions]

            data.append({
                "date": date,
                "date_total": date_total,
                "mode_code": mode_code,
                "count": len(mode_revisions),
                "page_range": page_range,
                "revision_ids": ",".join(map(str, revision_ids)),
            })

    return JSONResponse({
        "items": data,
        "total": len(data),
    })


# === Page Details API ===

@app.get("/api/page_details")
def get_page_details_json(auth):
    """Return page summary as JSON for Tabulator table."""
    # Get all hafizs_items with their revision counts per mode (including FR and MR)
    qry = f"""
        SELECT
            hi.item_id, hi.page_number, hi.mode_code, hi.memorized,
            hi.next_review, hi.next_interval, hi.good_streak, hi.bad_streak,
            i.surah_name, i.start_text,
            (SELECT COUNT(*) FROM revisions r WHERE r.item_id = hi.item_id AND r.mode_code = 'FC') as fc_count,
            (SELECT COUNT(*) FROM revisions r WHERE r.item_id = hi.item_id AND r.mode_code = 'SR') as sr_count,
            (SELECT COUNT(*) FROM revisions r WHERE r.item_id = hi.item_id AND r.mode_code = 'DR') as dr_count,
            (SELECT COUNT(*) FROM revisions r WHERE r.item_id = hi.item_id AND r.mode_code = 'WR') as wr_count,
            (SELECT COUNT(*) FROM revisions r WHERE r.item_id = hi.item_id AND r.mode_code = 'FR') as fr_count,
            (SELECT COUNT(*) FROM revisions r WHERE r.item_id = hi.item_id AND r.mode_code = 'MR') as mr_count,
            (SELECT COUNT(*) FROM revisions r WHERE r.item_id = hi.item_id AND r.mode_code = 'NM') as nm_count
        FROM hafizs_items hi
        LEFT JOIN items i ON hi.item_id = i.id
        WHERE hi.hafiz_id = {auth}
        ORDER BY hi.page_number ASC
    """
    records = db.q(qry)

    data = []
    for rec in records:
        data.append({
            "item_id": rec["item_id"],
            "page": rec["page_number"],
            "surah": rec["surah_name"],
            "mode_code": rec["mode_code"] or "-",
            "memorized": rec["memorized"] == 1,
            "next_review": rec["next_review"],
            "next_interval": rec["next_interval"],
            "good_streak": rec["good_streak"] or 0,
            "bad_streak": rec["bad_streak"] or 0,
            "fc_count": rec["fc_count"],
            "sr_count": rec["sr_count"],
            "dr_count": rec["dr_count"],
            "wr_count": rec["wr_count"],
            "fr_count": rec["fr_count"],
            "mr_count": rec["mr_count"],
            "nm_count": rec["nm_count"],
            "total_revisions": rec["fc_count"] + rec["sr_count"] + rec["dr_count"] + rec["wr_count"] + rec["fr_count"] + rec["mr_count"] + rec["nm_count"],
        })

    return JSONResponse({
        "items": data,
        "total": len(data),
    })


# === Page Revision History API ===

@app.get("/api/page_details/{item_id}/history")
def get_page_history_json(auth, item_id: int):
    """Return revision history for a specific page as JSON."""
    qry = f"""
        SELECT r.id, r.revision_date, r.rating, r.mode_code, r.plan_id, r.next_interval,
               m.name as mode_name,
               CASE
                   WHEN LAG(r.revision_date) OVER (ORDER BY r.revision_date, r.id) IS NULL THEN NULL
                   ELSE CAST(
                       JULIANDAY(r.revision_date) - JULIANDAY(LAG(r.revision_date) OVER (ORDER BY r.revision_date, r.id))
                       AS INTEGER
                   )
               END AS interval_since_last
        FROM revisions r
        LEFT JOIN modes m ON r.mode_code = m.code
        WHERE r.item_id = {item_id} AND r.hafiz_id = {auth}
        ORDER BY r.revision_date DESC, r.id DESC
    """
    records = db.q(qry)

    data = []
    for i, rec in enumerate(records):
        data.append({
            "num": len(records) - i,
            "id": rec["id"],
            "date": rec["revision_date"],
            "rating": rec["rating"],
            "mode_code": rec["mode_code"],
            "mode_name": rec["mode_name"],
            "plan_id": rec["plan_id"],
            "next_interval": rec["next_interval"],
            "interval_since_last": rec["interval_since_last"],
        })

    return JSONResponse({
        "items": list(reversed(data)),
        "total": len(data),
    })


serve()
