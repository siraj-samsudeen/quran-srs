from fasthtml.common import *
from datetime import datetime
from utils import standardize_column

ROW_OPTIONS = [5, 10, 15]

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


login_redir = RedirectResponse("/login", status_code=303)
home_redir = RedirectResponse("/", status_code=303)
revision_redir = RedirectResponse("/revision", status_code=303)


def before(req, sess):
    auth = req.scope["auth"] = sess.get("auth", None)
    id = sess.get("user_id", None)
    if not auth:
        return login_redir
    revisions.xtra(user_id=id)


bware = Beforeware(
    before, skip=[r"/favicon\.ico", r"/static/.*", r".*\.css", "/login", "/signup"]
)

app, rt = fast_app(live=True, before=bware)
setup_toasts(app)


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


def current_time(f="%Y-%m-%d %I:%M %p"):
    return datetime.now().strftime(f)


def convert_time(t, reverse=False):
    initial = "%Y-%m-%d"
    end = "%d %b %Y"
    if reverse:
        initial, end = end, initial
    try:
        return datetime.strptime(t, initial).strftime(end)
    except ValueError:
        return None


def radio_btn(id, state=False, **kwargs):
    return Input(
        type="radio",
        name="revision_id",
        value=id,
        id=f"r-{id}",
        checked=state,
        **kwargs,
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


@app.get
def signup():
    return Titled(
        "Sign up",
        P("Already have an account? ", A("login", href="/login")),
        Form(
            Input(name="name", placeholder="Name", required=True),
            Input(type="email", name="email", placeholder="Email", required=True),
            Input(
                type="password", name="password", placeholder="Password", required=True
            ),
            Button("sign up"),
            action=signup,
            method="POST",
        ),
    )


@app.post
def signup(user: User, sess):
    try:
        u = users(where=f"email = '{user.email}'")[0]
    except IndexError:
        u = users.insert(user)
    else:
        add_toast(sess, "This email is already registered", "info")
        return login_redir

    sess["auth"] = u.name
    sess["user_id"] = u.user_id
    return home_redir


@app.get
def login():
    return Titled(
        "Login",
        P("Don't have an account? ", A("sign up", href="/signup")),
        Form(
            Input(type="email", name="email", placeholder="Email", required=True),
            Input(
                type="password", name="password", placeholder="Password", required=True
            ),
            Button("login"),
            action=login,
            method="POST",
        ),
    )


@dataclass
class Login:
    email: str
    password: str


@app.post
def login(user: Login, sess):
    try:
        u = users(where=f"email = '{user.email}'")[0]
    except IndexError:
        add_toast(sess, "This email is not registered", "warning")
        return RedirectResponse("/signup", status_code=303)

    if not compare_digest(u.password.encode("utf-8"), user.password.encode("utf-8")):
        add_toast(sess, "Incorrect password", "error")
        return login_redir

    sess["auth"] = u.name
    sess["user_id"] = u.user_id
    return home_redir


@rt
def logout(sess):
    del sess["auth"]
    del sess["user_id"]
    return login_redir


def navbar(user, title, active="Home"):
    is_active = lambda x: None if x == active else "contrast"
    navigation = Nav(
        Ul(
            Li(A("Home", href="/", cls=is_active("Home"))),
            Li(A("Revision", href=revision, cls=is_active("Revision"))),
            Li(A("logout", href=logout, cls="secondary")),
        ),
        aria_label="breadcrumb",
        style="--pico-nav-breadcrumb-divider: '|';",
    )
    return (
        Nav(
            Ul(Li(P(Strong("User: "), user))),
            Ul(
                Li(
                    H3(title),
                    Span("Fresh start with FastHTML"),
                    style="text-align: center",
                )
            ),
            Ul(navigation),
        ),
        Hr(style="margin-top:0;"),
    )


@rt
def index(auth):
    form = Form(
        Group(
            Input(type="number", name="page", placeholder="Page", required=True),
            Button("Add"),
        ),
        hx_post=add_revision,
        hx_target="body",
        hx_swap="outerHTML",
        hx_push_url="true",
        style="max-width: 200px",
    )
    title = "Quran SRS Home"
    top = navbar(auth, title)
    rows = [Tr(Td(r["page"]), Td(r["revision_time"])) for r in get_first_unique_page()]
    table = Table(Thead(Tr(Th("Page"), Th("Last Revision Time"))), Tbody(*rows))
    return Title(title), Container(top, form, table)


edit_btn = lambda disable=True: Button(
    "Edit",
    hx_post=edit,
    hx_target="body",
    hx_swap="outerHTML",
    hx_push_url="true",
    id="editButton",
    cls="secondary",
    disabled=disable,
    hx_swap_oob="true",
)

delete_btn = lambda disable=True: Button(
    "Delete",
    hx_post=delete_row,
    hx_swap="none",
    id="deleteButton",
    cls="secondary",
    disabled=disable,
    hx_swap_oob="true",
)


def revision_table(limit=5, times=1):
    upper_limit = limit * times
    lower_limit = upper_limit - limit

    prev_btn = Button(
        "Previous",
        cls="contrast",
        hx_get=refresh_table.to(times=times - 1),
        target_id="revisionTable",
        hx_swap="outerHTML",
        **({"disabled": True} if times == 1 else {}),
    )
    next_btn = Button(
        "Next",
        cls="contrast",
        style="float: right;",
        hx_get=refresh_table.to(times=times + 1),
        target_id="revisionTable",
        hx_swap="outerHTML",
        **({"disabled": True} if upper_limit >= len(revisions()) else {}),
    )
    action_buttons = Grid(prev_btn, next_btn)
    return Div(
        Table(
            Thead(Tr(*map(Th, column_headers))),
            Tbody(
                *map(
                    render_revision_row,
                    # Reverse the list to get the last edited first
                    revisions(order_by="revision_time")[::-1][lower_limit:upper_limit],
                )
            ),
        ),
        action_buttons,
        id="revisionTable",
    )


@rt
def revision(auth, sess):
    row_limit = sess.get("row", 5)
    title = "Quran SRS Revision"
    new_btn = Button(
        "New",
        hx_get=add_revision,
        hx_target="body",
        hx_swap="outerHTML",
        hx_push_url="true",
    )

    def _option(x):
        return Option(x, value=x, **({"selected": True} if x == row_limit else {}))

    dropdown = Select(
        *(_option(x) for x in ROW_OPTIONS),
        name="row",
        style="width: 100px;float: right;",
        hx_trigger="change",
        hx_post=refresh_table,
        target_id="revisionTable",
        hx_swap="outerHTML",
    )
    actions = Div(new_btn, " ", edit_btn(), " ", delete_btn(), dropdown)
    table = revision_table(row_limit)
    form = Form(actions, table, cls="overflow-auto")
    return Title(title), Container(navbar(auth, title, active="Revision"), form)


@app.post
def refresh_table(row: int, sess):
    sess["row"] = row
    return revision_table(limit=row), edit_btn(), delete_btn()


@app.get
def refresh_table(times: int, sess):
    row = sess.get("row", 5)
    return revision_table(row, times=times), edit_btn(), delete_btn()


@app.post
def delete_row(revision_id: int):
    revisions.delete(revision_id)
    return (
        Tr(id=f"row-{revision_id}", hx_swap_oob="true"),
        edit_btn(),
        delete_btn(),
    )


@rt
def select(id: int):
    return (
        radio_btn(id, True, hx_swap_oob="true"),
        edit_btn(disable=False),
        delete_btn(disable=False),
    )


@app.post
def edit(revision_id: int):
    return RedirectResponse(f"/edit?id={revision_id}", status_code=303)


def input_form(action: str):
    return Form(
        Hidden(name="id") if action == "update" else None,
        Label("Page", Input(type="number", name="page", autofocus=True, required=True)),
        Label(
            "Date",
            Input(
                type="date",
                name="revision_time",
                value=current_time("%Y-%m-%d"),
                required=True,
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
        " ",
        A(Button("Discard", type="button"), href="javascript:window.history.back();"),
        action=f"/{action}",
        method="POST",
    )


@app.get
def edit(id: int):
    revision = revisions[id]
    # convert the time to correct format for the form
    revision.revision_time = convert_time(revision.revision_time, reverse=True)
    form = input_form(action="update")
    return Titled("Edit", fill_form(form, revision))


@app.post
def update(auth, revision: Revision):
    # Clean up the revision_time
    revision.revision_time = convert_time(revision.revision_time)
    revision.last_modified_at = current_time()
    revision.last_modified_by = auth
    revisions.update(revision)
    return revision_redir


@app.get
def add_revision():
    return Titled("Add Revision", input_form(action="create"))


@app.post
def add_revision(revision: Revision):
    form = input_form(action="create")
    return Titled("Add Revision", fill_form(form, revision))


@app.post
def create(auth, revision: Revision):
    revision.revision_time = convert_time(revision.revision_time)
    revision.created_at = revision.last_modified_at = current_time()
    revision.created_by = revision.last_modified_by = auth
    revisions.insert(revision)
    return revision_redir


serve()
