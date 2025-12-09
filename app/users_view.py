from fasthtml.common import *
from monsterui.all import *


def render_login_form():
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
        P(
            "Don't have an account? ",
            A("Register", href="/users/signup", cls=TextT.primary),
        ),
        cls="space-y-6",
    )


def render_signup_form():
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


def render_hafiz_card(hafiz, auth):
    is_current_hafiz = auth == hafiz.id

    if is_current_hafiz:
        # For current hafiz, show "Go Back to [name]" button only with distinct background
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
        # For other hafizs, show name with dropdown menu for delete
        return Div(
            # Clickable name area (takes most space)
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
            # Dropdown menu for actions (Alpine.js)
            Div(
                # Menu toggle button
                Button(
                    "⋮",  # Vertical ellipsis
                    type="button",
                    cls="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded",
                    title="More actions",
                    data_testid=f"hafiz-menu-{hafiz.name}",
                    **{"@click": "open = !open"},
                ),
                # Dropdown menu (hidden by default)
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


def render_hafiz_selection_page(cards, hafiz_form):
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
