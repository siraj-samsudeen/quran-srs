from fasthtml.common import *
from monsterui.all import *
from utils import *
from app.common_function import *
from globals import *

DEFAULT_RATINGS = {
    "new_memorization": 1,
}


hafiz_app, rt = create_app_with_auth()


@hafiz_app.get("/update_stats_column")
def update_stats_column(req, auth, item_id: int = None):
    current_date = get_current_date(auth)

    if item_id:
        populate_hafizs_items_stat_columns(item_id)
        update_actual_interval(item_id=item_id, current_date=current_date)
    else:
        populate_hafizs_items_stat_columns()
        for hafiz_item in hafizs_items(where="mode_id = 5"):
            update_actual_interval(
                item_id=hafiz_item.item_id, current_date=current_date
            )

    return RedirectResponse(req.headers.get("referer", "/"), status_code=303)


@hafiz_app.get("/settings")
def settings_page(auth):
    current_hafiz = hafizs[auth]

    def render_field(label, field_type, required=True, **kwargs):
        field_name = standardize_column(label)
        value = getattr(current_hafiz, field_name)
        return LabelInput(
            label,
            id=field_name,
            type=field_type,
            value=value,
            required=required,
            **kwargs,
        )

    form = Form(
        render_field("Name", "text"),
        render_field("Daily Capacity", "number", False),
        render_field("Current Date", "date"),
        render_field("Display Count", "number", min=1),
        DivHStacked(
            Button("Update", type="submit", cls=ButtonT.primary),
            Button(
                "Discard",
                hx_get="/hafiz/settings",
                hx_target="body",
                cls=ButtonT.destructive,
            ),
        ),
        action="/hafiz/settings",
        method="POST",
    )
    return main_area(
        Div(
            H1("Hafiz Preferences", cls=TextT.center),
            Div(form, cls="max-w-xl mx-auto"),
            cls="space-y-6",
        ),
        auth=auth,
        active="Settings",
    )


@hafiz_app.post("/settings")
def update_setings(auth, hafiz_data: Hafiz):
    display_count = hafiz_data.display_count
    if not display_count or display_count < 0:
        hafiz_data.display_count = get_display_count(auth)

    hafizs.update(
        hafiz_data,
        hafizs[auth].id,
    )
    return RedirectResponse("/hafiz/settings", status_code=303)


# hafiz delete route for testing
@hafiz_app.delete("/{hafiz_id}")
def delete_hafizs_data(hafiz_id: int):
    delete_hafiz(hafiz_id)


@hafiz_app.get("/theme")
def custom_theme_picker():
    return ThemePicker()
