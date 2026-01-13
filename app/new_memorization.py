from fasthtml.common import *
import fasthtml.common as fh
from monsterui.all import *
from constants import *
from app.common_function import create_app_with_auth, get_current_date, get_page_number, get_juz_name
from app.home_view import render_surah_header
from app.common_model import get_hafizs_items
from utils import add_days_to_date
from app.fixed_reps import REP_MODES_CONFIG, MODE_TO_THRESHOLD_COLUMN
from database import db, items, revisions, hafizs_items


new_memorization_app, rt = create_app_with_auth()


# === New Memorization Table Rendering Functions ===


def render_nm_row(item, current_date, is_memorized_today, prev_page_id=None):
    """Render a single row in the New Memorization table with checkbox."""
    item_id = item.id
    row_id = f"row-NM-{item_id}"

    # Check if this is a consecutive page (hide start text for recall)
    is_consecutive = prev_page_id is not None and item.page_id == prev_page_id + 1

    # Checkbox for marking as memorized
    checkbox = fh.Input(
        type="checkbox",
        name="item_ids",
        value=item_id,
        checked=is_memorized_today,
        cls="checkbox bulk-select-checkbox",
        # Update count when checkbox changes (no HTMX here, bulk action buttons handle submission)
        **{"@change": "count = $root.querySelectorAll('.bulk-select-checkbox:checked').length"},
    )

    # Row background: green if memorized today
    bg_class = "bg-green-100" if is_memorized_today else ""

    return Tr(
        Td(checkbox, cls="w-8 text-center"),
        Td(
            A(
                get_page_number(item_id),
                href=f"/page_details/{item_id}",
                cls="font-mono font-bold hover:underline",
            ),
            cls="w-12 text-center",
        ),
        Td(
            # Hidden text with tap-to-reveal using Alpine.js
            Div(
                Span("● ● ●", cls="text-gray-400 cursor-pointer select-none", x_show="!revealed", **{"@click": "revealed = true"}),
                Span(item.start_text or "-", x_show="revealed", x_cloak=True),
                x_data="{ revealed: false }",
            )
            if is_consecutive
            else Span(item.start_text or "-"),
            cls="text-lg",
        ),
        id=row_id,
        cls=bg_class,
    )


def render_nm_bulk_action_bar(current_date):
    """Render bulk action bar for New Memorization mode.

    Unlike other modes that have Good/Ok/Bad buttons, NM only has
    a single 'Mark as Memorized' button.
    """
    mode_code = NEW_MEMORIZATION_MODE_CODE

    # Select all checkbox - toggles all unchecked items
    select_all_checkbox = Div(
        fh.Input(
            type="checkbox",
            cls="checkbox",
            **{
                "@change": """
                    $root.querySelectorAll('.bulk-select-checkbox:not(:checked)').forEach(cb => {
                        if ($el.checked) cb.checked = true;
                    });
                    if (!$el.checked) {
                        $root.querySelectorAll('.bulk-select-checkbox').forEach(cb => cb.checked = false);
                    }
                    count = $root.querySelectorAll('.bulk-select-checkbox:checked').length
                """,
                ":checked": "count > 0 && count === $root.querySelectorAll('.bulk-select-checkbox').length",
            },
        ),
        Span("Select All", cls="text-sm ml-2", x_show="count < $root.querySelectorAll('.bulk-select-checkbox').length"),
        Span("Clear All", cls="text-sm ml-2", x_show="count === $root.querySelectorAll('.bulk-select-checkbox').length"),
        Span("|", cls="text-gray-300 mx-2"),
        Span(x_text="count", cls="font-bold"),
        cls="flex items-center",
    )

    mark_new_button = Button(
        "Mark as New Memorization",
        hx_post="/new_memorization/bulk_mark",
        hx_vals={"date": current_date},
        hx_include=f"#{mode_code}_tbody [name='item_ids']:checked",
        hx_target=f"#summary_table_{mode_code}",
        hx_swap="outerHTML",
        **{"@click": "count = 0"},
        cls=(ButtonT.secondary, "px-4 py-2"),
    )

    mark_memorized_button = Button(
        "Mark as Memorized",
        hx_post="/new_memorization/bulk_mark_memorized",
        hx_vals={"date": current_date},
        hx_include=f"#{mode_code}_tbody [name='item_ids']:checked",
        hx_target=f"#summary_table_{mode_code}",
        hx_swap="outerHTML",
        **{"@click": "count = 0"},
        cls=(ButtonT.primary, "px-4 py-2"),
    )

    return Div(
        select_all_checkbox,
        Div(
            mark_new_button,
            mark_memorized_button,
            cls="flex gap-2 items-center",
        ),
        id=f"bulk-bar-{mode_code}",
        cls="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg p-3 flex justify-between items-center z-50",
        x_show="count > 0",
        style="display: none",
    )


