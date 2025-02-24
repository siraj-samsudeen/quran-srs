from fasthtml.common import *
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


@rt
def index():
    return Titled(
        "Quran SRS Home",
        Div("Fresh start with FastHTML"),
        Div("Nav: ", A("Revision", href=revision)),
    )


@rt
def revision():
    edit_btn = Button(
        "Edit", hx_post=edit, hx_target="body", hx_swap="outerHTML", hx_push_url="true"
    )
    actions = Div(edit_btn)
    table = Table(
        Thead(Tr(*map(Th, column_headers))),
        Tbody(*map(render_revision_row, revisions())),
    )
    form = Form(actions, table)
    return Titled("Quran SRS Revision", form)


@rt
def select(id: int):
    return radio_btn(id, True)


@app.post
def edit(revision_id: int):
    return RedirectResponse(f"/edit?id={revision_id}", status_code=303)


@app.get
def edit(id: int):
    form = Form(
        Hidden(name="id"),
        Label("Page", Input(type="number", name="page")),
        Label("Date", Input(type="datetime-local", name="revision_time")),
        Label(
            "Rating",
            Select(
                Option("Good", value="Good"),
                Option("Ok", value="Ok"),
                Option("Bad", value="Bad"),
                name="rating",
            ),
        ),
        Button("Update"),
        action=update,
        method="POST",
    )
    return Titled("Edit", fill_form(form, revisions[id]))


@app.post
def update(revision: Revision):
    # Clean up the revision_time
    revision.revision_time = revision.revision_time.replace("T", " ")
    revisions.update(revision)
    return RedirectResponse("/revision", status_code=303)


serve()
