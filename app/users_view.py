from fasthtml.common import *
from monsterui.all import *


OPTION_MAP = {
    "age_group": ["child", "teen", "adult"],
    "relationship": ["self", "parent", "teacher", "sibling"],
}


def render_login_form():
    """Render login form"""
    return Titled(
        "Login",
        Form(
            LabelInput(label="Email", name="email", type="email"),
            LabelInput(label="Password", name="password", type="password"),
            Button("Login"),
            action="/users/login",
            method="post",
        ),
    )


def render_options(option):
    """Render option for select dropdown"""
    return Option(
        option.capitalize(),
        value=option,
    )


def render_add_hafiz_form():
    """Render add hafiz form"""
    return Card(
        Titled(
            "Add Hafiz",
            Form(
                LabelInput(label="Name", name="name"),
                LabelSelect(
                    *map(render_options, OPTION_MAP["age_group"]),
                    label="Age Group",
                    name="age_group",
                ),
                LabelInput(
                    label="Daily Capacity",
                    name="daily_capacity",
                    type="number",
                    min="1",
                    value="1",
                    required=True,
                ),
                LabelSelect(
                    *map(render_options, OPTION_MAP["relationship"]),
                    label="Relationship",
                    name="relationship",
                ),
                Button("Add Hafiz"),
                action="/users/add_hafiz",
                method="post",
            ),
        ),
        cls="w-[300px]",
    )


def render_hafiz_card(hafizs_user, auth, hafiz_name):
    """Render individual hafiz selection card"""
    is_current_hafizs_user = auth != hafizs_user.hafiz_id
    return Card(
        header=DivFullySpaced(H3(hafiz_name)),
        footer=Button(
            "Switch Hafiz" if is_current_hafizs_user else "Go to home",
            name="current_hafiz_id",
            value=hafizs_user.hafiz_id,
            hx_post="/users/hafiz_selection",
            hx_target="body",
            hx_replace_url="true",
            cls=ButtonT.primary,
            data_testid=f"switch-{hafiz_name}-hafiz-button",
        ),
        cls="min-w-[300px] max-w-[400px]",
    )


def render_hafiz_selection_page(cards, hafiz_form):
    """Render hafiz selection page"""
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