def make_new_memorization_table(auth, offset=0, items_per_page=None, table_only=False, rows_only=False):
    """Build the New Memorization tab content showing unmemorized pages.

    Shows:
    - Unmemorized items (hafizs_items.memorized = 0)
    - Items marked as memorized today (NM revisions today) - these stay until Close Date
    """
    current_date = get_current_date(auth)
    mode_code = NEW_MEMORIZATION_MODE_CODE

    # Query unmemorized items
    qry = f"""
        SELECT hafizs_items.item_id, hafizs_items.page_number
        FROM hafizs_items
        WHERE hafizs_items.hafiz_id = {auth}
          AND hafizs_items.memorized = 0
        ORDER BY hafizs_items.item_id ASC
    """
    unmemorized_records = db.q(qry)
    unmemorized_item_ids = set(r["item_id"] for r in unmemorized_records)

    # Get today's NM revisions (to show "memorized today" state)
    today_nm_revisions = revisions(
        where=f"revision_date = '{current_date}' AND mode_code = '{NEW_MEMORIZATION_MODE_CODE}' AND hafiz_id = {auth}"
    )
    today_nm_item_ids = set(r.item_id for r in today_nm_revisions)

    # Combine: unmemorized + memorized today (union)
    all_item_ids = sorted(unmemorized_item_ids | today_nm_item_ids)

    # Hide tab entirely if no items to display
    if not all_item_ids:
        return None

    # Infinite scroll batch
    total_items = len(all_item_ids)
    if items_per_page and items_per_page > 0:
        start_idx = offset
        end_idx = offset + items_per_page
        paginated_item_ids = all_item_ids[start_idx:end_idx]
        has_more = end_idx < total_items
    else:
        paginated_item_ids = all_item_ids
        has_more = False

    # Get item details for paginated items
    items_data = [items[item_id] for item_id in paginated_item_ids]

    # Render rows with surah headers
    body_rows = []
    current_surah_id = None
    prev_page_id = None

    for item in items_data:
        # Add surah header when surah changes
        if item.surah_id != current_surah_id:
            current_surah_id = item.surah_id
            juz_number = get_juz_name(item_id=item.id)
            body_rows.append(render_surah_header(current_surah_id, juz_number))
            prev_page_id = None  # Reset consecutive tracking on surah change

        is_memorized_today = item.id in today_nm_item_ids
        row = render_nm_row(item, current_date, is_memorized_today, prev_page_id)
        body_rows.append(row)
        prev_page_id = item.page_id

    # Add infinite scroll trigger to the last data row if more items exist
    if has_more and body_rows:
        for i in range(len(body_rows) - 1, -1, -1):
            row = body_rows[i]
            if hasattr(row, "attrs") and "surah-header" not in row.attrs.get("cls", ""):
                next_offset = offset + items_per_page
                row.attrs.update({
                    "hx-get": f"/page/{mode_code}/more?offset={next_offset}",
                    "hx-trigger": "revealed",
                    "hx-swap": "afterend",
                })
                break

    # Return just the rows for infinite scroll requests
    if rows_only:
        return tuple(body_rows)

    # Empty state
    if not body_rows:
        body_rows = [
            Tr(
                Td(
                    "All pages memorized!",
                    colspan=3,
                    cls="text-center text-gray-500 py-4",
                )
            )
        ]

    bulk_bar = render_nm_bulk_action_bar(current_date)

    table_content = [
        Table(
            Tbody(*body_rows, id=f"{mode_code}_tbody"),
            cls=(TableT.middle, TableT.divider, TableT.sm),
        ),
    ]

    table_content.append(bulk_bar)

    table = Div(
        *table_content,
        id=f"summary_table_{mode_code}",
        x_data="{ count: 0 }",
    )

    if table_only:
        return table
    return (mode_code, table)


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
    return make_new_memorization_table(
        auth=auth,
        table_only=True,
        items_per_page=ITEMS_PER_PAGE,
    )


@new_memorization_app.post("/bulk_mark")
def bulk_mark_as_memorized(auth, item_ids: list[str], date: str):
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

    # Return updated table (reset to first batch)
    return make_new_memorization_table(
        auth=auth,
        table_only=True,
        items_per_page=ITEMS_PER_PAGE,
    )


@new_memorization_app.post("/bulk_mark_memorized")
def bulk_mark_memorized(auth, item_ids: list[str], date: str):
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

    # Return updated table (reset to first batch)
    return make_new_memorization_table(
        auth=auth,
        table_only=True,
        items_per_page=ITEMS_PER_PAGE,
    )
