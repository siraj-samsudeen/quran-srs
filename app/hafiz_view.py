"""
Hafiz View Module

UI components for hafiz settings page.
"""

from fasthtml.common import *
from monsterui.all import *
from .utils import standardize_column
from .common_view import main_area


def render_settings_form(current_hafiz):
    """Render the hafiz settings form."""

    def render_field(label, field_type, required=True, **kwargs):
        field_name = standardize_column(label)
        value = getattr(current_hafiz, field_name)
        return LabelInput(
            label,
            id=field_name,
            type=field_type,
            value=value,
            required=required,
            **kwargs,
        )

    return Form(
        render_field("Name", "text"),
        render_field("Daily Capacity", "number", False),
        render_field("Current Date", "date"),
        DivFullySpaced(
            DivLAligned(
                Button("Update", type="submit", cls=ButtonT.primary),
                Button(
                    "Discard",
                    hx_get="/hafiz/settings",
                    hx_target="body",
                    cls=ButtonT.destructive,
                ),
            ),
            A(Button("Theme", cls=ButtonT.secondary), href="/hafiz/theme"),
        ),
        action="/hafiz/settings",
        method="POST",
    )


def render_settings_page(current_hafiz, auth):
    """Render the complete settings page."""
    form = render_settings_form(current_hafiz)
    return main_area(
        Div(
            H1("Hafiz Preferences", cls=TextT.center),
            Div(form, cls="max-w-xl mx-auto"),
            cls="space-y-6",
        ),
        auth=auth,
        active="Settings",
    )


def render_theme_page(auth):
    """Render the theme picker page."""
    return main_area(ThemePicker(), active="Settings", auth=auth)
