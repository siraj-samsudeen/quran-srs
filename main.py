from fasthtml.common import *
from monsterui.all import *
from utils import *
import pandas as pd
from io import BytesIO

RATING_MAP = {"1": "✅ Good", "0": "😄 Ok", "-1": "❌ Bad"}
DB_PATH = "data/quran_v3.db"

db = database(DB_PATH)
tables = db.t
revisions, users = tables.revisions, tables.users
plans, modes, pages = tables.plans, tables.modes, tables.pages
if revisions not in tables:
    users.create(id=int, name=str, email=str, password=str, pk="id")
    revisions.create(
        id=int,
        mode_id=int,
        plan_id=int,
        user_id=int,
        page_id=int,
        revision_date=str,
        rating=int,
        pk="id",
    )
if modes not in tables:
    modes.create(id=int, name=str, description=str, pk="id")
if plans not in tables:
    plans.create(
        id=int,
        mode_id=str,
        start_date=str,
        end_date=str,
        start_page=int,
        end_page=int,
        revision_count=int,
        page_count=int,
        completed=bool,
        pk="id",
    )
if pages not in tables:
    pages.create(
        id=int, page=int, juz=str, surah=str, description=str, start=str, pk="id"
    )
Revision, User = revisions.dataclass(), users.dataclass()
Plan, Mode, Page = plans.dataclass(), modes.dataclass(), pages.dataclass()

hyperscript_header = Script(src="https://unpkg.com/hyperscript.org@0.9.14")
alpinejs_header = Script(
    src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js", defer=True
)
app, rt = fast_app(
    hdrs=(Theme.blue.headers(), hyperscript_header, alpinejs_header),
    bodykw={"hx-boost": "true"},
)


def get_column_headers(table):
    data_class = tables[table].dataclass()
    columns = [k for k in data_class.__dict__.keys() if not k.startswith("_")]
    return columns


def mode_dropdown(default_mode=1):
    def mk_options(mode):
        id, name = mode.id, mode.name
        is_selected = lambda m: m == default_mode
        return Option(name, value=id, selected=is_selected(id))

    return LabelSelect(
        map(mk_options, modes()),
        label="Mode Id",
        name="mode_id",
    )


def action_buttons(last_added_page=1, source="Home"):

    if isinstance(last_added_page, int):
        last_added_page += 1
    entry_buttons = Form(
        DivLAligned(
            Input(
                type="text",
                placeholder="page",
                cls="max-w-12 sm:max-w-16",
                id="page",
                value=last_added_page,
                autocomplete="off",
            ),
            Button("Bulk Entry", name="type", value="bulk", cls=ButtonT.link),
            Button("Single Entry", name="type", value="single", cls=ButtonT.link),
            cls=("gap-3", FlexT.wrap),
        ),
        action="/revision/entry",
        method="POST",
    )
    # Enable and Disable the button based on the checkbox selection
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
        # A(Button("Import"), href=import_csv),
        A(Button("Export", type="button"), href=export_csv, hx_boost="false"),
    )
    return DivFullySpaced(
        entry_buttons if source == "Home" else Div(),
        import_export_buttons if source == "Revision" else Div(),
        cls="flex-wrap gap-4 mb-3",
    )


def main_area(*args, active=None):
    is_active = lambda x: AT.primary if x == active else None
    return Title("Quran SRS"), Container(
        Div(
            NavBar(
                A("Home", href=index, cls=is_active("Home")),
                A("Revision", href=revision, cls=is_active("Revision")),
                A("Tables", href="/tables", cls=is_active("Tables")),
                # A("User", href=user, cls=is_active("User")), # The user nav is temporarily disabled
                brand=H3(A("Quran SRS", href=index)),
            ),
            DividerLine(y_space=0),
            cls="bg-white sticky top-0 z-10",
        ),
        Main(*args, cls="p-4", id="main") if args else None,
        cls=ContainerT.xl,
    )


