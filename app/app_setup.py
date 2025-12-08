"""
App Setup Module

Contains middleware, beforeware, headers, and app factory functions.
Separated from common_function.py for cleaner architecture.
"""

from fasthtml.common import *
from monsterui.all import *
from .globals import users, revisions, hafizs_items, plans
from .hafiz_model import get_hafiz


def user_auth(req, sess):
    """Check user authentication - redirects to login if not authenticated."""
    user_id = req.scope["user_id"] = sess.get("user_id", None)
    if user_id:
        try:
            users[user_id]
        except NotFoundError:
            del sess["user_id"]
            user_id = None
    if not user_id:
        return RedirectResponse("/users/login", status_code=303)


user_bware = Beforeware(
    user_auth,
    skip=["/users/login", "/users/logout", "/users/signup"],
)


def hafiz_auth(req, sess):
    """Check hafiz selection and set up query filters."""
    # CRITICAL: Use 'auth' (FastHTML reserved name) for automatic parameter injection
    # auth is a dict: {"hafiz_id": int, "user_id": int}
    auth = req.scope['auth'] = sess.get("auth", None)
    if not auth:
        return RedirectResponse("/users/hafiz_selection", status_code=303)

    # Validate hafiz exists
    hafiz_id = auth.get("hafiz_id")
    if not hafiz_id:
        return RedirectResponse("/users/hafiz_selection", status_code=303)

    try:
        get_hafiz(hafiz_id)
    except NotFoundError:
        # Hafiz was deleted, clear session and redirect
        del sess["auth"]
        return RedirectResponse("/users/hafiz_selection", status_code=303)

    # Apply xtra filters for hafiz-specific queries
    revisions.xtra(hafiz_id=hafiz_id)
    hafizs_items.xtra(hafiz_id=hafiz_id)
    plans.xtra(hafiz_id=hafiz_id)


hafiz_bware = Beforeware(
    hafiz_auth,
    skip=[
        "/users/login",
        "/users/logout",
        "/users/signup",
        r"/users/\d+$",  # for deleting the user
        "/users/hafiz_selection",
        "/users/add_hafiz",
        r"/users/delete_hafiz/\d+$",  # delete hafiz (only needs user_auth, not hafiz_auth)
    ],
)

# External JS/CSS headers
hyperscript_header = Script(src="https://unpkg.com/hyperscript.org@0.9.14")
alpinejs_header = Script(
    src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js", defer=True
)
daisyui_css = Link(
    rel="stylesheet",
    href="https://cdn.jsdelivr.net/npm/daisyui@4.12.14/dist/full.min.css",
)
style_css = Link(rel="stylesheet", href="/public/css/style.css")
favicon = Link(rel="icon", type="image/svg+xml", href="/public/favicon.svg")


def create_app_with_auth(**kwargs):
    """Create a FastHTML app with standard auth middleware and headers."""
    app, rt = fast_app(
        before=[user_bware, hafiz_bware],
        hdrs=(
            Theme.blue.headers(),
            daisyui_css,
            hyperscript_header,
            alpinejs_header,
            style_css,
            favicon,
        ),
        bodykw={"hx-boost": "true"},
        **kwargs,
    )
    setup_toasts(app)
    return app, rt


# Toast helper functions
def error_toast(sess, msg):
    add_toast(sess, msg, "error")


def success_toast(sess, msg):
    add_toast(sess, msg, "success")


def warning_toast(sess, msg):
    add_toast(sess, msg, "warning")
