from fasthtml.common import *
from monsterui.all import *
from app.common_model import (
    get_page_part_info, 
    get_page_number,
)
from database import surahs
from app.fixed_reps import REP_MODES_CONFIG
from constants import (
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
    SRS_MODE_CODE,
)

def SurahHeader(surah_id, juz_number, colspan=4):
    """
    Render a surah section header row with surah name and juz indicator.
    """
    surah_name = surahs[surah_id].name
    return Tr(
        Td(
            Span(f"📖 {surah_name}", cls="font-semibold"),
            Span(f" (Juz {juz_number})", cls="text-gray-500 text-sm"),
            colspan=colspan,
            cls="bg-base-200 py-1 px-2",
        ),
        cls="surah-header",
    )


def PageNumberCell(item_id: int, show_part_indicator: bool = True):
    """
    Render a page number cell with optional part indicator (e.g., ①, ②).
    """
    part_indicator = ""
    if show_part_indicator:
        part_info = get_page_part_info(item_id)
        if part_info:
            part_num, total_parts = part_info
            circled_nums = "①②③④⑤⑥⑦⑧⑨⑩"
            if part_num <= len(circled_nums):
                part_indicator = Span(circled_nums[part_num - 1], cls="text-gray-500 text-xs ml-0.5", title=f"Part {part_num} of {total_parts}")
            else:
                part_indicator = Span(f".{part_num}", cls="text-gray-500 text-xs ml-0.5", title=f"Part {part_num} of {total_parts}")

    return Td(
        Div(
            A(
                get_page_number(item_id),
                href=f"/page_details/{item_id}",
                cls="font-mono font-bold hover:underline",
            ),
            part_indicator,
            cls="flex items-center justify-center gap-0.5",
        ),
        cls="w-16 text-center",
    )


def StartTextCell(start_text: str, hide_text: bool = False):
    """
    Render a start text cell. If hide_text is True, shows dots that reveal text on click.
    """
    if hide_text:
        content = Div(
            Span("● ● ●", cls="text-gray-400 cursor-pointer select-none", x_show="!revealed", **{"@click": "revealed = true"}),
            Span(start_text or "-", x_show="revealed", x_cloak=True),
            x_data="{ revealed: false }",
        )
    else:
        content = Span(start_text or "-")
    return Td(content, cls="text-lg")


def ProgressCell(current, total):
    """
    Render a progress bar (used for rep modes).
    """
    if total == 0:
        return Span("-", cls="text-gray-400")

    percent = (current / total) * 100
    # Color: red < 30%, amber 30-70%, green > 70%
    bar_color = "bg-red-500" if percent < 30 else "bg-amber-500" if percent < 70 else "bg-green-500"

    return Div(
        Div(
            Div(cls=f"{bar_color} h-full", style=f"width: {percent}%"),
            cls="flex-1 bg-gray-200 rounded h-2 overflow-hidden",
        ),
        Span(f"{current}/{total}", cls="text-xs text-gray-500 ml-2 min-w-[35px]"),
        cls="flex items-center gap-1",
    )


def InlineModeSelect(hafiz_item_id, current_mode_code):
    """
    Render mode dropdown for inline mode changes (HTMX enabled).
    """
    def mode_option(code, label):
        return fh.Option(label, value=code, selected=code == current_mode_code)

    all_mode_options = [
        (DAILY_REPS_MODE_CODE, "☀️ Daily"),
        (WEEKLY_REPS_MODE_CODE, "📅 Weekly"),
        (FORTNIGHTLY_REPS_MODE_CODE, "📆 Fortnightly"),
        (MONTHLY_REPS_MODE_CODE, "🗓️ Monthly"),
        (FULL_CYCLE_MODE_CODE, "🔄 Full Cycle"),
        (SRS_MODE_CODE, "🧠 SRS"),
    ]

    return fh.Select(
        *[mode_option(code, label) for code, label in all_mode_options],
        name="mode_code",
        cls="select select-bordered select-xs",
        hx_post=f"/profile/quick_change_mode/{hafiz_item_id}",
        hx_trigger="change",
        hx_swap="none",
    )


def GraduateCell(hafiz_item_id, current_mode_code):
    """
    Render graduate checkbox with target mode dropdown.
    """
    all_mode_options = [
        (DAILY_REPS_MODE_CODE, "☀️ Daily"),
        (WEEKLY_REPS_MODE_CODE, "📅 Weekly"),
        (FORTNIGHTLY_REPS_MODE_CODE, "📆 Fortnightly"),
        (MONTHLY_REPS_MODE_CODE, "🗓️ Monthly"),
        (FULL_CYCLE_MODE_CODE, "🔄 Full Cycle"),
        (SRS_MODE_CODE, "🧠 SRS"),
    ]

    # Default to next mode in chain
    next_mode = REP_MODES_CONFIG.get(current_mode_code, {}).get("next_mode_code", FULL_CYCLE_MODE_CODE)

    graduate_options = [
        (code, label) for code, label in all_mode_options
        if code != current_mode_code
    ]

    graduate_select = fh.Select(
        *[fh.Option(label, value=code, selected=code == next_mode) for code, label in graduate_options],
        name="target_mode",
        cls="select select-bordered select-xs",
    )

    return Form(
        fh.Input(
            type="checkbox",
            name="confirm",
            cls="checkbox checkbox-xs checkbox-primary",
            hx_post=f"/profile/graduate_item/{hafiz_item_id}",
            hx_include="closest form",
            hx_swap="none",
        ),
        graduate_select,
        cls="flex items-center gap-2",
    )