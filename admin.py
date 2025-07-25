from fasthtml.common import *
from monsterui.all import *
from io import BytesIO
import pandas as pd

from utils import (
    get_database_connection,
    format_number,
    render_date,
    select_all_with_shift_click_for_summary_table,
    calculate_days_difference,
    get_database_path,
    backup_sqlite_db,
)
from common_function import (
    main_area,
    get_current_date,
    get_page_description,
    create_app_with_auth,
    get_start_text,
    custom_select,
    get_mode_name,
    start_srs,
)

OPTION_MAP = {
    "role": ["hafiz", "parent", "teacher", "parent_hafiz"],
    "age_group": ["child", "teen", "adult"],
    "relationship": ["self", "parent", "teacher", "sibling"],
}

db = get_database_connection()
tables = db.t

revisions = db.t.revisions
items = db.t.items
hafizs_items = db.t.hafizs_items
hafizs = db.t.hafizs

(Revision, Item, Hafiz) = (
    revisions.dataclass(),
    items.dataclass(),
    hafizs.dataclass(),
)

admin_app, rt = create_app_with_auth()


def tables_main_area(*args, active_table=None, auth=None):
    is_active = lambda x: "uk-active" if x == active_table else None

    tables_list = [
        t for t in str(tables).split(", ") if not t.startswith(("sqlite", "_"))
    ]
    table_links = [
        Li(A(t.capitalize(), href=f"/admin/tables/{t}"), cls=is_active(t))
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


def get_column_headers(table):
    data_class = tables[table].dataclass()
    columns = [k for k in data_class.__dict__.keys() if not k.startswith("_")]
    return columns


def render_options(option):
    return Option(
        option.capitalize(),
        value=option,
    )


@admin_app.get("/backups")
def list_backups(auth):
    files = [f for f in os.listdir("data/backup") if f.endswith(".db")]
    files = sorted(files, reverse=True)

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
        active="Backups",
    )


@admin_app.get("/backups/{file}")
def download_backup(file: str):
    return FileResponse(f"data/backup/{file}", media_type="application/octet-stream")


@admin_app.get("/change_current_date")
def change_current_date(auth):
    current_date = get_current_date(auth)
    label_input = LabelInput(
        label="Current date",
        id="current_date",
        type="date",
        value=current_date,
        hx_post="/admin/change_current_date",
        hx_target="body",
        hx_trigger="change",
    )
    return main_area(label_input, auth=auth)


@admin_app.post("/change_current_date")
def update_current_date(auth, current_date: str):
    current_hafiz = hafizs[auth]
    current_hafiz.current_date = current_date
    hafizs.update(current_hafiz)
    return RedirectResponse("/admin/change_current_date", status_code=303)


@admin_app.get("/import_db")
def import_db_view(auth):
    current_dbs = [
        Li(f, cls=ListT.circle) for f in os.listdir("data") if f.endswith(".db")
    ]
    form = Form(
        UploadZone(
            DivCentered(Span("Upload Zone"), UkIcon("upload")),
            id="file",
            accept=".db",
        ),
        Button("Submit"),
        action="/admin/import_db",
        method="POST",
    )
    return main_area(
        Div(
            Div(H2("Current DBs"), Ul(*current_dbs)),
            Div(H1("Upload DB"), form),
            cls="space-y-6",
        ),
        active="Revision",
        auth=auth,
    )


@admin_app.post("/import_db")
async def import_db_handler(file: UploadFile):
    path = "data/" + file.filename
    if get_database_path() == path:
        return Titled("Error", P("Cannot overwrite the current DB"))

    file_content = await file.read()
    with open(path, "wb") as f:
        f.write(file_content)

    return RedirectResponse("/")


@admin_app.get("/backup")
def backup_active_db():
    db_path = get_database_path()
    if not os.path.exists(db_path):
        return Titled("Error", P("Database file not found"))

    backup_path = backup_sqlite_db(db_path, "data/backup")

    return FileResponse(backup_path, filename="quran_backup.db")


@admin_app.get("/tables")
def list_tables(auth):
    return tables_main_area(auth=auth)


