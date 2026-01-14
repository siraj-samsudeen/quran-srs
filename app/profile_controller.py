"""Profile controller - Routes and request handling for profile management."""

from fasthtml.common import *
from monsterui.all import *
from utils import add_days_to_date
from app.common_function import (
    create_app_with_auth,
    main_area,
    error_toast,
    success_toast,
    get_current_date,
    get_mode_name,
)
from app.profile_model import apply_status_to_item
from app.profile_view import (
    render_stats_cards,
    render_profile_table,
    render_rep_config_modal,
    render_tab_filter,
)
from app.fixed_reps import REP_MODES_CONFIG, MODE_TO_THRESHOLD_COLUMN
from constants import (
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
    SRS_MODE_CODE,
)
from database import hafizs_items

profile_app, rt = create_app_with_auth()


@profile_app.get("/")
def profile_home(auth, request, status_filter: str = None):
    """Main profile page."""
    # For HTMX requests, return only the table (e.g., filter changes)
    if request.headers.get("HX-Request"):
        return render_profile_table(auth, status_filter)

    # Configuration modal (DaisyUI dialog)
    config_modal = Dialog(
        Div(
            Form(
                Button("✕", cls="btn btn-sm btn-circle btn-ghost absolute right-2 top-2", method="dialog"),
                method="dialog",
            ),
            id="config-modal",
        ),
        id="config-modal",
        cls="modal",
    )

    # Main profile page
    return main_area(
        render_tab_filter(auth, status_filter, hx_swap_oob=False),
        render_profile_table(auth, status_filter),
        config_modal,
    )


@profile_app.post("/bulk/set_status")
async def bulk_set_status(req: Request, auth, sess, status: str, status_filter: str = None):
    """Bulk set status for selected items via HTMX form submission."""
    form_data = await req.form()
    item_ids = [int(id) for id in form_data.getlist("hafiz_item_ids") if id]

    if not item_ids:
        error_toast(sess, "No items selected")
        return render_profile_table(auth, status_filter)

    current_date = get_current_date(auth)
    updated = 0

    for hafiz_item_id in item_ids:
        try:
            hafiz_item = hafizs_items[hafiz_item_id]
            if hafiz_item.hafiz_id != auth:
                continue

            if apply_status_to_item(hafiz_item, status, current_date):
                hafizs_items.update(hafiz_item)
                updated += 1
        except (NotFoundError, ValueError):
            continue

    if updated > 0:
        # We need status_label, we can get it from helper or model
        from app.profile_model import get_status_display
        _, status_label = get_status_display(status)
        success_toast(sess, f"Marked {updated} page(s) as {status_label}")
    else:
        error_toast(sess, "No pages were updated")

    # Return table + tabs with OOB swap to update counts
    return (
        render_profile_table(auth, status_filter),
        render_tab_filter(auth, status_filter, hx_swap_oob=True),
    )


@profile_app.post("/load_more")
def load_more_rows(auth, status_filter: str = None, offset: int = 0):
    """Load more rows via Load More button."""
    from app.common_model import get_page_count
    from app.profile_model import get_profile_data
    from app.components.tables import JuzHeader, SurahHeader
    from app.profile_view import render_profile_row
    
    rows = get_profile_data(auth, status_filter)
    item_ids = [row["item_id"] for row in rows]
    total_items = len(rows)
    
    items_per_page = 25
    start_idx = offset
    end_idx = offset + items_per_page
    paginated_rows = rows[start_idx:end_idx]
    has_more = end_idx < total_items
    
    # Build table rows with juz and surah headers
    body_rows = []
    current_juz_number = None
    current_surah_id = None
    
    for row in paginated_rows:
        juz_number = row["juz_number"]
        surah_id = row["surah_id"]
        
        # Add juz header when juz changes
        if juz_number != current_juz_number:
            current_juz_number = juz_number
            body_rows.append(JuzHeader(juz_number, colspan=6))
            current_surah_id = None
        
        # Add surah header when surah changes
        if surah_id != current_surah_id:
            current_surah_id = surah_id
            body_rows.append(SurahHeader(surah_id, juz_number, colspan=6))
        
        body_rows.append(render_profile_row(row, status_filter, hafiz_id=auth))
    
    # Add Load More button if there are more items
    content = body_rows
    if has_more:
        filter_param = f"&status_filter={status_filter}" if status_filter else ""
        next_offset = offset + items_per_page
        content.append(
            Div(
                Button(
                    "Load More",
                    type="button",
                    cls="btn btn-outline btn-sm",
                    hx_post=f"/profile/load_more?offset={next_offset}{filter_param}",
                    hx_target="#profile-table-container",
                    hx_swap="beforeend",
                ),
                cls="flex justify-center py-4",
            )
        )
    
    return tuple(content)


