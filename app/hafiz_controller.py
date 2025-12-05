"""
Hafiz Controller Module

Route handlers for hafiz settings.
"""

from fasthtml.common import *
from .app_setup import create_app_with_auth
from .globals import hafizs, Hafiz
from .common_function import populate_hafizs_items_stat_columns
from .hafiz_view import render_settings_page, render_theme_page


hafiz_app, rt = create_app_with_auth()


@hafiz_app.get("/update_stats_column")
def update_stats_column(req, auth, item_id: int = None):
    """Trigger recalculation of hafizs_items statistics."""
    if item_id:
        populate_hafizs_items_stat_columns(item_id)
    else:
        populate_hafizs_items_stat_columns()

    return RedirectResponse(req.headers.get("referer", "/"), status_code=303)


@hafiz_app.get("/settings")
def settings_page(auth):
    """Display hafiz settings form."""
    current_hafiz = hafizs[auth]
    return render_settings_page(current_hafiz, auth)


@hafiz_app.post("/settings")
def update_settings(auth, hafiz_data: Hafiz):
    """Update hafiz settings."""
    hafizs.update(
        hafiz_data,
        hafizs[auth].id,
    )
    return Redirect("/")


@hafiz_app.get("/theme")
def theme_page(auth):
    """Display theme picker."""
    return render_theme_page(auth)