@admin_app.get("/tables/{table}")
def view_table(table: str, auth):
    records = db.q(f"SELECT * FROM {table}")
    columns = get_column_headers(table)

    def _render_rows(data: dict):
        def render_cell(column: str):
            if column == "id":
                return Td(
                    A(
                        data[column],
                        href=f"/admin/tables/{table}/{data[column]}/edit",
                        cls=AT.muted,
                    )
                )
            return Td(data[column])

        return Tr(
            *map(render_cell, columns),
            Td(
                A(
                    "Delete",
                    hx_delete=f"/admin/tables/{table}/{data["id"]}",
                    target_id=f"row-{data["id"]}",
                    hx_swap="outerHTML",
                    hx_confirm="Are you sure?",
                    cls=AT.muted,
                ),
            ),
            id=f"row-{data["id"]}",
        )

    table_element = Table(
        Thead(Tr(*map(Th, columns), Th("Action"))),
        Tbody(*map(_render_rows, records)),
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
        if column == "id":
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
        if column in ["role", "age_group", "relationship"]:
            return (
                LabelSelect(
                    *map(render_options, OPTION_MAP[column]),
                    label=column.capitalize(),
                    name=column,
                ),
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


@admin_app.get("/tables/{table}/{record_id}/edit")
def edit_record_view(table: str, record_id: int, auth):
    current_table = tables[table]
    current_data = current_table[record_id]

    # The `completed` column is stored in int but it needs to be considered as bool
    # so we are converting it to str in order to select the right radio button using fill_form
    if table == "plans":
        current_data.completed = str(current_data.completed)

    column_with_types = get_column_and_its_type(table)
    form = create_dynamic_input_form(
        column_with_types,
        hx_put=f"/admin/tables/{table}/{record_id}",
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


def get_column_and_its_type(table):
    data_class = tables[table].dataclass()
    return data_class.__dict__["__annotations__"]


@admin_app.put("/tables/{table}/{record_id}")
async def update_record(table: str, record_id: int, redirect_link: str, req: Request):
    formt_data = await req.form()
    current_data = formt_data.__dict__.get("_dict")
    # replace the value to `None` in order to set it as unset if the value came as empty
    current_data = {
        key: (value if value != "" else None)
        for key, value in current_data.items()
        if key != "redirect_link"
    }

    tables[table].update(current_data, record_id)

    return RedirectResponse(redirect_link, status_code=303)


@admin_app.delete("/tables/{table}/{record_id}")
def delete_record(table: str, record_id: int):
    try:
        tables[table].delete(record_id)
    except Exception as e:
        return Tr(Td(P(f"Error: {e}"), colspan="11", cls="text-center"))


@admin_app.get("/tables/{table}/new")
def new_record_view(table: str, auth):
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


@admin_app.post("/tables/{table}")
async def create_new_record(table: str, req: Request):
    formt_data = await req.form()
    current_data = formt_data.__dict__.get("_dict")
    tables[table].insert(current_data)
    return Redirect(f"/admin/tables/{table}")


@admin_app.get("/tables/{table}/export")
def export_specific_table(table: str):
    df = pd.DataFrame(tables[table](), columns=get_column_and_its_type(table).keys())

    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False, header=True)
    csv_buffer.seek(0)

    file_name = f"{table}.csv"
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )


@admin_app.get("/tables/{table}/import")
def import_specific_table_view(table: str):
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
    )


@admin_app.post("/tables/{table}/import/preview")
async def import_specific_table_preview(table: str, file: UploadFile):
    file_content = await file.read()
    imported_df = pd.read_csv(BytesIO(file_content)).fillna("")
    columns = imported_df.columns.tolist()
    records = imported_df.to_dict(orient="records")

    if sorted(columns) != sorted(get_column_headers(table)):
        return Div(
            H3("Filename: ", file.filename),
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
    return Div(H3("Filename: ", file.filename), Div(preview_table))


@admin_app.post("/tables/{table}/import")
async def import_specific_table(table: str, file: UploadFile):
    backup_sqlite_db(get_database_path(), "data/backup")
    # Instead of using the `import_file` method, we are using `upsert` method to import the csv file
    # as some of the forign key values are being used in another table
    # so we cannot truncate the table
    file_content = await file.read()
    data = pd.read_csv(BytesIO(file_content)).to_dict("records")
    for record in data:
        tables[table].upsert(record)

    return Redirect(f"/admin/tables/{table}")
