from fasthtml.common import *
from monsterui.all import *
from hmac import compare_digest
from .users_model import *
from .users_view import *


# Redirect target for login failures
login_redir = RedirectResponse("/users/login", status_code=303)

# Create FastHTML app instance for users
users_app, rt = fast_app(hdrs=Theme.blue.headers())


@rt("/login")
def get(sess):
    """Display login form"""
    return render_login_form()


@rt("/login")
def post(login: Login, sess):
    """Process login form submission"""
    if not login.email or not login.password:
        return login_redir

    u = get_user_by_email(login.email)
    if u is None:
        return login_redir

    if not compare_digest(u.password.encode("utf-8"), login.password.encode("utf-8")):
        return login_redir

    sess["user_auth"] = u.id
    return RedirectResponse("/users/hafiz_selection", status_code=303)


@rt("/logout")
def get(sess):
    """Logout user and clear session"""
    user_auth = sess.get("user_auth", None)
    if user_auth is not None:
        del sess["user_auth"]
    auth = sess.get("auth", None)
    if auth is not None:
        del sess["auth"]
    return RedirectResponse("/users/login", status_code=303)


@rt("/hafiz_selection")
def get(sess):
    """Display hafiz selection page"""
    reset_table_filters()
    auth = sess.get("auth", None)
    user_auth = sess.get("user_auth", None)
    if user_auth is None:
        return login_redir

    hafizs_users = get_hafizs_for_user(user_auth)
    cards = [
        render_hafiz_card(h, auth, get_hafiz_by_id(h.hafiz_id).name)
        for h in hafizs_users
    ]

    hafiz_form = render_add_hafiz_form()

    return render_hafiz_selection_page(cards, hafiz_form)


@rt("/hafiz_selection")
def post(current_hafiz_id: int, sess):
    """Switch to selected hafiz account"""
    sess["auth"] = current_hafiz_id
    return RedirectResponse("/", status_code=303)


@rt("/add_hafiz")
def post(hafiz: Hafiz, relationship: str, sess):
    """Add new hafiz and create user relationship"""
    hafiz_id = insert_hafiz(hafiz)
    insert_hafiz_user_relationship(hafiz_id.id, sess["user_auth"], relationship)
    return RedirectResponse("/users/hafiz_selection", status_code=303)
