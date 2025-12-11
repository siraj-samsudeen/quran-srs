from fasthtml.common import *
from monsterui.all import *
from utils import *
from app.common_function import *
from app.hafiz_model import get_hafizs_for_user, populate_hafiz_items, create_new_plan, reset_table_filters
from app.hafiz_view import render_hafiz_card, render_add_hafiz_form, render_hafiz_selection_page
from database import *


hafiz_app, rt = create_app_with_auth()


# ============================================================================
# HAFIZ SELECTION & MANAGEMENT
# ============================================================================

@rt("/selection")
def get(sess):
    """Display hafiz selection page with all user's hafizs"""
    reset_table_filters()
    auth = sess.get("auth", None)
    user_auth = sess.get("user_auth", None)
    if user_auth is None:
        return Redirect("/users/login")

    user_hafizs = get_hafizs_for_user(user_auth)
    cards = [render_hafiz_card(h, auth) for h in user_hafizs]
    hafiz_form = render_add_hafiz_form()

    return render_hafiz_selection_page(cards, hafiz_form)


@rt("/selection")
def post(current_hafiz_id: int, sess):
    """Select a hafiz (sets active hafiz in session)"""
    sess["auth"] = current_hafiz_id
    return RedirectResponse("/", status_code=303)


@rt("/add")
def post(hafiz: Hafiz, sess):
    """Create new hafiz profile with initial data"""
    hafiz.user_id = sess["user_auth"]
    new_hafiz = hafizs.insert(hafiz)
    hafiz_id = new_hafiz.id
    populate_hafiz_items(hafiz_id)
    create_new_plan(hafiz_id)
    return RedirectResponse("/hafiz/selection", status_code=303)


@rt("/delete/{hafiz_id}")
def delete(hafiz_id: int, sess):
    """Delete hafiz profile and all related data"""
    hafiz = hafizs[hafiz_id]
    if hafiz.user_id != sess["user_auth"]:
        return RedirectResponse("/hafiz/selection", status_code=303)

    hafizs.delete(hafiz_id)
    return RedirectResponse("/hafiz/selection", status_code=303)


# ============================================================================
# HAFIZ SETTINGS
# ============================================================================


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
        DivFullySpaced(
            DivLAligned(
                Button("Update", type="submit", cls=ButtonT.primary),
                Button(
                    "Discard",
                    hx_get="/hafiz/settings",
                    hx_target="body",
                    cls=ButtonT.destructive,
                ),
            ),
            A(Button("Theme", cls=ButtonT.secondary), href="/hafiz/theme"),
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


@hafiz_app.get("/theme")
def custom_theme_picker(auth):
    return main_area(ThemePicker(), active="Settings", auth=auth)
