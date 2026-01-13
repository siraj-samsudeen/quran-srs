from fasthtml.common import *
from monsterui.all import *
from app.admin_model import get_column_headers, get_column_and_its_type, get_table_records
from database import db

# We need the list of tables for the sidebar
tables = db.t

def tables_main_area(*args, active_table=None, auth=None):
    is_active = lambda x: "uk-active" if x == active_table else None

    tables_list = [
        t for t in str(tables).split(", ") if not t.startswith(("sqlite", "_"))
    ]
    table_links = [
        Li(
            A(t.capitalize(), href=f"/admin/tables/{t}", data_testid=f"{t}-link"),
            cls=is_active(t),
        )
        for t in tables_list
    ]

    side_nav = NavContainer(
        NavParentLi(
            H4("Tables", cls="pl-4"),
            NavContainer(*table_links, parent=False),
        )
    )

    return main_area(
        Div(
            Div(side_nav, cls="flex-1 p-2"),
            (
                Div(*args, cls="flex-[4] border-l-2 p-4", id="table_view")
                if args
                else None
            ),
            cls=(FlexT.block, FlexT.wrap),
        ),
        active="Tables",
        auth=auth,
    )

def render_backups_list(files, auth):
    def render_dbs(file_name: str):
        return Li(
            A(
                file_name,
                href=f"/admin/backups/{file_name}",
                cls=AT.classic,
                hx_boost="false",
            ),
            cls=ListT.bullet,
        )

    return main_area(
        Div(
            H1("Database Backups", cls=TextT.center),
            Ul(*map(render_dbs, files)),
            cls="space-y-6",
        ),
        auth=auth,
        active="Admin",
    )

def render_table_view(table, records, columns, auth):
    if table == "modes":
        primary_key_column = "code"
    else:
        primary_key_column = "id"

    def _render_rows(data: dict):
        def render_cell(column: str):
            if column == primary_key_column:
                return Td(
                    A(
                        data[column],
                        href=f"/admin/tables/{table}/{data[column]}/edit",
                        cls=AT.muted,
                    ),
                    data_testid="row-id",
                )
            return Td(data[column])

        return Tr(
            *map(render_cell, columns),
            Td(
                A(
                    "Delete",
                    hx_delete=f"/admin/tables/{table}/{data[primary_key_column]}",
                    target_id=f"row-{data[primary_key_column]}",
                    hx_swap="outerHTML",
                    hx_confirm="Are you sure?",
                    cls=AT.muted,
                ),
            ),
            id=f"row-{data[primary_key_column]}",
        )

    table_element = Table(
        Thead(Tr(*map(Th, columns), Th("Action"))),
        Tbody(*map(_render_rows, records), data_testid=f"{table}-rows"),
    )
    return tables_main_area(
        Div(
            DivFullySpaced(
                DivLAligned(
                    A(
                        UkIcon("undo-2", height=15, width=15),
                        cls="px-6 py-3 shadow-md rounded-sm",
                        href=f"/admin/tables",
                    ),
                    A(
                        Button("New", type="button", cls=ButtonT.link),
                        href=f"/admin/tables/{table}/new",
                    ),
                ),
                DivRAligned(
                    A(
                        Button("Export", type="button", cls=ButtonT.link),
                        href=f"/admin/tables/{table}/export",
                        hx_boost="false",
                    ),
                    A(
                        Button("Import", type="button", cls=ButtonT.link),
                        href=f"/admin/tables/{table}/import",
                    ),
                ),
            ),
            Div(table_element, cls="uk-overflow-auto"),
            cls="space-y-3",
        ),
        active_table=table,
        auth=auth,
    )

def create_dynamic_input_form(schema: dict, **kwargs):
    input_types_map = {"int": "number", "str": "text", "date": "date"}

    def create_input_field(o: dict):
        column, datatype = o
        if column in ["id", "code"]:
            return None
        # This is used to get the datatype of the columns as a dict
        datatype = datatype.__args__[0].__name__
        input_type = input_types_map.get(datatype, "text")
        # The datatype for the `date column` are stored in str
        # so we are checking if the 'date' is in the column name
        if "date" in column:
            input_type = "date"
        # The bool datatype is stored in int
        # so we are creating a column list that are type boolean to compare against column name
        if column in ["completed"]:
            return Div(
                FormLabel(column),
                LabelRadio(label="True", id=f"{column}-1", name=column, value="1"),
                LabelRadio(label="False", id=f"{column}-2", name=column, value="0"),
                cls="space-y-2",
            )
        return LabelInput(column, type=input_type)

    return Form(
        *map(create_input_field, schema.items()),
        DivFullySpaced(
            Button("Save"),
            A(Button("Discard", type="button"), onclick="history.back()"),
        ),
        **kwargs,
        cls="space-y-4",
    )

def render_edit_record_view(table, primary_key, current_data, auth):
    column_with_types = get_column_and_its_type(table)
    form = create_dynamic_input_form(
        column_with_types,
        hx_put=f"/admin/tables/{table}/{primary_key}",
        hx_target="body",
        hx_push_url="true",
        # The redirect_link is when we edit the description from the different page it should go back to that page
        hx_vals={"redirect_link": f"/admin/tables/{table}"},
    )

    return tables_main_area(
        Titled(f"Edit page", fill_form(form, current_data)),
        active_table=table,
        auth=auth,
    )

def render_new_record_view(table, auth):
    column_with_types = get_column_and_its_type(table)
    return tables_main_area(
        Titled(
            f"Add page",
            create_dynamic_input_form(
                column_with_types, hx_post=f"/admin/tables/{table}"
            ),
        ),
        active_table=table,
        auth=auth,
    )

def render_import_view(table, auth):
    form = Form(
        UploadZone(
            DivCentered(Span("Upload Zone"), UkIcon("upload")),
            id="file",
            accept="text/csv",
        ),
        DivFullySpaced(
            Button("Submit"),
            Button(
                "Preview",
                type="button",
                hx_post=f"/admin/tables/{table}/import/preview",
                hx_include="#file",
                hx_encoding="multipart/form-data",
                target_id="preview_table",
                hx_push_url="false",
            ),
            Button("Cancel", type="button", onclick="history.back()"),
        ),
        action=f"/admin/tables/{table}/import",
        method="POST",
    )
    return tables_main_area(
        Titled(
            f"Upload CSV",
            P(
                f"CSV should contain only these columns: ",
                Span(
                    " ,".join(get_column_headers(table)), cls=TextPresets.md_weight_sm
                ),
            ),
            form,
            Div(id="preview_table"),
            cls="space-y-4",
        ),
        active_table=table,
        auth=auth,
    )

def render_import_preview(table, filename, columns, records):
    if sorted(columns) != sorted(get_column_headers(table)):
        return Div(
            H3("Filename: ", filename),
            P("Please check the columns in the CSV file", cls="text-red-500"),
        )

    def _render_rows(data: dict):
        return Tr(
            *map(lambda col: Td(data[col]), columns),
        )

    preview_table = Table(
        Thead(Tr(*map(Th, columns))),
        Tbody(*map(_render_rows, records)),
    )
    return Div(H3("Filename: ", filename), Div(preview_table))
