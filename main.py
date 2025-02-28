from fasthtml.common import *
from utils import standardize_column, convert_time, current_time

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


@dataclass
class Login:
    email: str
    password: str


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

# Session will expire after 7 days
app, rt = fast_app(live=True, before=bware, max_age=7 * 24 * 3600)
setup_toasts(app)


column_headers = ["Select", "Page", "Revision Time", "Rating", "Created By", "Action"]

# To exclude the select and action buttons
column_standardized = list(map(standardize_column, column_headers))[1:-1]


def get_first_unique_page(sort_by, sort_type) -> list:
    unique_pages = set()
    result = []
    for r in revisions(order_by="revision_time DESC"):
        if r.page not in unique_pages:
            unique_pages.add(r.page)
            result.append(r.__dict__)
    return sorted(result, key=lambda d: d[sort_by], reverse=(sort_type == "DESC"))


def edit_btn(disable=True, oob=False):
    return Button(
        "Edit",
        hx_post=edit,
        hx_include="[name='revision_id']",
        hx_target="body",
        hx_swap="outerHTML",
        hx_push_url="true",
        id="editButton",
        cls="secondary",
        disabled=disable,
        **({"hx_swap_oob": "true"} if oob else {}),
    )


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
    rev_dict = revision if isinstance(revision, dict) else vars(revision)
    id = rev_dict["id"]
    rid = f"r-{id}"

    return Tr(
        Td(radio_btn(id)),
        *[Td(rev_dict[c]) for c in column_standardized],
        Td(
            Button(
                "Delete",
                hx_delete=delete_row.to(id=id),
                target_id=f"row-{id}",
                hx_swap="outerHTML",
                cls="secondary",
                style="padding:3px 4px; font-size: 0.8rem;",
            )
        ),
        hx_get=select.to(id=id),
        target_id=rid,
        hx_swap="outerHTML",
        id=f"row-{id}",
    )


def add_pagination(limit, filter, times=1, sort_by="revision_time", sort_type=""):
    table_data = (
        get_first_unique_page(sort_by, sort_type)
        if filter
        else revisions(order_by=f"{sort_by} {sort_type}")
    )

    upper_limit = limit * times
    lower_limit = upper_limit - limit

    prev_btn = Button(
        "Previous",
        cls="contrast",
        hx_get=refresh_revison_table.to(times=times - 1, filter=filter),
        target_id="tableArea",
        hx_swap="outerHTML",
        **({"disabled": True} if times == 1 else {}),
    )
    next_btn = Button(
        "Next",
        cls="contrast",
        style="float: right;",
        hx_get=refresh_revison_table.to(times=times + 1, filter=filter),
        target_id="tableArea",
        hx_swap="outerHTML",
        **({"disabled": True} if upper_limit >= len(table_data) else {}),
    )
    action_buttons = Grid(prev_btn, next_btn)

    icon = {"ASC": "▲", "DESC": "▼", "": ""}

    def _column_header_render(col_name):
        column_standardized = standardize_column(col_name)
        if col_name in ["Select", "Action"]:
            return Th(col_name)

        return Th(
            col_name,
            (icon[sort_type] if column_standardized == sort_by else ""),
            hx_get=sort_revision_table.to(
                times=times,
                filter=filter,
                sort_by=column_standardized,
            ),
            target_id="paginationArea",
            hx_swap="outerHTML",
            style="cursor: pointer;",
        )

    return Div(
        Table(
            Thead(Tr(*map(_column_header_render, column_headers))),
            Tbody(
                *map(
                    render_revision_row,
                    # Reverse the list to get the (last edited / oldest) first unless there is no sorting
                    (
                        table_data[::-1][lower_limit:upper_limit]
                        if sort_type == ""
                        else table_data[lower_limit:upper_limit]
                    ),
                )
            ),
        ),
        action_buttons,
        id="paginationArea",
    )


def dropdown(table_link, row_limit=5):
    def _option(x):
        return Option(x, value=x, **({"selected": True} if x == row_limit else {}))

    return Select(
        *(_option(x) for x in ROW_OPTIONS),
        name="row",
        style="width: 100px;float: right;",
        hx_trigger="change",
        hx_post=table_link,
        target_id="tableArea",
        hx_swap="outerHTML",
    )


