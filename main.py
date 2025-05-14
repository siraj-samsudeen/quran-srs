from fasthtml.common import *
from monsterui.all import *
from utils import *
import pandas as pd
from io import BytesIO

RATING_MAP = {"1": "✅ Good", "0": "😄 Ok", "-1": "❌ Bad"}
DB_PATH = "data/quran_v3.db"

db = database(DB_PATH)
tables = db.t
revisions, hafizs, users, hafizs_users = (
    tables.revisions,
    tables.hafizs,
    tables.users,
    tables.hafizs_users,
)
plans, modes, pages = tables.plans, tables.modes, tables.pages
if modes not in tables:
    modes.create(id=int, name=str, description=str, pk="id")
    modes_data = pd.read_csv("metadata/modes.csv").to_dict("records")
    modes.insert_all(modes_data)
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
        # foreign_key, reference_table, reference_column
        foreign_keys=[("mode_id", "modes", "id")],
    )
if pages not in tables:
    pages.create(
        id=int, page=int, juz=str, surah=str, description=str, start=str, pk="id"
    )
    pages_data = pd.read_csv("metadata/pages.csv").to_dict("records")
    pages.insert_all(pages_data)
if hafizs not in tables:
    hafizs.create(id=int, name=str, age_group=str, daily_capacity=int, pk="id")
    # FIXME: Add Siraj as a hafizs in order to select the hafiz_id when creating a new revision
    # as it was currently not handled by session
    hafizs.insert({"name": "Siraj"})
    hafizs.insert({"name": "Firoza"})
if users not in tables:
    users.create(id=int, name=str, email=str, password=str, role=str, pk="id")
    users.insert({"name": "Siraj", "email": "siraj@bisquared.com", "password": "123"})
    users.insert({"name": "Firoza", "email": "firoza@bisquared.com", "password": "123"})
if hafizs_users not in tables:
    hafizs_users.create(
        id=int,
        user_id=int,
        hafiz_id=int,
        relationship=str,
        granted_by_user_id=int,
        granted_at=str,
        pk="id",
        foreign_keys=[("user_id", "users", "id"), ("hafiz_id", "hafizs", "id")],
    )
    hafizs_users.insert({"user_id": 1, "hafiz_id": 1, "relationship": "self"})
    hafizs_users.insert({"user_id": 2, "hafiz_id": 2, "relationship": "self"})
if revisions not in tables:
    revisions.create(
        id=int,
        mode_id=int,
        plan_id=int,
        hafiz_id=int,
        page_id=int,
        revision_date=str,
        rating=int,
        pk="id",
        foreign_keys=[
            ("mode_id", "modes", "id"),
            ("hafiz_id", "hafizs", "id"),
            ("page_id", "pages", "id"),
        ],
    )
Revision, Hafiz, User, Users_hafiz = (
    revisions.dataclass(),
    hafizs.dataclass(),
    users.dataclass(),
    hafizs_users.dataclass(),
)
Plan, Mode, Page = plans.dataclass(), modes.dataclass(), pages.dataclass()

hyperscript_header = Script(src="https://unpkg.com/hyperscript.org@0.9.14")
alpinejs_header = Script(
    src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js", defer=True
)


def before(req, sess):
    user_auth = req.scope["user_auth"] = sess.get("user_auth", None)
    if not user_auth:
        return RedirectResponse("/login", status_code=303)
    auth = req.scope["auth"] = sess.get("auth", None)
    if not auth:
        return RedirectResponse("/hafiz_selection", status_code=303)
    revisions.xtra(hafiz_id=auth)


bware = Beforeware(before, skip=["/hafiz_selection", "/login", "/logout", "/add_hafiz"])

