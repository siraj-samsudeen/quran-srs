from fasthtml.common import *
from monsterui.all import *
from constants import RATING_MAP
from app.components.forms import (
    RatingDropdown,
    RatingRadio,
    RepConfigForm,
    BulkSelectCheckbox,
)
from app.components.tables import (
    ProgressCell,
    GraduateCell,
    InlineModeSelect,
    SurahHeader,
    PageNumberCell,
    StartTextCell,
)
from app.components.display import (
    PageDescription,
    CountLink,
    ModeAndReps,
    StatusBadge,
    ModeBadge,
    TrendIndicator,
)
from app.components.layout import MainArea, BulkActionBar, StatsCards

# Aliases for backward compatibility
rating_dropdown = RatingDropdown
rating_radio = RatingRadio
render_rep_config_form = RepConfigForm
render_progress_cell = ProgressCell
render_graduate_cell = GraduateCell
render_mode_dropdown = InlineModeSelect
render_inline_mode_config = InlineModeSelect
render_mode_and_reps = ModeAndReps
create_count_link = CountLink
get_page_description = PageDescription
main_area = MainArea
render_surah_header = SurahHeader
render_page_number_cell = PageNumberCell
render_start_text_cell = StartTextCell
render_bulk_checkbox = BulkSelectCheckbox

def error_toast(sess, msg):
    add_toast(sess, msg, "error")

def success_toast(sess, msg):
    add_toast(sess, msg, "success")

def warning_toast(sess, msg):
    add_toast(sess, msg, "warning")

def render_rating(rating: int):
    return RATING_MAP.get(str(rating))

def group_by_type(data, current_type, feild=None, preserve_order=False):
    from collections import defaultdict
    columns_map = {
        "juz": "juz_number",
        "surah": "surah_id",
        "page": "page_number",
        "item_id": "item_id",
        "id": "id",
    }
    grouped = defaultdict(
        list
    )
    for row in data:
        grouped[row[columns_map[current_type]]].append(
            row if feild is None else row[feild]
        )
    if preserve_order:
        return dict(grouped)
    sorted_grouped = dict(sorted(grouped.items(), key=lambda x: int(x[0])))
    return sorted_grouped
