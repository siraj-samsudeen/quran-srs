from fasthtml.common import *
from constants import *
from app.common_function import *
from app.fixed_reps import REP_MODES_CONFIG, MODE_TO_THRESHOLD_COLUMN
from database import *


new_memorization_app, rt = create_app_with_auth()


def update_hafiz_item_for_new_memorization(rev, mode_code=None, rep_count=None, current_date=None):
    """
    Update hafiz_item after new memorization revision (called by Close Date).

    Args:
        rev: The revision record
        mode_code: Target rep mode (defaults to DAILY_REPS_MODE_CODE)
        rep_count: Custom repetition threshold (defaults to mode's default)
        current_date: Current date for scheduling (optional)
    """
    hafiz_item_details = get_hafizs_items(rev.item_id)
    if hafiz_item_details is None:
        return  # Skip if no hafiz_items record exists

    target_mode = mode_code or DAILY_REPS_MODE_CODE
    hafiz_item_details.mode_code = target_mode
    hafiz_item_details.memorized = True

    # Set custom threshold if provided
    if rep_count is not None and target_mode in MODE_TO_THRESHOLD_COLUMN:
        column = MODE_TO_THRESHOLD_COLUMN[target_mode]
        setattr(hafiz_item_details, column, int(rep_count))

    # Set next_review and next_interval based on mode
    if target_mode in REP_MODES_CONFIG and current_date:
        config = REP_MODES_CONFIG[target_mode]
        hafiz_item_details.next_interval = config["interval"]
        hafiz_item_details.next_review = add_days_to_date(current_date, config["interval"])
    elif target_mode == FULL_CYCLE_MODE_CODE:
        hafiz_item_details.next_interval = None
        hafiz_item_details.next_review = None

    hafizs_items.update(hafiz_item_details)


# === Routes for NM Tab on Home Page ===


@new_memorization_app.post("/toggle/{item_id}")
def toggle_new_memorization(sess, auth, item_id: int, date: str):
    """Toggle memorization status for a single item in the NM tab."""
    existing = revisions(
        where=f"item_id = {item_id} AND mode_code = '{NEW_MEMORIZATION_MODE_CODE}' AND revision_date = '{date}' AND hafiz_id = {auth}"
    )

    if existing:
        # Uncheck: delete the revision
        revisions.delete(existing[0].id)
    else:
        # Check: create revision with rating=1 (Good)
        revisions.insert(
            hafiz_id=auth,
            item_id=item_id,
            revision_date=date,
            rating=1,
            mode_code=NEW_MEMORIZATION_MODE_CODE,
        )

    # Return updated table
    current_page = sess.get("pagination", {}).get(NEW_MEMORIZATION_MODE_CODE, 1)
    return make_new_memorization_table(
        auth=auth,
        table_only=True,
        page=current_page,
        items_per_page=ITEMS_PER_PAGE,
    )


@new_memorization_app.post("/bulk_mark")
def bulk_mark_as_memorized(sess, auth, item_ids: list[str], date: str):
    """Bulk mark items as newly memorized."""
    for item_id in item_ids:
        # Only create revision if it doesn't exist
        existing = revisions(
            where=f"item_id = {item_id} AND mode_code = '{NEW_MEMORIZATION_MODE_CODE}' AND revision_date = '{date}' AND hafiz_id = {auth}"
        )
        if not existing:
            revisions.insert(
                hafiz_id=auth,
                item_id=int(item_id),
                revision_date=date,
                rating=1,
                mode_code=NEW_MEMORIZATION_MODE_CODE,
            )

    # Return updated table
    current_page = sess.get("pagination", {}).get(NEW_MEMORIZATION_MODE_CODE, 1)
    return make_new_memorization_table(
        auth=auth,
        table_only=True,
        page=current_page,
        items_per_page=ITEMS_PER_PAGE,
    )


@new_memorization_app.post("/bulk_mark_memorized")
def bulk_mark_memorized(sess, auth, item_ids: list[str], date: str):
    """Bulk mark items as permanently memorized (skip New Memorization workflow)."""
    for item_id in item_ids:
        item_id_int = int(item_id)
        # Create revision with FULL_CYCLE_MODE_CODE
        revisions.insert(
            hafiz_id=auth,
            item_id=item_id_int,
            revision_date=date,
            rating=1,
            mode_code=FULL_CYCLE_MODE_CODE,
        )
        # Immediately mark as memorized in full cycle mode
        hafiz_item = get_hafizs_items(item_id_int)
        if hafiz_item:
            hafiz_item.memorized = True
            hafiz_item.mode_code = FULL_CYCLE_MODE_CODE
            hafizs_items.update(hafiz_item)

    # Return updated table
    current_page = sess.get("pagination", {}).get(NEW_MEMORIZATION_MODE_CODE, 1)
    return make_new_memorization_table(
        auth=auth,
        table_only=True,
        page=current_page,
        items_per_page=ITEMS_PER_PAGE,
    )