@profile_app.get("/configure_reps/{hafiz_item_id}")
def load_rep_config_modal(hafiz_item_id: int, auth):
    """Load the rep configuration modal for a specific hafiz_item."""
    try:
        hafiz_item = hafizs_items[hafiz_item_id]
    except NotFoundError:
        return P("Item not found", cls="text-red-500")

    if hafiz_item.hafiz_id != auth:
        return P("Unauthorized", cls="text-red-500")

    return render_rep_config_modal(hafiz_item_id, auth, hafiz_item)


@profile_app.post("/configure_reps")
async def configure_reps(req: Request, auth, sess):
    """Handle rep configuration for one or multiple items."""
    form_data = await req.form()

    hafiz_item_ids = form_data.getlist("hafiz_item_id")
    if not hafiz_item_ids:
        hafiz_item_id = form_data.get("hafiz_item_id")
        if hafiz_item_id:
            hafiz_item_ids = [hafiz_item_id]

    mode_code = form_data.get("mode_code")
    rep_count_raw = form_data.get("rep_count")

    # Parse rep_count: empty string -> None, otherwise int (including 0)
    rep_count = None
    if rep_count_raw is not None and rep_count_raw != "":
        try:
            rep_count = int(rep_count_raw)
        except ValueError:
            pass

    # Check for advanced mode rep counts
    advanced_rep_counts = {}
    for mode in [DAILY_REPS_MODE_CODE, WEEKLY_REPS_MODE_CODE, FORTNIGHTLY_REPS_MODE_CODE, MONTHLY_REPS_MODE_CODE]:
        count_raw = form_data.get(f"rep_count_{mode}")
        if count_raw is not None and count_raw != "":
            try:
                advanced_rep_counts[mode] = int(count_raw)
            except ValueError:
                pass

    if not hafiz_item_ids or not mode_code:
        error_toast(sess, "Missing required parameters")
        return RedirectResponse("/profile/table", status_code=303)

    current_date = get_current_date(auth)
    updated_count = 0

    for item_id_str in hafiz_item_ids:
        try:
            hafiz_item_id = int(item_id_str)
            hafiz_item = hafizs_items[hafiz_item_id]

            if hafiz_item.hafiz_id != auth:
                continue

            # Update mode code
            hafiz_item.mode_code = mode_code

            # Update custom thresholds
            if advanced_rep_counts:
                # Advanced mode: set all thresholds
                hafiz_item.custom_daily_threshold = advanced_rep_counts.get(DAILY_REPS_MODE_CODE)
                hafiz_item.custom_weekly_threshold = advanced_rep_counts.get(WEEKLY_REPS_MODE_CODE)
                hafiz_item.custom_fortnightly_threshold = advanced_rep_counts.get(FORTNIGHTLY_REPS_MODE_CODE)
                hafiz_item.custom_monthly_threshold = advanced_rep_counts.get(MONTHLY_REPS_MODE_CODE)
            elif rep_count is not None:
                # Simple mode: only set threshold for selected mode (including 0)
                column = MODE_TO_THRESHOLD_COLUMN.get(mode_code)
                if column:
                    setattr(hafiz_item, column, rep_count)

            # Set next_review and next_interval based on mode
            if mode_code in REP_MODES_CONFIG:
                config = REP_MODES_CONFIG[mode_code]
                hafiz_item.next_interval = config["interval"]
                hafiz_item.next_review = add_days_to_date(current_date, config["interval"])
            elif mode_code == FULL_CYCLE_MODE_CODE:
                hafiz_item.next_interval = None
                hafiz_item.next_review = None

            hafizs_items.update(hafiz_item)
            updated_count += 1
        except (ValueError, NotFoundError):
            continue

    if updated_count > 0:
        success_toast(sess, f"Updated configuration for {updated_count} page(s)")
    else:
        error_toast(sess, "No pages were updated")

    return RedirectResponse("/profile/table", status_code=303)


