"""
Hafiz Controller Module

Route handlers for hafiz settings.
"""

from fasthtml.common import *
from .app_setup import create_app_with_auth, error_toast, success_toast
from .hafiz_model import Hafiz, get_hafiz, update_hafiz
from .hafiz_view import render_settings_page, render_theme_page


hafiz_app, rt = create_app_with_auth()


@hafiz_app.get("/settings")
def settings_page(auth, sess):
    try:
        current_hafiz = get_hafiz(auth)
        return render_settings_page(current_hafiz, auth)
    except Exception as e:
        error_toast(sess, "Failed to load settings. Please try again.")
        return Redirect("/")


@hafiz_app.post("/settings")
def update_settings(auth, hafiz_data: Hafiz, sess):
    try:
        current_hafiz = get_hafiz(auth)
        update_hafiz(hafiz_data, current_hafiz.id)
        success_toast(sess, "Settings updated successfully!")
        return Redirect("/")
    except Exception as e:
        error_toast(sess, "Failed to update settings. Please try again.")
        return Redirect("/hafiz/settings")


@hafiz_app.get("/theme")
def theme_page(auth, sess):
    try:
        return render_theme_page(auth)
    except Exception as e:
        error_toast(sess, "Failed to load theme picker. Please try again.")
        return Redirect("/")