@rt
def index():
    try:
        last_added_record = revisions()[-1]
    except IndexError:
        last_added_page = None
    else:
        last_added_page = last_added_record.page_id

    def split_page_range(page_range: str):
        start_page, end_page = (
            page_range.split("-") if "-" in page_range else [page_range, None]
        )
        start_page = int(start_page)
        end_page = int(end_page) if end_page else None
        return start_page, end_page

    def render_page(page):
        page_data = pages[page]
        return Span(Span(page, cls=TextPresets.bold_sm), f" - {page_data.description}")

    ################### Datewise summary ###################
    qry = f"SELECT MIN(revision_date) AS earliest_date FROM {revisions}"
    result = db.q(qry)
    earliest_date = result[0]["earliest_date"]
    current_date = current_time("%Y-%m-%d")

    date_range = pd.date_range(
        start=(earliest_date or current_date), end=current_date, freq="D"
    )
    date_range = [date.strftime("%Y-%m-%d") for date in date_range][::-1]

    def _render_datewise_row(date):
        current_date_revisions = [
            r.__dict__ for r in revisions(where=f"revision_date = '{date}'")
        ]
        pages_list = sorted([r["page_id"] for r in current_date_revisions])

        def _render_page_range(page_range: str):
            start_page, end_page = split_page_range(page_range)
            # Get the ids for all the pages for the particular date
            ids = [
                str(d["id"])
                for page in range(start_page, (end_page or start_page) + 1)
                for d in current_date_revisions
                if d.get("page_id") == page
            ]
            if end_page:
                ctn = (render_page(start_page), Span(" -> "), render_page(end_page))
            else:
                ctn = render_page(start_page)
            return P(
                A(
                    *ctn,
                    hx_get=f"/revision/bulk_edit?ids={','.join(ids)}",
                    hx_push_url="true",
                    hx_target="body",
                    cls=AT.classic,
                )
            )

        return Tr(
            Td(date_to_human_readable(date)),
            Td(len(pages_list)),
            Td(
                *(
                    map(_render_page_range, compact_format(pages_list).split(", "))
                    if pages_list
                    else "-"
                ),
                cls="space-y-3",
            ),
        )

    datewise_table = Div(
        # H1("Datewise summary"),
        Table(
            Thead(Tr(Th("Date"), Th("Count"), Th("Range"))),
            Tbody(*map(_render_datewise_row, date_range)),
        ),
        cls="uk-overflow-auto",
    )

    ################### Overall summary ###################
    qry = f"SELECT DISTINCT mode_id || '-' || plan_id AS combined_value FROM {revisions} ORDER BY combined_value"
    result = db.q(qry)
    unique_mode_and_plan_id = [i["combined_value"] for i in result]

    # To get the unique page ranges for the combination of mode and plan_id
    unique_page_ranges = []
    for mp in unique_mode_and_plan_id:
        if not mp:
            continue
        mode_id, plan_id = mp.split("-")
        pages_list = sorted(
            [
                r.page_id
                for r in revisions(
                    where=f"mode_id = '{mode_id}' AND plan_id = '{plan_id}'"
                )
            ]
        )
        for p in compact_format(pages_list).split(", "):
            unique_page_ranges.append(
                {"mode_id": mode_id, "plan_id": plan_id, "page_range": p}
            )

    def render_overall_row(o: dict):
        plan_id, mode_id, page_range = o["plan_id"], o["mode_id"], o["page_range"]
        if not page_range:
            return None

        start_page, end_page = split_page_range(page_range)
        next_page = (end_page or start_page) + 1

        mode = modes[mode_id]

        current_plan = plans(where=f"id = '{plan_id}' AND mode_id = '{mode_id}'")
        if current_plan:
            is_completed = current_plan[0].completed
        else:
            is_completed = False

        return Tr(
            Td(mode.name if mode else mode_id),
            Td(A(plan_id, href=f"/tables/plans/{plan_id}/edit", cls=AT.muted)),
            Td(page_range),
            Td(render_page(start_page)),
            (Td(render_page(end_page) if end_page else None)),
            Td(
                (
                    A(
                        render_page(next_page),
                        href=f"revision/bulk_add?page={next_page}&mode_id={mode_id}&plan_id={plan_id}",
                        cls=AT.classic,
                    )
                    if not is_completed
                    else "Completed"
                ),
            ),
        )

    overall_table = Div(
        # H1("Overall summary"),
        Table(
            Thead(
                Tr(
                    Th("Mode"),
                    Th("Plan Id"),
                    Th("Range"),
                    Th("Start"),
                    Th("End"),
                    Th("Continue"),
                )
            ),
            Tbody(*map(render_overall_row, unique_page_ranges)),
        ),
        cls="uk-overflow-auto",
    )

    return main_area(
        action_buttons(
            **(
                {"last_added_page": last_added_page}
                if last_added_page is not None
                else {}
            )
        ),
        Div(overall_table, Divider(), datewise_table),
        active="Home",
    )


