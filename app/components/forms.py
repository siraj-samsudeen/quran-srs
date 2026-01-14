from fasthtml.common import *
import fasthtml.common as fh
from monsterui.all import *
from constants import (
    RATING_MAP,
    REP_MODE_OPTIONS,
    FULL_CYCLE_MODE_CODE,
    SRS_MODE_CODE,
    NEW_MEMORIZATION_MODE_CODE,
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    DEFAULT_REP_COUNTS,
)

def RatingDropdown(
    rating="None",
    name="rating",
    cls="",
    **kwargs,
):
    """
    A dropdown for selecting rating (Good/Ok/Bad).
    """
    def mk_options(o):
        id, name = o
        is_selected = lambda m: m == str(rating)
        return fh.Option(name, value=id, selected=is_selected(id))

    return fh.Select(
        fh.Option("-", value="None", selected=(rating is None or rating == "None")),
        *map(mk_options, RATING_MAP.items()),
        name=name,
        cls=f"select select-bordered select-sm {cls}",
        **kwargs,
    )

def RatingRadio(
    default_rating: int = 1,
    direction: str = "vertical",
    is_label: bool = True,
    id: str = "rating",
    cls: str = None,
):
    """
    Radio buttons for selecting rating.
    """
    def render_radio(o):
        value, label = o
        is_checked = True if int(value) == default_rating else False
        return Div(
            FormLabel(
                Radio(id=id, value=value, checked=is_checked, cls=cls),
                Span(label),
                cls="space-x-2 p-1 border border-transparent has-[:checked]:border-blue-500",
            ),
            cls=f"{'inline-block' if direction == 'horizontal' else None}",
        )

    options = map(render_radio, RATING_MAP.items())

    if direction == "horizontal":
        outer_cls = (FlexT.block, FlexT.row, FlexT.wrap, "gap-x-6 gap-y-4")
    elif direction == "vertical":
        outer_cls = "space-y-2 leading-8 sm:leading-6"

    label = FormLabel("Rating") if is_label else None

    return Div(label, *options, cls=outer_cls)


def ModeSelect(
    selected_mode=None,
    name="mode_code",
    cls="select select-bordered select-sm",
    include_all=True,
    **kwargs
):
    """
    Dropdown for selecting a revision mode.
    
    Args:
        include_all: If True, includes Full Cycle and SRS. If False, only Rep modes.
    """
    options = list(REP_MODE_OPTIONS)
    if include_all:
        options.extend([
            (FULL_CYCLE_MODE_CODE, "🔄 Full Cycle"),
            (SRS_MODE_CODE, "🧠 SRS"),
        ])
    
    def mode_option(code, label):
        return Option(label, value=code, selected=code == selected_mode)

    return Select(
        *[mode_option(code, label) for code, label in options],
        name=name,
        cls=cls,
        **kwargs,
    )


def BulkSelectCheckbox(value, name="item_ids", cls="", checked=False, **kwargs):
    """
    Checkbox for bulk selection in table rows.
    Connects to the SelectAllCheckbox via the 'bulk-select-checkbox' class.
    """
    return fh.Input(
        type="checkbox",
        name=name,
        value=value,
        checked=checked,
        cls=f"checkbox bulk-select-checkbox {cls}",
        **{"@change": "count = $root.querySelectorAll('.bulk-select-checkbox:checked').length"},
        **kwargs
    )


def SelectAllCheckbox(cls="checkbox", **kwargs):
    """
    Master checkbox for selecting all BulkSelectCheckboxes in the current scope.
    """
    return fh.Input(
        type="checkbox",
        cls=cls,
        **{
            "@change": """
                $root.querySelectorAll('.bulk-select-checkbox').forEach(cb => cb.checked = $el.checked);
                count = $el.checked ? $root.querySelectorAll('.bulk-select-checkbox').length : 0
            """,
            ":checked": "count > 0 && count === $root.querySelectorAll('.bulk-select-checkbox').length",
        },
        **kwargs
    )


def RepConfigForm(
    form_id="rep-config-form",
    default_mode_code=DAILY_REPS_MODE_CODE,
    show_advanced=False,
    custom_thresholds=None,
):
    """
    Form for configuring repetition thresholds.
    Includes AlpineJS logic for toggling advanced mode.
    """
    custom_thresholds = custom_thresholds or {}

    def mode_option(code, label):
        return Option(label, value=code, selected=code == default_mode_code)

    mode_select = Select(
        *[mode_option(code, label) for code, label in REP_MODE_OPTIONS],
        name="mode_code",
        cls="select select-bordered select-sm w-full",
        x_model="selectedMode",
    )

    # Get default rep count for selected mode
    default_rep_count = custom_thresholds.get(
        default_mode_code, DEFAULT_REP_COUNTS.get(default_mode_code, 7)
    )

    simple_rep_input = Div(
        FormLabel("Repetitions", cls="text-sm"),
        fh.Input(
            type="number",
            name="rep_count",
            min="0",
            max="99",
            value=default_rep_count,
            cls="input input-bordered input-sm w-20",
            x_model="repCounts[selectedMode]",
        ),
        cls="flex items-center gap-2",
    )

    def advanced_rep_input(mode_code, label):
        threshold = custom_thresholds.get(mode_code, DEFAULT_REP_COUNTS.get(mode_code, 7))
        return Div(
            FormLabel(label, cls="text-sm w-24"),
            fh.Input(
                type="number",
                name=f"rep_count_{mode_code}",
                min="0",
                max="99",
                value=threshold,
                cls="input input-bordered input-sm w-20",
                x_model=f"repCounts['{mode_code}']",
            ),
            cls="flex items-center gap-2",
        )

    advanced_inputs = Div(
        *[advanced_rep_input(code, label) for code, label in REP_MODE_OPTIONS],
        cls="grid grid-cols-2 gap-2",
        x_show="advancedMode",
        x_cloak=True,
    )

    advanced_toggle = Div(
        FormLabel(
            fh.Input(
                type="checkbox",
                cls="checkbox checkbox-sm",
                x_model="advancedMode",
            ),
            Span("Advanced config (set all modes)", cls="text-sm ml-2"),
            cls="cursor-pointer",
        ),
        cls="mt-2",
    )

    # Alpine.js state initialization
    alpine_init = {
        "selectedMode": f"'{default_mode_code}'",
        "advancedMode": "true" if show_advanced else "false",
        "repCounts": str({
            code: custom_thresholds.get(code, DEFAULT_REP_COUNTS.get(code, 7))
            for code, _ in REP_MODE_OPTIONS
        }).replace("'", '"'),
    }
    alpine_data = "{ " + ", ".join(f"{k}: {v}" for k, v in alpine_init.items()) + " }"

    return Div(
        Div(
            Div(
                FormLabel("Starting Mode", cls="text-sm"),
                mode_select,
                cls="flex-1",
            ),
            Div(
                simple_rep_input,
                x_show="!advancedMode",
            ),
            cls="flex gap-4 items-end",
        ),
        advanced_toggle,
        advanced_inputs,
        id=form_id,
        x_data=alpine_data,
        cls="space-y-2 p-3 bg-base-200 rounded-lg",
    )