def revision_table(limit=5, times=1, filter=False, **kwargs):

    new_btn = Button(
        "New",
        hx_get=add_revision,
        hx_target="body",
        hx_swap="outerHTML",
        hx_push_url="true",
    )

    actions = Div(
        new_btn,
        " ",
        edit_btn(),
        " ",
        dropdown(refresh_revison_table, limit),
        Hidden(name="filter", value=str(filter)),
    )
    table = add_pagination(
        limit=limit,
        times=times,
        filter=filter,
        **kwargs,
    )
    return Div(actions, table, cls="overflow-auto", id="tableArea")


def input_form(action: str):
    def _radio(name: str):
        return Label(
            Input(
                type="radio",
                name="rating",
                value=name,
                checked=(name.startswith("Good")),
            ),
            name,
        )

    ratings = ["Good ✅", "Ok 😄", "Bad ❌"]
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
        Label("Rating"),
        *map(_radio, ratings),
        Div(
            Button(action.capitalize()),
            " ",
            A(
                Button("Discard", type="button"),
                href="javascript:window.history.back();",
            ),
            style="margin-top: 1rem;",
        ),
        action=f"/{action}",
        method="POST",
    )


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
            Ul(Li(H3(title))),
            Ul(navigation),
        ),
        Hr(style="margin-top:0;"),
    )


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


@rt
def index(auth, sess):
    if "sort" in sess:
        del sess["sort"]
    row_limit = sess.get("row", 5)
    title = "Quran SRS Home"
    top = navbar(auth, title)
    form = revision_table(limit=row_limit, filter=True)
    return Title(title), Container(top, form)


@rt
def revision(auth, sess):
    if "sort" in sess:
        del sess["sort"]
    row_limit = sess.get("row", 5)
    title = "Quran SRS Revision"
    form = revision_table(row_limit)
    return Title(title), Container(navbar(auth, title, active="Revision"), form)


@app.post
def refresh_revison_table(filter: bool, row: int, sess):
    current_sort = sess.get("sort", {})
    sess["row"] = row
    return revision_table(limit=row, filter=filter, **current_sort)


@app.get
def refresh_revison_table(filter: bool, times: int, sess):
    current_sort = sess.get("sort", {})
    row = sess.get("row", 5)
    return revision_table(limit=row, times=times, filter=filter, **current_sort)


sort_type_mapping = {"": "ASC", "ASC": "DESC", "DESC": ""}


@rt
def sort_revision_table(filter: bool, sort_by: str, sess):
    row_limit = sess.get("row", 5)
    current_sort = sess.get("sort", {"sort_by": "", "sort_type": ""})

    if current_sort["sort_by"] == sort_by:
        current_sort["sort_type"] = sort_type_mapping[current_sort["sort_type"]]
    else:
        current_sort = {"sort_by": sort_by, "sort_type": "ASC"}

    if current_sort["sort_type"]:
        sess["sort"] = current_sort
    else:
        del sess["sort"]
        # Reset the current sort to use the default
        current_sort = {}

    return add_pagination(limit=row_limit, filter=filter, **current_sort)


@rt
def select(id: int):
    return (
        radio_btn(id, True, hx_swap_oob="true"),
        edit_btn(disable=False, oob=True),
    )


@app.post
def update(auth, revision: Revision):
    # Clean up the revision_time
    revision.revision_time = convert_time(revision.revision_time)
    revision.last_modified_at = current_time()
    revision.last_modified_by = auth
    revisions.update(revision)
    return revision_redir


@app.post
def edit(revision_id: int):
    return RedirectResponse(f"/edit?id={revision_id}", status_code=303)


@app.get
def edit(id: int):
    revision = revisions[id]
    # convert the time to correct format for the form
    revision.revision_time = convert_time(revision.revision_time, reverse=True)
    form = input_form(action="update")
    return Titled("Edit", fill_form(form, revision))


@app.delete
def delete_row(id: int):
    revisions.delete(id)
    return edit_btn(oob=True)


@app.get
def add_revision():
    return Titled("Add Revision", input_form(action="create"))


@app.post
def create(auth, revision: Revision):
    revision.revision_time = convert_time(revision.revision_time)
    revision.created_at = revision.last_modified_at = current_time()
    revision.created_by = revision.last_modified_by = auth
    revisions.insert(revision)
    return revision_redir


serve()