app, rt = fast_app(
    before=bware,
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
        select_kwargs={"name": "mode_id"},
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
                required=True,
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


def split_page_range(page_range: str):
    start_page, end_page = (
        page_range.split("-") if "-" in page_range else [page_range, None]
    )
    start_page = int(start_page)
    end_page = int(end_page) if end_page else None
    return start_page, end_page


def render_page(page):
    page_data = pages[page]
    return Span(
        Span(page, cls=TextPresets.bold_sm),
        f" - {page_data.description or page_data.surah}",
    )


def datewise_summary_table(show=None, hafiz_id=None):
    qry = f"SELECT MIN(revision_date) AS earliest_date FROM {revisions}"
    qry = (qry + f" WHERE hafiz_id = {hafiz_id}") if hafiz_id else qry
    result = db.q(qry)
    earliest_date = result[0]["earliest_date"]
    current_date = current_time("%Y-%m-%d")

    date_range = pd.date_range(
        start=(earliest_date or current_date), end=current_date, freq="D"
    )
    date_range = [date.strftime("%Y-%m-%d") for date in date_range][::-1]
    date_range = date_range[:show] if show else date_range

    def _render_datewise_row(date):
        rev_query = f"revision_date = '{date}'"
        revisions_query = revisions(
            where=(rev_query + f"AND hafiz_id = {hafiz_id}" if hafiz_id else rev_query)
        )
        current_date_revisions = [r.__dict__ for r in revisions_query]
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
    return datewise_table


def render_hafiz_card(hafizs_user, auth):
    is_current_hafizs_user = auth != hafizs_user.hafiz_id
    return Card(
        (
            Subtitle("last 3 revision")(
                datewise_summary_table(show=3, hafiz_id=hafizs_user.hafiz_id)
            ),
        ),
        header=DivFullySpaced(H3(hafizs[hafizs_user.hafiz_id].name)),
        footer=Button(
            "Switch hafiz" if is_current_hafizs_user else "Go to home",
            name="current_hafiz_id",
            value=hafizs_user.hafiz_id,
            hx_post="/hafiz_selection",
            hx_target="body",
            hx_replace_url="true",
            cls=(ButtonT.primary if is_current_hafizs_user else ButtonT.secondary),
        ),
        cls="min-w-[300px] max-w-[400px]",
    )


login_redir = RedirectResponse("/login", status_code=303)


@app.get("/login")
def login():
    form = Form(
        LabelInput(label="Email", name="email", type="email"),
        LabelInput(label="Password", name="password", type="password"),
        Button("Login"),
        action="/login",
        method="post",
    )
    return Titled("Login", form)


@dataclass
class Login:
    email: str
    password: str


@app.post("/login")
def login_post(login: Login, sess):
    if not login.email or not login.password:
        return login_redir
    try:
        u = users(where="email = '{}'".format(login.email))[0]
    except IndexError:
        # u = users.insert(login)
        return login_redir
    if not compare_digest(u.password.encode("utf-8"), login.password.encode("utf-8")):
        return login_redir
    sess["user_auth"] = u.id
    hafizs_users.xtra(id=u.id)
    return RedirectResponse("/", status_code=303)


@app.get("/logout")
def logout(sess):
    user_auth = sess.get("user_auth", None)
    if user_auth is not None:
        del sess["user_auth"]
    auth = sess.get("auth", None)
    if auth is not None:
        del sess["auth"]
    return RedirectResponse("/login", status_code=303)


@app.post("/add_hafiz")
def add_hafiz_and_relations(hafiz: Hafiz, relationship: str, sess):
    hafiz_id = hafizs.insert(hafiz)
    hafizs_users.insert(
        hafiz_id=hafiz_id.id,
        user_id=sess["user_auth"],
        relationship=relationship,
        granted_by_user_id=sess["user_auth"],
        granted_at=datetime.now().strftime("%d-%m-%y %H:%M:%S"),
    )
    return RedirectResponse("/hafiz_selection", status_code=303)


@app.get("/hafiz_selection")
def hafiz_selection(sess):
    # In beforeware we are adding the hafiz_id filter using xtra
    # we have to reset that xtra attribute in order to show revisions for all hafiz
    revisions.xtra()
    hafizs_users.xtra()
    auth = sess.get("auth", None)
    user_auth = sess.get("user_auth", None)
    if user_auth is None:
        return login_redir

    # cards = [render_hafiz_card(h, auth) for h in hafizs()]
    cards = [
        render_hafiz_card(h, auth) for h in hafizs_users() if h.user_id == user_auth
    ]
    age_groups = ["child", "teen", "adult"]
    relationships = ["self", "parent", "teacher", "sibling"]

    def mk_options(option):
        return Option(
            option.capitalize(),
            value=option,
        )

    hafiz_form = Card(
        Titled(
            "Add Hafiz",
            Form(
                LabelInput(label="Hafiz Name", name="name", required=True),
                LabelSelect(
                    *map(mk_options, age_groups),
                    label="Age Group",
                    name="age_group",
                ),
                LabelInput(
                    label="Daily Capacity", name="daily_capacity", type="number"
                ),
                LabelSelect(
                    *map(mk_options, relationships),
                    label="Relationship",
                    name="relationship",
                ),
                Button("Add Hafiz"),
                action="/add_hafiz",
                method="post",
                cls="space-y-3",
            ),
        ),
        cls="w-[300px]",
    )
    return main_area(
        H5("Select Hafiz"),
        Div(*cards, cls=(FlexT.block, FlexT.wrap, "gap-4")),
        Div(hafiz_form),
        auth=auth,
    )


@app.post("/hafiz_selection")
def change_hafiz(current_hafiz_id: int, sess):
    sess["auth"] = current_hafiz_id
    return RedirectResponse("/", status_code=303)


def main_area(*args, active=None, auth=None):
    is_active = lambda x: AT.primary if x == active else None
    title = A("Quran SRS", href=index)
    hafiz_name = A(
        f"{hafizs[auth].name if auth is not None else "Select hafiz"}",
        href="/hafiz_selection",
        method="GET",
    )
    return Title("Quran SRS"), Container(
        Div(
            NavBar(
                A("Home", href=index, cls=is_active("Home")),
                A("Revision", href=revision, cls=is_active("Revision")),
                A("Tables", href="/tables", cls=is_active("Tables")),
                A("logout", href="/logout"),
                # A("User", href=user, cls=is_active("User")), # The user nav is temporarily disabled
                brand=H3(title, Span(" - "), hafiz_name),
            ),
            DividerLine(y_space=0),
            cls="bg-white sticky top-0 z-10",
        ),
        Main(*args, cls="p-4", id="main") if args else None,
        cls=ContainerT.xl,
    )


def tables_main_area(*args, active_table=None, auth=None):
    is_active = lambda x: "uk-active" if x == active_table else None

    tables_list = [t for t in str(tables).split(", ") if not t.startswith("sqlite")]
    table_links = [
        Li(A(t.capitalize(), href=f"/tables/{t}"), cls=is_active(t))
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


@rt
def index(auth):
    revision_data = revisions()
    last_added_page = revision_data[-1].page_id if revision_data else None
    # if it is greater than 604, we are reseting the last added page to None
    if isinstance(last_added_page, int) and last_added_page >= 604:
        last_added_page = None

    ################### Overall summary ###################
    # Sequential revision table
    seq_id = "1"
    qry = f"SELECT plan_id FROM {revisions} WHERE mode_id = {seq_id} ORDER BY revision_date DESC"
    result = db.q(qry)
    seq_plan_ids = [i["plan_id"] for i in result]
    # when using the `DISTINCT` keyword in the query the original order of the rows is not preserved
    # so we need to use the `dict.fromkeys` method to remove the duplicates which preserves the order
    unique_seq_plan_id = list(dict.fromkeys(seq_plan_ids))
    # To get the unique page ranges for the plan_id
    unique_page_ranges = []
    for plan_id in unique_seq_plan_id:
        if not plan_id:
            continue
        pages_list = sorted(
            [
                r.page_id
                for r in revisions(
                    where=f"mode_id = '{seq_id}' AND plan_id = '{plan_id}'"
                )
            ]
        )
        for p in compact_format(pages_list).split(", "):
            unique_page_ranges.append({"plan_id": plan_id, "page_range": p})

    def render_overall_row(o: dict):
        plan_id, page_range = o["plan_id"], o["page_range"]
        if not page_range:
            return None

        start_page, end_page = split_page_range(page_range)
        next_page = (end_page or start_page) + 1

        current_plan = plans(where=f"id = '{plan_id}' AND mode_id = '{seq_id}'")
        if current_plan:
            is_completed = current_plan[0].completed
        else:
            is_completed = False

        if is_completed:
            continue_message = "Completed"
        elif next_page > 604:
            continue_message = "No further page"
        else:
            continue_message = A(
                render_page(next_page),
                href=f"revision/bulk_add?page={next_page}&mode_id={seq_id}&plan_id={plan_id}&hide_id_fields=true",
                cls=AT.classic,
            )

        return Tr(
            Td(A(plan_id, href=f"/tables/plans/{plan_id}/edit", cls=AT.muted)),
            Td(page_range),
            Td(render_page(start_page)),
            (Td(render_page(end_page) if end_page else None)),
            Td(continue_message),
        )

    overall_table = Div(
        H4("Sequential Revision Round"),
        Table(
            Thead(
                Tr(
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
        Div(overall_table, Divider(), datewise_summary_table()),
        active="Home",
        auth=auth,
    )


@app.get("/tables")
def list_tables(auth):
    return tables_main_area(auth=auth)


@app.get("/tables/{table}")
def view_table(table: str, auth):
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
    return tables_main_area(
        Div(
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
        active_table=table,
        auth=auth,
    )


def create_dynamic_input_form(schema: dict, **kwargs):
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
def edit_record_view(table: str, record_id: int, auth):
    current_table = tables[table]
    current_data = current_table[record_id]

    # The completed column is stored in int and it is considered as bool
    # so we are converting it to str in order to select the right radio button using fill_form
    if table == "plans":
        current_data.completed = str(current_data.completed)

    column_with_types = get_column_and_its_type(table)
    form = create_dynamic_input_form(
        column_with_types, hx_put=f"/tables/{table}/{record_id}"
    )

    return tables_main_area(
        Titled(f"Edit page", fill_form(form, current_data)),
        active_table=table,
        auth=auth,
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
def new_record_view(table: str, auth):
    column_with_types = get_column_and_its_type(table)
    return tables_main_area(
        Titled(
            f"Add page",
            create_dynamic_input_form(column_with_types, hx_post=f"/tables/{table}"),
        ),
        active_table=table,
        auth=auth,
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

    # file_name = f"{table}_{current_time("%Y%m%d%I%M")}"
    file_name = f"{table}.csv"
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )


@app.get("/tables/{table}/import")
def import_specific_table_view(table: str, auth):
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
                hx_post=f"/tables/{table}/import/preview",
                hx_include="#file",
                hx_encoding="multipart/form-data",
                target_id="preview_table",
                hx_push_url="false",
            ),
            Button("Cancel", type="button", onclick="history.back()"),
        ),
        action=f"/tables/{table}/import",
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


@app.post("/tables/{table}/import/preview")
async def import_specific_table_preview(table: str, file: UploadFile):
    file_content = await file.read()
    imported_df = pd.read_csv(BytesIO(file_content)).fillna("")
    columns = imported_df.columns.tolist()
    records = imported_df.to_dict(orient="records")

    # Check if the columns match the table's columns
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


# this function is used to create infinite scroll for the revisions table
def generate_revision_table_part(part_num: int = 1, size: int = 20) -> Tuple[Tr]:
    start = (part_num - 1) * size
    end = start + size
    data = revisions(order_by="id desc")[start:end]

    def _render_rows(rev: Revision):
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

    paginated = [_render_rows(i) for i in data]

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


@app.get
def revision(auth, idx: int | None = 1):
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
        Tbody(*generate_revision_table_part(part_num=idx)),
    )
    return main_area(
        # To send the selected revision ids for bulk delete and bulk edit
        Form(
            action_buttons(source="Revision"),
            Div(table, cls="uk-overflow-auto"),
        ),
        active="Revision",
        auth=auth,
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
            *map(_option, hafizs()), label="hafiz Id", name="hafiz_id", cls="hidden"
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
def get(revision_id: int, auth):
    current_revision = revisions[revision_id]
    # Convert rating to string in order to make the fill_form to select the option.
    current_revision.rating = str(current_revision.rating)
    form = create_revision_form("edit")
    return main_area(
        Titled("Edit Revision", fill_form(form, current_revision)),
        active="Revision",
        auth=auth,
    )


@rt("/revision/edit")
def post(revision_details: Revision):
    # setting the plan_id to None if it is 0
    # as it get defaults to 0 if the field is empty.
    revision_details.plan_id = set_zero_to_none(revision_details.plan_id)
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
def bulk_edit_view(ids: str, auth):
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
        auth=auth,
    )


@app.post("/revision")
async def bulk_edit_save(revision_date: str, mode_id: int, plan_id: int, req):
    plan_id = set_zero_to_none(plan_id)
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
def get(auth, page: str, max_page: int = 605, date: str = None):
    if "." in page:
        page = page.split(".")[0]

    page = int(page)

    if page >= max_page:
        return Redirect(index)

    try:
        last_added_record = revisions()[-1]
    except IndexError:
        defalut_mode_value = 1
        defalut_plan_value = None
    else:
        defalut_mode_value = last_added_record.mode_id
        defalut_plan_value = last_added_record.plan_id

    current_page_details = pages[page]
    return main_area(
        Titled(
            f"{page} - {current_page_details.description or current_page_details.surah} - {current_page_details.start}",
            fill_form(
                create_revision_form("add"),
                {
                    "page_id": page,
                    "mode_id": defalut_mode_value,
                    "plan_id": defalut_plan_value,
                    "revision_date": date,
                },
            ),
        ),
        active="Revision",
        auth=auth,
    )


@rt("/revision/add")
def post(revision_details: Revision):
    # The id is set to zero in the form, so we need to delete it
    # before inserting to generate the id automatically
    del revision_details.id
    revision_details.plan_id = set_zero_to_none(revision_details.plan_id)

    rev = revisions.insert(revision_details)

    return Redirect(f"/revision/add?page={rev.page_id + 1}&date={rev.revision_date}")


@app.get("/revision/bulk_add")
def get(
    auth,
    page: str,
    mode_id: int = None,
    plan_id: int = None,
    revision_date: str = None,
    length: int = 5,
    max_page: int = 605,
    hide_id_fields: bool = False,
):

    if "." in page:
        page, length = map(int, page.split("."))
    else:
        page = int(page)

    if page >= max_page:
        return Redirect(index)

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

        current_page_details = pages[current_page]
        return Tr(
            Td(P(current_page)),
            Td(current_page_details.description or current_page_details.surah),
            Td(P(current_page_details.start, cls=(TextT.xl))),
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

    try:
        last_added_record = revisions()[-1]
    except IndexError:
        defalut_mode_value = 1
        defalut_plan_value = None
    else:
        defalut_mode_value = last_added_record.mode_id
        defalut_plan_value = last_added_record.plan_id

    start_page_details = pages[page]
    end_page_details = pages[last_page - 1]

    start_description = start_page_details.description or start_page_details.surah
    end_description = end_page_details.description or end_page_details.surah
    return main_area(
        H1(f"{page} - {start_description} => {last_page - 1} - {end_description}"),
        Form(
            Hidden(name="length", value=length),
            Grid(
                mode_dropdown(default_mode=(mode_id or defalut_mode_value)),
                LabelInput(
                    "Plan ID",
                    name="plan_id",
                    type="number",
                    value=(plan_id or defalut_plan_value),
                ),
                # To hide the id fields on the when navigating through continue link
                **({"cls": "hidden"} if hide_id_fields else {}),
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
        Script(src="/public/script.js"),
        active="Revision",
        auth=auth,
    )


@rt("/revision/bulk_add")
async def post(
    revision_date: str,
    mode_id: int,
    plan_id: int,
    length: int,
    req,
):
    plan_id = set_zero_to_none(plan_id)
    form_data = await req.form()

    parsed_data = [
        Revision(
            page_id=int(page.split("-")[1]),
            rating=int(rating),
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
def import_csv(auth):
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
    return main_area(Titled("Upload CSV", form), active="Revision", auth=auth)


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
def import_db(auth):
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
        auth=auth,
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
