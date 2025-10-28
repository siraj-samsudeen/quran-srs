from fasthtml.common import *
from monsterui.all import *
from hmac import compare_digest
from .users_model import *
from .users_view import *
from .common_function import *


# Redirect target for login failures
login_redir = Redirect("/users/login")
signup_redir = Redirect("/users/signup")
hafizs_selection_redir = Redirect("/users/hafiz_selection")

# Create FastHTML app instance for users
users_app, rt = create_app_with_auth()


@rt("/login")
def get(sess):
    """Display login form"""
    return render_login_form()


@rt("/login")
def post(login: Login, sess):
    """Process login form submission"""
    u = get_user_by_email(login.email)
    if u is None:
        error_toast(sess, "This email is not registered!")
        return signup_redir

    if not compare_digest(u.password.encode("utf-8"), login.password.encode("utf-8")):
        error_toast(sess, "Incorrect password!")
        return login_redir

    sess["user_auth"] = u.id
    return hafizs_selection_redir


# @rt("/signup")
def get(sess):
    """Display signup form"""
    return render_signup_form()


# @rt("/signup")
def post(user: User, confirm_password: str, sess):
    """Process signup form submission"""
    # Check if passwords match
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
    """Logout user and clear session"""
    user_auth = sess.get("user_auth", None)
    if user_auth is not None:
        del sess["user_auth"]
    auth = sess.get("auth", None)
    if auth is not None:
        del sess["auth"]
    return RedirectResponse("/users/login", status_code=303)


# user delete route for testing
@rt("/{user_id}")
def delete(user_id: int):
    delete_user(user_id)
    cleanup_orphaned_hafizs()


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
    hafiz_id = hafiz_id.id
    insert_hafiz_user_relationship(hafiz_id, sess["user_auth"], relationship)
    populate_hafiz_items(hafiz_id)
    create_new_plan(hafiz_id)
    return RedirectResponse("/users/hafiz_selection", status_code=303)
