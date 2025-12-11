"""
Hafiz view components - UI rendering for hafiz management.

Extracted from users_view.py for better separation of concerns.
"""

from fasthtml.common import *
from monsterui.all import *


# ============================================================================
# HIGH-LEVEL VIEWS (What users see)
# ============================================================================


def render_hafiz_selection_page(cards, hafiz_form):
    """
    Render the hafiz selection page.

    Shows all hafizs for the current user with option to add new one.
    """
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
# MID-LEVEL COMPONENTS (Building blocks)
# ============================================================================


def render_hafiz_card(hafiz, auth):
    """
    Render a hafiz selection card.

    Shows different UI based on whether this is the currently active hafiz:
    - Current hafiz: Green background with "Go Back to [name]" button
    - Other hafizs: White background with name button + delete dropdown menu
    """
    is_current_hafiz = auth == hafiz.id

    if is_current_hafiz:
        return Div(
            Button(
                f"← Go Back to {hafiz.name}",
                name="current_hafiz_id",
                value=hafiz.id,
                hx_post="/hafiz/selection",
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
                hx_post="/hafiz/selection",
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
                        hx_delete=f"/hafiz/delete/{hafiz.id}",
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
# LOW-LEVEL COMPONENTS (Forms, cards)
# ============================================================================


def render_add_hafiz_form():
    """Render form for creating a new hafiz"""
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
                action="/hafiz/add",
                method="post",
            ),
        ),
        cls="w-[300px]",
    )
