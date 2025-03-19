from fasthtml.common import *
from monsterui.all import *
from utils import *
import pandas as pd
from io import BytesIO

RATING_MAP = {"1": "✅ Good", "0": "😄 Ok", "-1": "❌ Bad"}

# Quran metadata
q = pd.read_csv("metadata/quran_metadata.csv")
q["page description"] = q["page description"].fillna(q["surah"])
q["page description"] = q["page description"].str.replace(".", "")
# If the page description starts with J, then it is a Juz
q["page description"] = q["page description"].where(
    q["page description"].str.startswith("J"), "S" + q["page description"]
)
quran_data = q.fillna("").to_dict(orient="records")


db = database("data/quran.db")

revisions, users = db.t.revisions, db.t.users
if revisions not in db.t:
    users.create(id=int, name=str, email=str, password=str, pk="id")
    revisions.create(
        id=int,
        user_id=int,
        page=int,
        revision_date=str,
        rating=int,
        pk="id",
    )
Revision, User = revisions.dataclass(), users.dataclass()

app, rt = fast_app(hdrs=Theme.blue.headers())


def get_quran_data(page: int) -> dict:
    current_page_quran_data = [d for d in quran_data if d["page"] == page]
    return current_page_quran_data[0] if current_page_quran_data else {}


def action_buttons(last_added_page, source="Home"):

    if isinstance(last_added_page, int):
        last_added_page += 1
    entry_buttons = Form(
        DivLAligned(
            Input(
                type="text",
                placeholder="page",
                cls="max-w-20",
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
    import_export_buttons = DivLAligned(
        # A(Button("Import"), href=import_csv),
        A(Button("Export"), href=export_csv),
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
def index(sess):
    last_added_page = sess.get("last_added_page", None)

    def split_page_range(page_range: str):
        start_page, end_page = (
            page_range.split("-") if "-" in page_range else [page_range, None]
        )
        start_page = int(start_page)
        end_page = int(end_page) if end_page else None
        return start_page, end_page

    def render_page(page):
        page_data = get_quran_data(page)
        page_description = page_data.get("page description", "")
        return Span(Span(page, cls=TextPresets.bold_sm), f" - {page_description}")

    ################### Datewise summary ###################
    qry = f"select distinct revision_date from {revisions}"
    unique_dates = db.q(qry)
    unique_dates = sorted([d["revision_date"] for d in unique_dates], reverse=True)

    def _render_datewise_row(date):
        pages = revisions(where=f"revision_date = '{date}'")
        pages = sorted([p.page for p in pages])

        def _render_page_range(page_range: str):
            start_page, end_page = split_page_range(page_range)
            if end_page:
                return P(
                    render_page(start_page),
                    Span(" -> "),
                    render_page(end_page),
                )
            else:
                return P(render_page(start_page))

        return Tr(
            Td(date_to_human_readable(date)),
            Td(len(pages)),
            Td(*map(_render_page_range, compact_format(pages).split(", "))),
        )

    datewise_table = Div(
        # H1("Datewise summary"),
        Table(
            Thead(Tr(Th("Date"), Th("Count"), Th("Page Range"))),
            Tbody(*map(_render_datewise_row, unique_dates)),
        ),
        cls="uk-overflow-auto",
    )

    ################### Overall summary ###################
    all_pages = sorted([p.page for p in revisions()])

    def render_overall_row(page_range: str):
        if not page_range:
            return None

        start_page, end_page = split_page_range(page_range)
        next_page = (end_page or start_page) + 1

        return Tr(
            Td(page_range),
            Td(render_page(start_page)),
            (Td(render_page(end_page) if end_page else None)),
            Td(
                A(
                    render_page(next_page),
                    href=f"revision/bulk_add?page={next_page}",
                    cls=AT.classic,
                )
            ),
        )

    overall_table = Div(
        # H1("Overall summary"),
        Table(
            Thead(
                Tr(
                    Th("Page Range"),
                    Th("Start Page"),
                    Th("End Page"),
                    Th("Continue From"),
                )
            ),
            Tbody(*map(render_overall_row, compact_format(all_pages).split(", "))),
        ),
        cls="uk-overflow-auto",
    )

    return main_area(
        action_buttons(last_added_page),
        Div(overall_table, Divider(), datewise_table),
        active="Home",
    )


@rt
def user():
    def _render_user(user):
        return Tr(
            Td(user.id),
            Td(A(user.name, href=f"/user/edit/{user.id}", cls=AT.muted)),
            Td(user.email),
            Td(user.password),
            Td(
                A(
                    "Delete",
                    hx_delete=f"/user/delete/{user.id}",
                    target_id=f"user-{user.id}",
                    hx_swap="outerHTML",
                    hx_confirm="Are you sure?",
                    cls=AT.muted,
                ),
            ),
            id=f"user-{user.id}",
        )

    table = Table(
        Thead(Tr(Th("Id"), Th("Name"), Th("Email"), Th("Password"), Th("Action"))),
        Tbody(*map(_render_user, users())),
    )
    return main_area(
        A(Button("Add", type="button", cls=ButtonT.link), href="/user/add"),
        Div(table, cls="uk-overflow-auto"),
        active="User",
    )


def create_user_form(type):
    return Form(
        Hidden(name="id"),
        LabelInput("Name"),
        LabelInput("Email"),
        LabelInput("Password"),
        DivFullySpaced(Button("Save"), A(Button("Discard", type="button"), href=user)),
        method="POST",
        action=f"/user/{type}",
    )


@rt("/user/edit/{user_id}")
def get(user_id: int):
    current_user = users[user_id]
    form = create_user_form("edit")
    return main_area(Titled("Edit User", fill_form(form, current_user)), active="User")


@rt("/user/edit")
def post(user_details: User):
    users.update(user_details)
    return Redirect(user)


@rt("/user/delete/{user_id}")
def delete(user_id: int):
    users.delete(user_id)


@rt("/user/add")
def get():
    return main_area(Titled("Add User", create_user_form("add")), active="User")


@rt("/user/add")
def post(user_details: User):
    del user_details.id
    users.insert(user_details)
    return Redirect(user)


@rt
def revision(sess):
    last_added_page = sess.get("last_added_page", None)

    def _render_revision(rev):
        current_page_quran_data = get_quran_data(rev.page)

        return Tr(
            # Td(rev.id),
            # Td(rev.user_id),
            Td(A(rev.page, href=f"/revision/edit/{rev.id}", cls=AT.muted)),
            Td(RATING_MAP.get(str(rev.rating))),
            Td(current_page_quran_data.get("surah", "-")),
            Td(current_page_quran_data.get("juz", "-")),
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
                Th("Page"),
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
        action_buttons(last_added_page, source="Revision"),
        Div(table, cls="uk-overflow-auto"),
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
        LabelInput(
            "Revision Date",
            name="revision_date",
            type="date",
            value=current_time("%Y-%m-%d"),
        ),
        LabelInput("Page", type="number", input_cls="text-2xl"),
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


# This route is used to redirect to the appropriate revision entry form
@rt("/revision/entry")
def post(type: str, page: int):
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

    page_desc = get_quran_data(page).get("page description", "-")
    return main_area(
        Titled(
            f"{page} - {page_desc}",
            fill_form(create_revision_form("add"), {"page": page}),
        ),
        active="Revision",
    )


@rt("/revision/add")
def post(revision_details: Revision, sess):
    # The id is set to zero in the form, so we need to delete it
    # before inserting to generate the id automatically
    del revision_details.id
    revisions.insert(revision_details)

    page = revision_details.page
    sess["last_added_page"] = page

    return Redirect(f"/revision/add?page={page + 1}")


@app.get("/revision/bulk_add")
def get(page: str, revision_date: str = None, length: int = 5, max_page: int = 605):

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

        current_page_quran_data = get_quran_data(current_page)
        return Tr(
            Td(P(current_page)),
            Td(current_page_quran_data.get("page description", "-")),
            Td(
                Div(
                    *map(_render_radio, RATING_MAP.items()),
                    cls=(FlexT.block, FlexT.row, FlexT.wrap, "gap-x-6 gap-y-4"),
                )
            ),
        )

    table = Table(
        Thead(Tr(Th("No"), Th("Page"), Th("Rating"))),
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

    start_page_desc = get_quran_data(page).get("page description", "-")
    last_page_desc = get_quran_data(last_page - 1).get("page description", "-")
    return main_area(
        H1(f"{page} - {start_page_desc} => {last_page - 1} - {last_page_desc}"),
        Form(
            Hidden(id="user_id", value=user_id),
            Hidden(name="last_page", value=last_page),
            Hidden(name="length", value=length),
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
    user_id: int, revision_date: str, last_page: int, length: int, sess, req
):
    form_data = await req.form()

    parsed_data = [
        Revision(
            page=int(page.split("-")[1]),
            rating=int(rating),
            user_id=user_id,
            revision_date=revision_date,
        )
        for page, rating in form_data.items()
        if page.startswith("rating-")
    ]
    revisions.insert_all(parsed_data)

    if len(parsed_data) > 0:
        sess["last_added_page"] = last_page = parsed_data[-1].page
        # To show the next page
        last_page += 1

    return Redirect(
        f"/revision/bulk_add?page={last_page}&revision_date={revision_date}&length={length}"
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
    db_path = "data/quran.db"  # This should match your database path

    if not os.path.exists(db_path):
        return Titled("Error", P("Database file not found"))

    return FileResponse(db_path, filename="quran_backup.db")


serve()
