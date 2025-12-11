"""
User Views - UI components for authentication and account management

Renders forms and pages for the user journey.
"""

from fasthtml.common import *
from monsterui.all import *


# ============================================================================
# HIGH-LEVEL VIEWS (Pages users see)
# ============================================================================


def render_hafiz_selection_page(cards, hafiz_form):
    """Hafiz selection page with all hafiz cards and add form"""
    return Titled(
        "Hafiz Selection",
        Container(
            Div(
                Div(*cards, cls=(FlexT.block, FlexT.wrap, "gap-4")),
                hafiz_form,
                cls="space-y-4",
            )
        ),
    )


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


def render_hafiz_card(hafiz, auth):
    """
    Render a hafiz card with switch/delete actions.

    Current hafiz: green background, "Go Back" button
    Other hafizs: white background, name button + delete dropdown
    """
    is_current_hafiz = auth == hafiz.id

    if is_current_hafiz:
        return Div(
            Button(
                f"← Go Back to {hafiz.name}",
                name="current_hafiz_id",
                value=hafiz.id,
                hx_post="/users/hafiz_selection",
                hx_target="body",
                hx_replace_url="true",
                cls=f"{ButtonT.primary} w-full text-left",
                data_testid=f"hafiz-switch-{hafiz.name}",
            ),
            cls="flex gap-2 items-center p-2 border-2 border-green-400 rounded-lg bg-green-50 shadow-sm hover:shadow-md transition-shadow",
        )
    else:
        return Div(
            Button(
                hafiz.name,
                name="current_hafiz_id",
                value=hafiz.id,
                hx_post="/users/hafiz_selection",
                hx_target="body",
                hx_replace_url="true",
                cls=f"{ButtonT.primary} flex-1 text-left",
                data_testid=f"hafiz-switch-{hafiz.name}",
            ),
            Div(
                Button(
                    "⋮",
                    type="button",
                    cls="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded",
                    title="More actions",
                    data_testid=f"hafiz-menu-{hafiz.name}",
                    **{"@click": "open = !open"},
                ),
                Div(
                    Button(
                        "Delete",
                        type="button",
                        hx_delete=f"/users/delete_hafiz/{hafiz.id}",
                        hx_target="body",
                        hx_confirm=f"Are you sure you want to delete {hafiz.name}? This will delete all their progress.",
                        cls="w-full text-left px-4 py-2 text-red-600 hover:bg-red-50 rounded",
                        data_testid=f"hafiz-delete-{hafiz.name}",
                    ),
                    cls="absolute right-0 mt-2 w-32 bg-white border rounded-lg shadow-lg z-10",
                    **{"x-show": "open", "@click.away": "open = false"},
                ),
                cls="relative",
                **{"x-data": "{ open: false }"},
            ),
            cls="flex gap-2 items-center p-2 border rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow",
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


def render_add_hafiz_form():
    """Form to create a new hafiz profile"""
    return Card(
        Titled(
            "Add Hafiz",
            Form(
                LabelInput(label="Name", name="name", required=True),
                LabelInput(
                    label="Daily Capacity",
                    name="daily_capacity",
                    type="number",
                    min="1",
                    value="10",
                    required=True,
                ),
                Button("Add Hafiz"),
                action="/users/add_hafiz",
                method="post",
            ),
        ),
        cls="w-[300px]",
    )