@profile_app.post("/quick_change_mode/{hafiz_item_id}")
def quick_change_mode(hafiz_item_id: int, mode_code: str, auth, sess):
    """Quick inline mode change from the profile page dropdown."""
    try:
        hafiz_item = hafizs_items[hafiz_item_id]
    except NotFoundError:
        error_toast(sess, "Item not found")
        return Response(status_code=204)

    if hafiz_item.hafiz_id != auth:
        error_toast(sess, "Unauthorized")
        return Response(status_code=204)

    current_date = get_current_date(auth)

    # Update mode code
    hafiz_item.mode_code = mode_code

    # Set next_review and next_interval based on mode
    if mode_code in REP_MODES_CONFIG:
        config = REP_MODES_CONFIG[mode_code]
        hafiz_item.next_interval = config["interval"]
        hafiz_item.next_review = add_days_to_date(current_date, config["interval"])
    elif mode_code == FULL_CYCLE_MODE_CODE:
        hafiz_item.next_interval = None
        hafiz_item.next_review = None

    hafizs_items.update(hafiz_item)
    success_toast(sess, f"Mode changed to {get_mode_name(mode_code)}")
    return Response(status_code=204)


@profile_app.post("/update_threshold/{hafiz_item_id}")
def update_threshold(hafiz_item_id: int, threshold: int, auth, sess):
    """Update the threshold for the current mode inline."""
    try:
        hafiz_item = hafizs_items[hafiz_item_id]
    except NotFoundError:
        error_toast(sess, "Item not found")
        return Response(status_code=204)

    if hafiz_item.hafiz_id != auth:
        error_toast(sess, "Unauthorized")
        return Response(status_code=204)

    # Set custom threshold for current mode
    mode_code = hafiz_item.mode_code
    if mode_code in MODE_TO_THRESHOLD_COLUMN:
        column = MODE_TO_THRESHOLD_COLUMN[mode_code]
        setattr(hafiz_item, column, threshold)
        hafizs_items.update(hafiz_item)
        success_toast(sess, f"Threshold updated to {threshold}")
    else:
        error_toast(sess, "Cannot set threshold for this mode")

    return Response(status_code=204)


@profile_app.post("/graduate_item/{hafiz_item_id}")
def graduate_item(hafiz_item_id: int, target_mode: str, auth, sess):
    """Graduate an item to a target mode."""
    try:
        hafiz_item = hafizs_items[hafiz_item_id]
    except NotFoundError:
        error_toast(sess, "Item not found")
        return Response(status_code=204)

    if hafiz_item.hafiz_id != auth:
        error_toast(sess, "Unauthorized")
        return Response(status_code=204)

    current_date = get_current_date(auth)
    old_mode = hafiz_item.mode_code

    # Update mode code
    hafiz_item.mode_code = target_mode

    # Set next_review and next_interval based on target mode
    if target_mode in REP_MODES_CONFIG:
        config = REP_MODES_CONFIG[target_mode]
        hafiz_item.next_interval = config["interval"]
        hafiz_item.next_review = add_days_to_date(current_date, config["interval"])
    elif target_mode == FULL_CYCLE_MODE_CODE:
        hafiz_item.memorized = True
        hafiz_item.next_interval = None
        hafiz_item.next_review = None

    hafizs_items.update(hafiz_item)
    success_toast(sess, f"Graduated from {get_mode_name(old_mode)} to {get_mode_name(target_mode)}")
    return Response(status_code=204)
