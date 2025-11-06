from fasthtml.common import *
from monsterui.all import *
from utils import *
from app.common_function import *
from globals import *


hafiz_app, rt = create_app_with_auth()


@hafiz_app.get("/update_stats_column")
def update_stats_column(req, auth, item_id: int = None):
    if item_id:
        populate_hafizs_items_stat_columns(item_id)
    else:
        populate_hafizs_items_stat_columns()

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

    hafizs.update(
        hafiz_data,
        hafizs[auth].id,
    )
    return Redirect("/")
