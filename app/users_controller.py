from fasthtml.common import *
from monsterui.all import *
from hmac import compare_digest
from .users_model import Login, get_user_by_email, insert_user, reset_table_filters
from .users_view import *
from .globals import User
from .hafiz_model import (
    Hafiz,
    get_hafiz,
    insert_hafiz,
    delete_hafiz,
    get_hafizs_for_user,
)
from .hafiz_service import setup_new_hafiz
from .app_setup import (
    create_app_with_auth,
    add_toast,
    error_toast,
    warning_toast,
    success_toast,
)


# Redirect target for login failures
login_redir = Redirect("/users/login")
signup_redir = Redirect("/users/signup")
hafizs_selection_redir = Redirect("/users/hafiz_selection")

# Create FastHTML app instance for users
users_app, rt = create_app_with_auth()


@rt("/login")
def get(sess):
    return render_login_form()


@rt("/login")
def post(login: Login, sess):
    u = get_user_by_email(login.email)
    if u is None:
        error_toast(sess, "This email is not registered!")
        return signup_redir

    if not compare_digest(u.password.encode("utf-8"), login.password.encode("utf-8")):
        error_toast(sess, "Incorrect password!")
        return login_redir

    sess["user_auth"] = u.id
    return hafizs_selection_redir


@rt("/signup")
def get(sess):
    return render_signup_form()


@rt("/signup")
def post(user: User, confirm_password: str, sess):
    if user.password != confirm_password:
        add_toast(sess, "Passwords do not match!", "warning")
        return signup_redir

    # Check if user already exists
    existing_user = get_user_by_email(user.email)
    if existing_user:
        warning_toast(sess, "This email is already registered!")
        return login_redir

    # Create new user
    try:
        new_user = insert_user(user)
        sess["user_auth"] = new_user.id
        success_toast(sess, "Account created successfully!")
        return login_redir
    except Exception as e:
        error_toast(sess, f"Failed to create account. Please try again.")
        return signup_redir


@rt("/logout")
def get(sess):
    user_auth = sess.get("user_auth", None)
    if user_auth is not None:
        del sess["user_auth"]
    auth = sess.get("auth", None)
    if auth is not None:
        del sess["auth"]
    return RedirectResponse("/users/login", status_code=303)


@rt("/hafiz_selection")
def get(sess):
    reset_table_filters()
    auth = sess.get("auth", None)
    user_auth = sess.get("user_auth", None)
    if user_auth is None:
        return login_redir

    user_hafizs = get_hafizs_for_user(user_auth)
    cards = [render_hafiz_card(h, auth) for h in user_hafizs]

    hafiz_form = render_add_hafiz_form()

    return render_hafiz_selection_page(cards, hafiz_form)


@rt("/hafiz_selection")
def post(current_hafiz_id: int, sess):
    sess["auth"] = current_hafiz_id
    return RedirectResponse("/", status_code=303)


@rt("/add_hafiz")
def post(hafiz: Hafiz, sess):
    hafiz.user_id = sess["user_auth"]
    new_hafiz = insert_hafiz(hafiz)
    setup_new_hafiz(new_hafiz.id)
    return RedirectResponse("/users/hafiz_selection", status_code=303)


@rt("/delete_hafiz/{hafiz_id}")
def delete(hafiz_id: int, sess):
    hafiz = get_hafiz(hafiz_id)
    if hafiz.user_id != sess["user_auth"]:
        return RedirectResponse("/users/hafiz_selection", status_code=303)

    delete_hafiz(hafiz_id)
    return RedirectResponse("/users/hafiz_selection", status_code=303)
