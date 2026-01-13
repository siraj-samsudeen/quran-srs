from fasthtml.common import *
from monsterui.all import *
from utils import *
from app.common_model import get_current_date
from app.common_view import (
    render_rating, 
    main_area,
)
from app.components.display import PageDescription
from app.components.forms import RatingRadio
from app.revision_model import get_revision_table_data
from database import *


def action_buttons():
    # Enable/disable buttons based on checkbox selection
    dynamic_enable_button_hyperscript = "on checkboxChanged if first <input[type=checkbox]:checked/> remove @disabled else add @disabled"
    import_export_buttons = DivLAligned(
        Button(
            "Bulk Edit",
            hx_post="/revision/bulk_edit",
            hx_push_url="true",
            hx_include="closest form",
            hx_target="body",
            cls="toggle_btn",  # To disable and enable the button based on the checkboxes (Don't change, it is referenced in hyperscript)
            disabled=True,
            _=dynamic_enable_button_hyperscript,
        ),
        Button(
            "Bulk Delete",
            hx_delete="/revision",
            hx_confirm="Are you sure you want to delete these revisions?",
            hx_target="body",
            cls=("toggle_btn", ButtonT.destructive),
            disabled=True,
            _=dynamic_enable_button_hyperscript,
        ),
        A(
            Button("Export", type="button"),
            href="tables/revisions/export",
            hx_boost="false",
        ),
    )
    return DivFullySpaced(
        Div(),
        import_export_buttons,
        cls="flex-wrap gap-4 mb-3",
    )


def generate_revision_table_part(part_num: int = 1, size: int = 20) -> Tuple[Tr]:
    def _render_rows(rev: Revision):
        return Tr(
            Td(
                CheckboxX(
                    name="ids",
                    value=rev.id,
                    cls="revision_ids",
                    # To trigger the checkboxChanged event to the bulk edit and bulk delete buttons
                    _="on click send checkboxChanged to .toggle_btn",
                    _at_click="handleCheckboxClick($event)",
                )
            ),
            Td(
                PageDescription(item_id=rev.item_id, is_link=False),
            ),
            Td(rev.mode_code),
            Td(rev.plan_id),
            Td(render_rating(rev.rating)),
            Td(date_to_human_readable(rev.revision_date)),
            Td(
                A(
                    "Delete",
                    hx_delete=f"/revision/delete/{rev.id}",
                    target_id=f"revision-{rev.id}",
                    hx_swap="outerHTML",
                    hx_confirm="Are you sure?",
                    cls=AT.muted,
                ),
            ),
            id=f"revision-{rev.id}",
        )

    paginated = [_render_rows(i) for i in get_revision_table_data(part_num, size)]

    if len(paginated) == 20:
        paginated[-1].attrs.update(
            {
                "get": f"revision?idx={part_num + 1}",
                "hx-trigger": "revealed",
                "hx-swap": "afterend",
                "hx-select": "tbody > tr",
            }
        )
    return tuple(paginated)


def create_revision_form(type, auth, backlink="/"):
    def _option(obj):
        name = obj.name
        id = obj.id
        return Option(
            f"{id} ({name})",
            value=id,
            # FIXME: Temp condition for selecting siraj, later it should be handled by sess
            # Another caviat is that siraj should be in the top of the list of users
            # or else the edit functionality will not work properly.
            selected=True if "siraj" in name.lower() else False,
        )

    additional_fields = (
        LabelInput(
            "Revision Date",
            name="revision_date",
            type="date",
            value=get_current_date(auth),
            cls="space-y-2 col-span-2",
        ),
    )

    return Form(
        Hidden(name="id"),
        Hidden(name="item_id"),
        Hidden(name="plan_id"),
        # Hide the User selection temporarily
        LabelSelect(
            *map(_option, hafizs()), label="Hafiz Id", name="hafiz_id", cls="hidden"
        ),
        *additional_fields,
        RatingRadio(),
        Div(
            Button("Save", name="backlink", value=backlink, cls=ButtonT.primary),
            A(Button("Cancel", type="button", cls=ButtonT.secondary), href=backlink),
            cls="flex justify-around items-center w-full",
        ),
        action=f"/revision/{type}",
        method="POST",
    )


def render_revision_table(auth, idx: int | None = 1):
    table = Table(
        Thead(
            Tr(
                Th(),  # empty header for checkbox
                Th("Page"),
                Th("Mode"),
                Th("Plan Id"),
                Th("Rating"),
                Th("Revision Date"),
                Th("Action"),
            )
        ),
        Tbody(*generate_revision_table_part(part_num=idx)),
        x_data=select_all_checkbox_x_data(class_name="revision_ids"),
    )
    return main_area(
        # To send the selected revision ids for bulk delete and bulk edit buttons
        Form(
            action_buttons(),
            Div(table, cls="uk-overflow-auto"),
        ),
        active="Revision",
        auth=auth,
    )