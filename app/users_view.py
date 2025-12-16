"""
User Views - UI components for authentication and account management

Renders forms and pages for the user journey.
"""

from fasthtml.common import *
from monsterui.all import *


# ============================================================================
# MID-LEVEL VIEWS (Forms with context)
# ============================================================================


def render_profile_form(user):
    """User profile edit form (name, email, password)"""
    return Titled(
        "User Profile",
        Form(
            LabelInput(
                label="Name",
                name="name",
                type="text",
                value=user.name,
                required=True,
                placeholder="Name",
            ),
            LabelInput(
                label="Email",
                name="email",
                type="email",
                value=user.email,
                required=True,
                placeholder="Email",
            ),
            LabelInput(
                label="New Password",
                name="password",
                type="password",
                required=False,
                placeholder="Leave blank to keep current password",
            ),
            LabelInput(
                label="Confirm Password",
                name="confirm_password",
                type="password",
                required=False,
                placeholder="Confirm new password",
            ),
            Button("Update Profile"),
            action="/users/account",
            method="post",
        ),
        cls="space-y-6",
    )


# ============================================================================
# LOW-LEVEL COMPONENTS (Simple forms)
# ============================================================================


def render_login_form():
    """Login form with email and password"""
    return Titled(
        "Login",
        Form(
            LabelInput(
                label="Email",
                name="email",
                type="email",
                required=True,
                placeholder="Email",
            ),
            LabelInput(
                label="Password",
                name="password",
                type="password",
                required=True,
                placeholder="Password",
            ),
            Button("Login"),
            action="/users/login",
            method="post",
        ),
        cls="space-y-6",
    )


def render_signup_form():
    """Signup form with name, email, password, and confirmation"""
    return Titled(
        "User Registration",
        Form(
            LabelInput(
                label="Name",
                name="name",
                type="text",
                required=True,
                placeholder="Name",
            ),
            LabelInput(
                label="Email",
                name="email",
                type="email",
                required=True,
                placeholder="Email",
            ),
            LabelInput(
                label="Password",
                name="password",
                type="password",
                required=True,
                placeholder="Password",
            ),
            LabelInput(
                label="Confirm Password",
                name="confirm_password",
                type="password",
                required=True,
                placeholder="Password",
            ),
            Button("Signup"),
            action="/users/signup",
            method="post",
        ),
        P(
            "Already have an account? ",
            A("Login", href="/users/login", cls=TextT.primary),
        ),
        cls="space-y-6",
    )
