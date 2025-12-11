"""
User Controller - Authentication, Account Management, Hafiz Selection

Handles the complete user journey from signup through hafiz management.
Routes are organized by feature area for readability.
"""

from fasthtml.common import *
from monsterui.all import *
from hmac import compare_digest
from .users_model import *
from .users_view import *
from .hafiz_model import *
from .hafiz_view import *
from .common_function import *


# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

login_redir = Redirect("/users/login")
signup_redir = Redirect("/users/signup")
hafizs_selection_redir = Redirect("/hafiz/selection")

users_app, rt = create_app_with_auth()


# ============================================================================
# AUTHENTICATION - Login & Logout
# ============================================================================

@rt("/login")
def get(sess):
    """Display login form"""
    return render_login_form()


@rt("/login")
def post(login: Login, sess):
    """Authenticate user and redirect to hafiz selection"""
    u = get_user_by_email(login.email)
    if u is None:
        error_toast(sess, "This email is not registered!")
        return signup_redir

    if not compare_digest(u.password.encode("utf-8"), login.password.encode("utf-8")):
        error_toast(sess, "Incorrect password!")
        return login_redir

    sess["user_auth"] = u.id
    return hafizs_selection_redir


@rt("/logout")
def get(sess):
    """Clear session and redirect to login"""
    if "user_auth" in sess:
        del sess["user_auth"]
    if "auth" in sess:
        del sess["auth"]
    return RedirectResponse("/users/login", status_code=303)


# ============================================================================
# REGISTRATION - User Signup
# ============================================================================

@rt("/signup")
def get(sess):
    """Display signup form"""
    return render_signup_form()


@rt("/signup")
def post(user: User, confirm_password: str, sess):
    """Create new user account"""
    if user.password != confirm_password:
        add_toast(sess, "Passwords do not match!", "warning")
        return signup_redir

    existing_user = get_user_by_email(user.email)
    if existing_user:
        warning_toast(sess, "This email is already registered!")
        return login_redir

    try:
        new_user = users.insert(user)
        sess["user_auth"] = new_user.id
        success_toast(sess, "Account created successfully!")
        return login_redir
    except Exception as e:
        error_toast(sess, f"Failed to create account. Please try again.")
        return signup_redir


# ============================================================================
# ACCOUNT MANAGEMENT - Profile & Settings
# ============================================================================

@rt("/account")
def get(sess):
    """Display user account settings"""
    user_auth = sess.get("user_auth", None)
    if user_auth is None:
        return login_redir

    user = users[user_auth]
    return render_profile_form(user)


@rt("/account")
def post(sess, name: str, email: str, password: str = "", confirm_password: str = ""):
    """Update user profile (name, email, password)"""
    user_auth = sess.get("user_auth", None)
    if user_auth is None:
        return login_redir

    if password:
        if password != confirm_password:
            error_toast(sess, "Passwords do not match!")
            return Redirect("/users/account")
        users.update({"name": name, "email": email, "password": password}, user_auth)
    else:
        users.update({"name": name, "email": email}, user_auth)

    success_toast(sess, "Profile updated successfully!")
    return Redirect("/users/account")


@rt("/delete/{user_id}")
def delete(user_id: int, sess):
    """Delete user account and all related data (cascade)"""
    if sess.get("user_auth") != user_id:
        error_toast(sess, "Unauthorized!")
        return Redirect("/hafiz/selection")

    users.delete(user_id)

    if "user_auth" in sess:
        del sess["user_auth"]
    if "auth" in sess:
        del sess["auth"]

    return RedirectResponse("/users/login", status_code=303)


