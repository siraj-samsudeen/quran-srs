from fasthtml.common import *
from monsterui.all import *
from app.common_model import (
    get_page_number, 
    get_surah_name, 
    get_status_display,
    get_mode_icon,
    get_mode_name,
    get_mode_count
)
from database import items
from constants import (
    STATUS_NOT_MEMORIZED,
    STATUS_LEARNING,
    STATUS_REPS,
    STATUS_SOLID,
    STATUS_STRUGGLING,
    NEW_MEMORIZATION_MODE_CODE,
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
    SRS_MODE_CODE,
    GRADUATABLE_MODES,
    DEFAULT_REP_COUNTS
)

def PageDescription(
    item_id,
    link: str = None,
    is_link: bool = True,
    is_bold: bool = True,
    custom_text="",
):
    """
    Renders a description of the page (Page number - Surah name).
    Fetches data from DB using item_id.
    """
    item_description = items[item_id].description
    if not item_description:
        item_description = (
            Span(get_page_number(item_id), cls=TextPresets.bold_sm if is_bold else ""),
            Span(" - ", get_surah_name(item_id=item_id)),
            Span(custom_text) if custom_text else "",
        )

    if not is_link:
        return Span(item_description)
    else:
        # If description exists in DB, it might be "Page 5 - Surah Al-Fatiha"
        # We split it to style the page number differently
        if isinstance(item_description, str) and " " in item_description:
            page, description = item_description.split(" ", maxsplit=1)
        else:
            if isinstance(item_description, tuple):
                 return A(
                    *item_description,
                    href=(f"/page_details/{item_id}" if not link else link),
                    cls=AT.classic,
                )
            page, description = item_description.split(" ", maxsplit=1)

    return A(
        Span(page, cls=TextPresets.bold_lg),
        Br(),
        Span(description),
        href=(f"/page_details/{item_id}" if not link else link),
        cls=AT.classic,
    )


def CountLink(count: int, rev_ids: str):
    """
    Renders a count that links to bulk edit revisions if count > 0.
    """
    if not rev_ids or count == 0:
        return count
    return A(
        count,
        href=f"/revision/bulk_edit?ids={rev_ids}",
        cls=AT.classic,
    )


def StatusBadge(status):
    """
    Return status badge with appropriate color and icon.
    """
    status_colors = {
        STATUS_NOT_MEMORIZED: ("bg-gray-100", "text-gray-600"),
        STATUS_LEARNING: ("bg-green-100", "text-green-700"),
        STATUS_REPS: ("bg-amber-100", "text-amber-700"),
        STATUS_SOLID: ("bg-purple-100", "text-purple-700"),
        STATUS_STRUGGLING: ("bg-red-100", "text-red-700"),
    }
    icon, label = get_status_display(status)
    bg, text = status_colors.get(status, ("bg-gray-100", "text-gray-600"))
    return Span(f"{icon} {label}", cls=f"{bg} {text} px-2 py-0.5 rounded text-xs whitespace-nowrap")


def ModeBadge(mode_code):
    """
    Return mode badge with appropriate color and icon.
    """
    if not mode_code:
        return Span("-", cls="text-gray-400")

    mode_colors = {
        NEW_MEMORIZATION_MODE_CODE: ("bg-green-100", "text-green-700"),
        DAILY_REPS_MODE_CODE: ("bg-yellow-100", "text-yellow-700"),
        WEEKLY_REPS_MODE_CODE: ("bg-amber-100", "text-amber-700"),
        FORTNIGHTLY_REPS_MODE_CODE: ("bg-orange-100", "text-orange-700"),
        MONTHLY_REPS_MODE_CODE: ("bg-orange-200", "text-orange-800"),
        FULL_CYCLE_MODE_CODE: ("bg-purple-100", "text-purple-700"),
        SRS_MODE_CODE: ("bg-red-100", "text-red-700"),
    }
    icon = get_mode_icon(mode_code)
    name = get_mode_name(mode_code)
    bg, text = mode_colors.get(mode_code, ("bg-gray-100", "text-gray-600"))
    return Span(f"{icon} {name}", cls=f"{bg} {text} px-2 py-0.5 rounded text-xs whitespace-nowrap")


def TrendIndicator(today_count, yesterday_count):
    """
    Renders an arrow indicating if today's count is higher, lower, or equal to yesterday.
    """
    difference = today_count - yesterday_count
    
    if difference > 0:
        arrow = "↑"
        color = "text-green-600"
    elif difference < 0:
        arrow = "↓"
        color = "text-red-600"
    else:
        arrow = "="
        color = "text-gray-600"
        
    return Span(
        Span(f"{today_count}", data_testid="pages-today", cls="font-semibold text-lg"),
        Span(" vs ", cls="text-gray-500 text-sm"),
        Span(f"{yesterday_count}", data_testid="pages-yesterday", cls="font-semibold text-lg"),
        Span(f" {arrow}", cls=f"{color} font-bold ml-1", data_testid="pages-indicator"),
        id="pages-revised-indicator",
        cls="whitespace-nowrap",
    )

def ModeAndReps(hafiz_item, mode_code=None):
    """
    Render mode name and rep count (e.g., "☀️ Daily 3/7").
    """
    if isinstance(hafiz_item, dict):
        item_mode_code = mode_code or hafiz_item.get("mode_code")
        item_id = hafiz_item.get("item_id")
        hafiz_id = hafiz_item.get("hafiz_id")
    else:
        item_mode_code = mode_code or hafiz_item.mode_code
        item_id = hafiz_item.item_id
        hafiz_id = hafiz_item.hafiz_id

    if not item_mode_code or item_mode_code not in GRADUATABLE_MODES:
        icon = get_mode_icon(item_mode_code) if item_mode_code else ""
        return Span(f"{icon} {get_mode_name(item_mode_code) if item_mode_code else '-'}")

    # Get custom threshold or default
    threshold_columns = {
        DAILY_REPS_MODE_CODE: "custom_daily_threshold",
        WEEKLY_REPS_MODE_CODE: "custom_weekly_threshold",
        FORTNIGHTLY_REPS_MODE_CODE: "custom_fortnightly_threshold",
        MONTHLY_REPS_MODE_CODE: "custom_monthly_threshold",
    }
    column = threshold_columns.get(item_mode_code)

    if isinstance(hafiz_item, dict):
        custom_threshold = hafiz_item.get(column) if column else None
    else:
        custom_threshold = getattr(hafiz_item, column, None) if column else None

    threshold = custom_threshold if custom_threshold is not None else DEFAULT_REP_COUNTS.get(item_mode_code, 7)

    # Get current count
    current_count = get_mode_count(item_id, item_mode_code, hafiz_id)
    icon = get_mode_icon(item_mode_code)
    mode_name = get_mode_name(item_mode_code)

    # Show mode name with progress: "☀️ Daily 3/7"
    return Span(f"{icon} {mode_name} {current_count}/{threshold}")