@app.get("/tables")
def list_tables():
    tables_list = [t for t in str(tables).split(", ") if not t.startswith("sqlite")]
    return main_area(
        Div(
            H1("Tables"),
            Ul(
                *[
                    Li(A(t, href=f"/tables/{t}", cls=AT.classic), cls=ListT.bullet)
                    for t in tables_list
                ]
            ),
        ),
        active="Tables",
    )


@app.get("/tables/{table}")
def view_table(table: str):
    records = db.q(f"SELECT * FROM {table}")
    columns = get_column_headers(table)

    def _render_rows(data: dict):
        def render_cell(column: str):
            if column == "id":
                return Td(
                    A(
                        data[column],
                        href=f"/tables/{table}/{data[column]}/edit",
                        cls=AT.muted,
                    )
                )
            return Td(data[column])

        return Tr(
            *map(render_cell, columns),
            Td(
                A(
                    "Delete",
                    hx_delete=f"/tables/{table}/{data["id"]}",
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
    return main_area(
        Div(
            H2(f"Table: {table}"),
            DivFullySpaced(
                DivLAligned(
                    A(
                        UkIcon("undo-2", height=15, width=15),
                        cls="px-6 py-3 shadow-md rounded-sm",
                        href=f"/tables",
                    ),
                    A(
                        Button("New", type="button", cls=ButtonT.link),
                        href=f"/tables/{table}/new",
                    ),
                ),
                DivRAligned(
                    A(
                        Button("Export", type="button", cls=ButtonT.link),
                        href=f"/tables/{table}/export",
                        hx_boost="false",
                    ),
                    A(
                        Button("Import", type="button", cls=ButtonT.link),
                        href=f"/tables/{table}/import",
                    ),
                ),
            ),
            Div(table_element, cls="uk-overflow-auto"),
            cls="space-y-3",
        ),
        active="Tables",
    )


def create_input_form(schema: dict, **kwargs):
    input_types_map = {"int": "number", "str": "text", "date": "date"}

    def create_input_field(o: dict):
        column, datatype = o
        if column == "id":
            return None
        # datatype is an union type, so we need to extract the first element using __args__
        # and it returns datatype class so to get the name we'll use __name__ attribute
        datatype = datatype.__args__[0].__name__
        input_type = input_types_map.get(datatype, "text")
        # The datatype for the date column are stored in str
        # so we are checking if the 'date'  is in the column name
        if "date" in column:
            input_type = "date"
        # The bool datatype is stored in int
        # so we are creating a column list that are bool to compare against column name
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


@app.get("/tables/{table}/{record_id}/edit")
def edit_record_view(table: str, record_id: int):
    current_table = tables[table]
    current_data = current_table[record_id]

    # The completed column is stored in int and it is considered as bool
    # so we are converting it to str in order to select the right radio button using fill_form
    if table == "plans":
        current_data.completed = str(current_data.completed)

    column_with_types = get_column_and_its_type(table)
    form = create_input_form(column_with_types, hx_put=f"/tables/{table}/{record_id}")

    return main_area(
        Titled(f"Edit page - {table}", fill_form(form, current_data)), active="Tables"
    )


def get_column_and_its_type(table):
    data_class = tables[table].dataclass()
    return data_class.__dict__["__annotations__"]


@app.put("/tables/{table}/{record_id}")
async def update_record(table: str, record_id: int, req: Request):
    formt_data = await req.form()
    current_data = formt_data.__dict__.get("_dict")
    tables[table].update(current_data, record_id)

    return Redirect(f"/tables/{table}")


@app.delete("/tables/{table}/{record_id}")
def delete_record(table: str, record_id: int):
    tables[table].delete(record_id)


@app.get("/tables/{table}/new")
def new_record_view(table: str):
    column_with_types = get_column_and_its_type(table)
    return main_area(
        Titled(
            f"Add page - {table}",
            create_input_form(column_with_types, hx_post=f"/tables/{table}"),
        ),
        active="Tables",
    )


@app.post("/tables/{table}")
async def create_new_record(table: str, req: Request):
    formt_data = await req.form()
    current_data = formt_data.__dict__.get("_dict")
    tables[table].insert(current_data)
    return Redirect(f"/tables/{table}")


@app.get("/tables/{table}/export")
def export_specific_table(table: str):
    df = pd.DataFrame(tables[table]())

    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    file_name = f"{table}_{current_time("%Y%m%d%I%M")}"
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={file_name}.csv"},
    )


@app.get("/tables/{table}/import")
def import_specific_table_view(table: str):
    form = Form(
        UploadZone(
            DivCentered(Span("Upload Zone"), UkIcon("upload")),
            id="file",
            accept="text/csv",
        ),
        DivFullySpaced(
            Button("Submit"), Button("Cancel", type="button", onclick="history.back()")
        ),
        action=f"/tables/{table}/import",
        method="POST",
    )
    return main_area(
        Titled(
            f"Upload CSV: {table}",
            P(
                f"CSV should contain these columns: ",
                Span(
                    " ,".join(get_column_headers(table)), cls=TextPresets.md_weight_sm
                ),
            ),
            form,
            cls="space-y-4",
        ),
        active="Tables",
    )


@app.post("/tables/{table}/import")
async def import_specific_table(table: str, file: UploadFile):
    backup_sqlite_db(DB_PATH, "data/backup")
    # Instead of using the import_file method, we are using upsert method to import the csv file
    # as some of the forign key values are being used in another table
    # so we cannot truncate the table
    file_content = await file.read()
    data = pd.read_csv(BytesIO(file_content)).to_dict("records")
    for row in data:
        tables[table].upsert(row)

    return Redirect(f"/tables/{table}")


@app.get
def revision():

    def _render_revision(rev):
        current_page_quran_data = pages[rev.page_id]

        return Tr(
            # Td(rev.id),
            # Td(rev.user_id),
            Td(
                CheckboxX(
                    name="ids",
                    value=rev.id,
                    # To trigger the checkboxChanged event to the bulk edit and bulk delete buttons
                    _="on click send checkboxChanged to .toggle_btn",
                )
            ),
            Td(A(rev.page_id, href=f"/revision/edit/{rev.id}", cls=AT.muted)),
            # FIXME: Added temporarly to check is the date is added correctly and need to remove this
            Td(rev.mode_id),
            Td(rev.plan_id),
            Td(RATING_MAP.get(str(rev.rating))),
            Td(current_page_quran_data.surah),
            Td(current_page_quran_data.juz),
            Td(rev.revision_date),
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

    table = Table(
        Thead(
            Tr(
                # Columns are temporarily hidden
                # Th("Id"),
                # Th("User Id"),
                Th(),  # empty header for checkbox
                Th("Page"),
                # FIXME: Added temporarly to check is the date is added correctly and need to remove this
                Th("Mode"),
                Th("Plan Id"),
                Th("Rating"),
                Th("Surah"),
                Th("Juz"),
                Th("Revision Date"),
                Th("Action"),
            )
        ),
        Tbody(*map(_render_revision, revisions(order_by="id desc"))),
    )
    return main_area(
        # To send the selected revision ids for bulk delete and bulk edit
        Form(
            action_buttons(source="Revision"),
            Div(table, cls="uk-overflow-auto"),
        ),
        active="Revision",
    )


def create_revision_form(type):
    def RadioLabel(o):
        value, label = o
        is_checked = True if value == "1" else False
        return Div(
            FormLabel(
                Radio(
                    id="rating", value=value, checked=is_checked, autofocus=is_checked
                ),
                Span(label),
                cls="space-x-2",
            )
        )

    def _option(obj):
        return Option(
            f"{obj.id} ({obj.name})",
            value=obj.id,
            # TODO: Temp condition for selecting siraj, later it should be handled by sess
            # Another caviat is that siraj should be in the top of the list of users
            # or else the edit functionality will not work properly.
            selected=True if "siraj" in obj.name.lower() else False,
        )

    return Form(
        Hidden(name="id"),
        # Hide the User selection temporarily
        LabelSelect(
            *map(_option, users()), label="User Id", name="user_id", cls="hidden"
        ),
        Grid(
            mode_dropdown(),
            LabelInput("Plan Id", name="plan_id", type="number"),
        ),
        LabelInput(
            "Revision Date",
            name="revision_date",
            type="date",
            value=current_time("%Y-%m-%d"),
        ),
        LabelInput("Page", name="page_id", type="number", input_cls="text-2xl"),
        Div(
            FormLabel("Rating"),
            *map(RadioLabel, RATING_MAP.items()),
            cls="space-y-2 leading-8 sm:leading-6 ",
        ),
        Div(
            Button("Save", cls=ButtonT.primary),
            A(Button("Cancel", type="button", cls=ButtonT.secondary), href=index),
            cls="flex justify-around items-center w-full",
        ),
        action=f"/revision/{type}",
        method="POST",
    )


@rt("/revision/edit/{revision_id}")
def get(revision_id: int):
    current_revision = revisions[revision_id]
    # Convert rating to string in order to make the fill_form to select the option.
    current_revision.rating = str(current_revision.rating)
    form = create_revision_form("edit")
    return main_area(
        Titled("Edit Revision", fill_form(form, current_revision)), active="Revision"
    )


@rt("/revision/edit")
def post(revision_details: Revision):
    revisions.update(revision_details)
    return Redirect(revision)


@rt("/revision/delete/{revision_id}")
def delete(revision_id: int):
    revisions.delete(revision_id)


@app.delete("/revision")
def revision_delete_all(ids: List[int]):
    for id in ids:
        revisions.delete(id)
    return RedirectResponse(revision, status_code=303)


# This is to handle the checkbox on revison page as it was coming as individual ids.
@app.post("/revision/bulk_edit")
def bulk_edit_redirect(ids: List[str]):
    return RedirectResponse(f"/revision/bulk_edit?ids={','.join(ids)}", status_code=303)


@app.get("/revision/bulk_edit")
def bulk_edit_view(ids: str):
    ids = ids.split(",")

    # Get the default values from the first selected revision
    first_revision = revisions[ids[0]]

    def _render_row(id):
        current_revision = revisions[id]

        def _render_radio(o):
            value, label = o

            is_checked = True if int(value) == current_revision.rating else False
            return FormLabel(
                Radio(name=f"rating-{id}", value=value, checked=is_checked),
                Span(label),
                cls="space-x-2",
            )

        return Tr(
            Td(
                CheckboxX(
                    name="ids",
                    value=id,
                    cls="revision_ids",
                    # _at_ is a alias for @
                    _at_click="handleCheckboxClick($event)",  # To handle `shift+click` selection
                )
            ),
            Td(P(current_revision.page_id)),
            Td(P(current_revision.revision_date)),
            Td(P(current_revision.mode_id)),
            Td(P(current_revision.plan_id)),
            Td(
                Div(
                    *map(_render_radio, RATING_MAP.items()),
                    cls=(FlexT.block, FlexT.row, FlexT.wrap, "gap-x-6 gap-y-4"),
                )
            ),
        )

    table = Table(
        Thead(
            Tr(
                Th(
                    CheckboxX(
                        cls="select_all",
                        x_model="selectAll",  # To update the current status of the checkbox (checked or unchecked)
                        _at_change="toggleAll()",  # based on that update the status of all the checkboxes
                    )
                ),
                Th("Page"),
                Th("Date"),
                Th("Mode"),
                Th("Plan ID"),
                Th("Rating"),
            )
        ),
        Tbody(*[_render_row(i) for i in ids]),
        # defining the reactive data for for component to reference (alpine.js)
        x_data="""
        { 
        selectAll: true,
        updateSelectAll() {
            const checkboxes = [...$el.querySelectorAll('.revision_ids')];
          this.selectAll = checkboxes.length > 0 && checkboxes.every(cb => cb.checked);
        },
        toggleAll() {
          $el.querySelectorAll('.revision_ids').forEach(cb => {
            cb.checked = this.selectAll;
          });
        },
        handleCheckboxClick(e) {
            // Handle shift+click selection
            if (e.shiftKey) {
                const checkboxes = [...$el.querySelectorAll('.revision_ids')];
                const currentCheckboxIndex = checkboxes.indexOf(e.target);
                
                // loop through the checkboxes backwards untll we find one that is checked
                for (let i = currentCheckboxIndex; i >= 0; i--) {
                    if (i != currentCheckboxIndex && checkboxes[i].checked) {break;}
                    checkboxes[i].checked = true;
                }
            }
            this.updateSelectAll();
        }
      }  
    """,
        # initializing the toggleAll function to select all the checkboxes by default.
        x_init="toggleAll()",
    )

    action_buttons = Div(
        Button("Save", cls=ButtonT.primary),
        Button(
            "Cancel", type="button", cls=ButtonT.secondary, onclick="history.back()"
        ),
        cls=(FlexT.block, FlexT.around, FlexT.middle, "w-full"),
    )

    return main_area(
        H1("Bulk Edit Revision"),
        Form(
            Grid(
                mode_dropdown(default_mode=first_revision.mode_id),
                LabelInput(
                    "Plan ID",
                    name="plan_id",
                    type="number",
                    value=first_revision.plan_id,
                ),
            ),
            Div(
                LabelInput(
                    "Revision Date",
                    name="revision_date",
                    type="date",
                    value=first_revision.revision_date,
                    cls="space-y-2 w-full",
                ),
                Button(
                    "Delete",
                    hx_delete="/revision",
                    hx_confirm="Are you sure you want to delete these revisions?",
                    hx_target="body",
                    hx_push_url="true",
                    cls=ButtonT.destructive,
                ),
                cls=(FlexT.block, FlexT.between, FlexT.bottom, "w-full gap-2"),
            ),
            Div(table, cls="uk-overflow-auto"),
            action_buttons,
            action="/revision",
            method="POST",
        ),
        active="Revision",
    )


@app.post("/revision")
async def bulk_edit_save(revision_date: str, mode_id: int, plan_id: int, req):
    form_data = await req.form()
    ids_to_update = form_data.getlist("ids")

    for name, value in form_data.items():
        if name.startswith("rating-"):
            current_id = name.split("-")[1]
            if current_id in ids_to_update:
                revisions.update(
                    Revision(
                        id=int(current_id),
                        rating=int(value),
                        revision_date=revision_date,
                        mode_id=mode_id,
                        plan_id=plan_id,
                    )
                )

    return RedirectResponse("/revision", status_code=303)


# This route is used to redirect to the appropriate revision entry form
@rt("/revision/entry")
def post(type: str, page: str):
    if type == "bulk":
        return Redirect(f"/revision/bulk_add?page={page}")
    elif type == "single":
        return Redirect(f"/revision/add?page={page}")


@rt("/revision/add")
def get(page: str, max_page: int = 605):
    if "." in page:
        page = page.split(".")[0]

    page = int(page)

    if page >= max_page:
        return Redirect(revision)

    try:
        last_added_record = revisions()[-1]
    except IndexError:
        defalut_mode_value = 1
        defalut_plan_value = None
    else:
        defalut_mode_value = last_added_record.mode_id
        defalut_plan_value = last_added_record.plan_id

    return main_area(
        Titled(
            f"{page} - {pages[page].description} - {pages[page].start}",
            fill_form(
                create_revision_form("add"),
                {
                    "page_id": page,
                    "mode_id": defalut_mode_value,
                    "plan_id": defalut_plan_value,
                },
            ),
        ),
        active="Revision",
    )


@rt("/revision/add")
def post(revision_details: Revision):
    # The id is set to zero in the form, so we need to delete it
    # before inserting to generate the id automatically
    del revision_details.id
    revisions.insert(revision_details)

    page = revision_details.page_id

    return Redirect(f"/revision/add?page={page + 1}")


@app.get("/revision/bulk_add")
def get(
    page: str,
    mode_id: int = None,
    plan_id: int = None,
    revision_date: str = None,
    length: int = 5,
    max_page: int = 605,
):

    if "." in page:
        page, length = map(int, page.split("."))
    else:
        page = int(page)

    if page >= max_page:
        return Redirect(revision)

    last_page = page + length

    if last_page > max_page:
        last_page = max_page

    def _render_row(current_page):
        def _render_radio(o):
            value, label = o
            is_checked = True if value == "1" else False
            return FormLabel(
                Radio(
                    id=f"rating-{current_page}",
                    value=value,
                    checked=is_checked,
                    cls="toggleable-radio",
                ),
                Span(label),
                cls="space-x-2",
            )

        return Tr(
            Td(P(current_page)),
            Td(pages[current_page].description),
            Td(pages[current_page].start),
            Td(
                Div(
                    *map(_render_radio, RATING_MAP.items()),
                    cls=(FlexT.block, FlexT.row, FlexT.wrap, "gap-x-6 gap-y-4"),
                )
            ),
        )

    table = Table(
        Thead(Tr(Th("No"), Th("Page"), Th("Start"), Th("Rating"))),
        Tbody(*[_render_row(i) for i in range(page, last_page)]),
    )

    action_buttons = Div(
        Button(
            "Save",
            cls=ButtonT.primary,
        ),
        A(Button("Cancel", type="button", cls=ButtonT.secondary), href=index),
        cls=(FlexT.block, FlexT.around, FlexT.middle, "w-full"),
    )

    # TODO: Later handle the user selection by session, for now temporarily setting it to siraj
    try:
        user_id = users(where="name='Siraj'")[0].id
    except IndexError:
        user_id = 1

    try:
        last_added_record = revisions()[-1]
    except IndexError:
        defalut_mode_value = 1
        defalut_plan_value = None
    else:
        defalut_mode_value = last_added_record.mode_id
        defalut_plan_value = last_added_record.plan_id

    return main_area(
        H1(
            f"{page} - {pages[page].description} => {last_page - 1} - {pages[last_page - 1].description}"
        ),
        Form(
            Hidden(id="user_id", value=user_id),
            Hidden(name="length", value=length),
            Grid(
                mode_dropdown(default_mode=(mode_id or defalut_mode_value)),
                LabelInput(
                    "Plan ID",
                    name="plan_id",
                    type="number",
                    value=(plan_id or defalut_plan_value),
                ),
            ),
            LabelInput(
                "Revision Date",
                name="revision_date",
                type="date",
                value=(revision_date or current_time("%Y-%m-%d")),
            ),
            Div(table, cls="uk-overflow-auto"),
            action_buttons,
            action="/revision/bulk_add",
            method="POST",
        ),
        Script(src="/script.js"),
        active="Revision",
    )


@rt("/revision/bulk_add")
async def post(
    user_id: int,
    revision_date: str,
    mode_id: int,
    plan_id: int,
    length: int,
    req,
):
    form_data = await req.form()

    parsed_data = [
        Revision(
            page_id=int(page.split("-")[1]),
            rating=int(rating),
            user_id=user_id,
            revision_date=revision_date,
            mode_id=mode_id,
            plan_id=plan_id,
        )
        for page, rating in form_data.items()
        if page.startswith("rating-")
    ]
    revisions.insert_all(parsed_data)
    if parsed_data:
        last_page = parsed_data[-1].page_id
        # To show the next page
        next_page = last_page + 1
    else:
        return Redirect(index)

    return Redirect(
        f"/revision/bulk_add?page={next_page}&revision_date={revision_date}&length={length}&mode_id={mode_id}&plan_id={plan_id}"
    )


@app.get
def import_csv():
    form = Form(
        UploadZone(
            DivCentered(Span("Upload Zone"), UkIcon("upload")),
            id="file",
            accept="text/csv",
        ),
        Button("Submit"),
        action=import_csv,
        method="POST",
    )
    return main_area(Titled("Upload CSV", form), active="Revision")


@app.post
async def import_csv(file: UploadFile):
    backup_sqlite_db(DB_PATH, "data/backup")
    file_content = await file.read()
    revisions.delete_where()  # Truncate the table before importing
    db.import_file("revisions", file_content)
    return Redirect(revision)


@app.get
def export_csv():
    df = pd.DataFrame(revisions())

    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    file_name = f"Quran_SRS_data_{current_time("%Y%m%d%I%M")}"
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={file_name}.csv"},
    )


@app.get
def backup():
    if not os.path.exists(DB_PATH):
        return Titled("Error", P("Database file not found"))

    backup_path = backup_sqlite_db(DB_PATH, "data/backup")

    return FileResponse(backup_path, filename="quran_backup.db")


@app.get
def import_db():
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
        action=import_db,
        method="POST",
    )
    return main_area(
        Div(
            Div(H2("Current DBs"), Ul(*current_dbs)),
            Div(H1("Upload DB"), form),
            cls="space-y-6",
        ),
        active="Revision",
    )


@app.post
async def import_db(file: UploadFile):
    path = "data/" + file.filename
    if DB_PATH == path:
        return Titled("Error", P("Cannot overwrite the current DB"))

    file_content = await file.read()
    with open(path, "wb") as f:
        f.write(file_content)

    return RedirectResponse(index)


serve()
