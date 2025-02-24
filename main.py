from fasthtml.common import *
from datetime import datetime
from utils import standardize_column

app, rt = fast_app(live=True)

db = database("data/quran.db")

revisions, users = db.t.revisions, db.t.users
if revisions not in db.t:
    users.create(user_id=int, name=str, email=str, password=str, pk="user_id")
    revisions.create(
        id=int,
        user_id=int,
        page=int,
        revision_time=str,
        rating=str,
        created_by=str,
        created_at=str,
        last_modified_by=str,
        last_modified_at=str,
        pk="id",
    )
Revision, User = revisions.dataclass(), users.dataclass()


column_headers = [
    "Select",
    "Page",
    "Revision Time",
    "Rating",
    "Created By",
    "Created At",
    "Last Modified By",
    "Last Modified At",
]

column_standardized = list(map(standardize_column, column_headers))[1:]


def radio_btn(id, state=False):
    return Input(
        type="radio",
        name="revision_id",
        value=id,
        id=f"r-{id}",
        hx_swap_oob="true",
        checked=state,
    )


def render_revision_row(revision):
    # Convert the revision object to a dictionary to easily access its attributes by column names
    rev_dict = vars(revision)
    id = rev_dict["id"]
    rid = f"r-{id}"

    return Tr(
        Td(radio_btn(id)),
        *[Td(rev_dict[c]) for c in column_standardized],
        hx_get=select.to(id=id),
        target_id=rid,
        hx_swap="outerHTML",
        id=f"row-{id}",
    )


def get_first_unique_page() -> list[dict]:
    unique_pages = set()
    result = []
    for r in revisions(order_by="revision_time DESC"):
        if r.page not in unique_pages:
            unique_pages.add(r.page)
            result.append(r.__dict__)
    # Reverse the list to get the oldest first
    return result[::-1]


@rt
def index():
    rows = [Tr(Td(r["page"]), Td(r["revision_time"])) for r in get_first_unique_page()]
    table = Table(Thead(Tr(Th("Page"), Th("Revision Time"))), Tbody(*rows))
    return Titled(
        "Quran SRS Home",
        Div("Fresh start with FastHTML"),
        Div("Nav: ", A("Revision", href=revision)),
        table,
    )


@rt
def revision():
    new_btn = Button(
        "New",
        hx_get=add_revision,
        hx_target="body",
        hx_swap="outerHTML",
        hx_push_url="true",
    )
    edit_btn = Button(
        "Edit", hx_post=edit, hx_target="body", hx_swap="outerHTML", hx_push_url="true"
    )
    delete_btn = Button("Delete", hx_post=delete_row, hx_swap="none")
    actions = Div(new_btn, " ", edit_btn, " ", delete_btn)
    table = Table(
        Thead(Tr(*map(Th, column_headers))),
        Tbody(*map(render_revision_row, revisions())),
    )
    form = Form(actions, table)
    return Titled("Quran SRS Revision", form)


@app.post
def delete_row(revision_id: int):
    revisions.delete(revision_id)
    return Tr(id=f"row-{revision_id}", hx_swap_oob="true")


@rt
def select(id: int):
    return radio_btn(id, True)


@app.post
def edit(revision_id: int):
    return RedirectResponse(f"/edit?id={revision_id}", status_code=303)


def input_form(action: str):
    return Form(
        Hidden(name="id") if action == "update" else None,
        Label("Page", Input(type="number", name="page")),
        Label(
            "Date",
            Input(
                type="datetime-local",
                name="revision_time",
                value=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            ),
        ),
        Label(
            "Rating",
            Select(
                Option("Good", value="Good"),
                Option("Ok", value="Ok"),
                Option("Bad", value="Bad"),
                name="rating",
            ),
        ),
        Button(action.capitalize()),
        action=f"/{action}",
        method="POST",
    )


@app.get
def edit(id: int):
    form = input_form(action="update")
    return Titled("Edit", fill_form(form, revisions[id]))


@app.post
def update(revision: Revision):
    # Clean up the revision_time
    revision.revision_time = revision.revision_time.replace("T", " ")
    revisions.update(revision)
    return RedirectResponse("/revision", status_code=303)


@rt
def add_revision():
    return Titled("Add Revision", input_form(action="create"))


@app.post
def create(revision: Revision):
    revision.revision_time = revision.revision_time.replace("T", " ")
    revision.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    revision.last_modified_at = revision.created_at
    # Temp user
    revision.created_by = "admin"
    revision.last_modified_by = "admin"
    revisions.insert(revision)
    return RedirectResponse("/revision", status_code=303)


serve()
