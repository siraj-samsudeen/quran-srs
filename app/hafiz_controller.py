"""
Hafiz Controller Module

Route handlers for hafiz settings.
"""

from fasthtml.common import *
from .app_setup import create_app_with_auth, success_toast
from .hafiz_model import Hafiz, get_hafiz, update_hafiz
from .hafiz_view import render_settings_page, render_theme_page


hafiz_app, rt = create_app_with_auth()


@hafiz_app.get("/settings")
def settings_page(auth):  # auth is dict: {"hafiz_id": int, "user_id": int}
    hafiz_id = auth["hafiz_id"]
    current_hafiz = get_hafiz(hafiz_id)
    return render_settings_page(current_hafiz, hafiz_id)


@hafiz_app.post("/settings")
def update_settings(hafiz: Hafiz, auth, sess):  # auth is dict
    hafiz_id = auth["hafiz_id"]
    update_hafiz(hafiz, hafiz_id)
    success_toast(sess, "Settings updated successfully!")
    return Redirect("/")


@hafiz_app.get("/theme")
def theme_page(auth):  # auth is dict
    hafiz_id = auth["hafiz_id"]
    return render_theme_page(hafiz_id)
