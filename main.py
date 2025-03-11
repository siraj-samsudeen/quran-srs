from fasthtml.common import *
from monsterui.all import *
from utils import *
import pandas as pd
from io import BytesIO

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


def side_nav(active=None):
    is_active = lambda x: "uk-active" if x == active else None
    table_links = [
        Li(A("User", href=user), cls=is_active("User")),
        Li(A("Revision", href=revision), cls=is_active("Revision")),
    ]
    return NavContainer(
        NavParentLi(
            H4("Tables", cls="pl-4"),
            NavContainer(*table_links, parent=False),
        )
    )


def main_area(*args, **kwargs):
    return Title("Quran SRS"), Container(
        Div(
            NavBar(A("Home", href=index), brand=H3("Quran SRS")),
            DividerLine(y_space=0),
            cls="bg-white sticky top-0 z-10",
        ),
        Div(
            Div(side_nav(**kwargs), cls="flex-1 p-2"),
            Main(*args, cls="flex-[4] border-l-2 p-4", id="main") if args else None,
            cls=(FlexT.block, "flex-col md:flex-row"),
        ),
        cls=ContainerT.xl,
    )


@rt
def index():
    return main_area()


@rt
def user():
    def _render_user(user):
        return Tr(
            Td(user.id),
            Td(user.name),
            Td(user.email),
            Td(user.password),
            Td(
                A(
                    "Edit",
                    hx_get=f"/user/edit/{user.id}",
                    target_id="main",
                    cls=AT.muted,
                ),
                " | ",
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
        Thead(Tr(Th("id"), Th("name"), Th("email"), Th("password"), Th("Action"))),
        Tbody(*map(_render_user, users())),
    )
    return main_area(
        Button(
            "Add", type="button", hx_get="/user/add", target_id="main", cls=ButtonT.link
        ),
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
    return Titled("Edit User", fill_form(form, current_user))


@rt("/user/edit")
def post(user_details: User):
    users.update(user_details)
    return Redirect(user)


@rt("/user/delete/{user_id}")
def delete(user_id: int):
    users.delete(user_id)


@rt("/user/add")
def get():
    return Titled("Add User", create_user_form("add"))


@rt("/user/add")
def post(user_details: User):
    del user_details.id
    users.insert(user_details)
    return Redirect(user)


@rt
def revision(sess):
    last_added_page = sess.get("last_added_page", None)

    if isinstance(last_added_page, int):
        last_added_page += 1

    def _render_revision(user):
        return Tr(
            # Td(user.id),
            # Td(user.user_id),
            Td(user.page),
            Td(user.revision_date),
            Td(user.rating),
            Td(
                A(
                    "Edit",
                    hx_get=f"/revision/edit/{user.id}",
                    target_id="main",
                    cls=AT.muted,
                ),
                " | ",
                A(
                    "Delete",
                    hx_delete=f"/revision/delete/{user.id}",
                    target_id=f"revision-{user.id}",
                    hx_swap="outerHTML",
                    hx_confirm="Are you sure?",
                    cls=AT.muted,
                ),
            ),
            id=f"revision-{user.id}",
        )

    table = Table(
        Thead(
            Tr(
                # Columns are temporarily hidden
                # Th("id"),
                # Th("user_id"),
                Th("page"),
                Th("revision_date"),
                Th("rating"),
                Th("Action"),
            )
        ),
        Tbody(*map(_render_revision, revisions(order_by="id desc"))),
    )
    return main_area(
        DivFullySpaced(
            DivLAligned(
                Input(
                    type="number",
                    placeholder="page",
                    cls="max-w-20",
                    id="page",
                    value=last_added_page,
                ),
                Button(
                    "Add",
                    type="button",
                    hx_get="/revision/add",
                    hx_include="#page",
                    target_id="main",
                    cls=ButtonT.link,
                ),
                Button(
                    "Bulk",
                    type="button",
                    hx_get="/revision/bulk_add",
                    hx_include="#page",
                    target_id="main",
                    cls=ButtonT.link,
                ),
            ),
            DivLAligned(
                Button("Import", type="button", hx_get=import_csv, target_id="main"),
                A(Button("Export"), href=export_csv),
            ),
            cls="flex-wrap gap-4",
        ),
        Div(table, cls="uk-overflow-auto"),
        active="Revision",
    )


def create_revision_form(type):
    def RadioLabel(o):
        label, value = o
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
            *map(_option, users()), label="User_Id", name="user_id", cls="hidden"
        ),
        LabelInput("Revision_Date", type="date", value=current_time("%Y-%m-%d")),
        LabelInput("Page", type="number", input_cls="text-2xl"),
        Div(
            FormLabel("Rating"),
            *map(RadioLabel, {"✅ Good": "1", "😄 Ok": "0", "❌ Bad": "-1"}.items()),
            cls="space-y-2 leading-8 sm:leading-6 ",
        ),
        Div(
            Button("Save", cls=ButtonT.primary),
            A(Button("Cancel", type="button", cls=ButtonT.secondary), href=revision),
            cls="flex justify-around items-center w-full",
        ),
        hx_post=f"/revision/{type}",
        target_id="main",
    )


@rt("/revision/edit/{revision_id}")
def get(revision_id: int):
    current_revision = revisions[revision_id]
    # Convert rating to string in order to make the fill_form to select the option.
    current_revision.rating = str(current_revision.rating)
    form = create_revision_form("edit")
    return Titled("Edit Revision", fill_form(form, current_revision))


@rt("/revision/edit")
def post(revision_details: Revision):
    revisions.update(revision_details)
    return Redirect(revision)


@rt("/revision/delete/{revision_id}")
def delete(revision_id: int):
    revisions.delete(revision_id)


@rt("/revision/add")
def get(page: int):
    return Titled(
        "Add Revision", fill_form(create_revision_form("add"), {"page": page})
    )


@rt("/revision/add")
def post(revision_details: Revision, sess):
    # The id is set to zero in the form, so we need to delete it
    # before inserting to generate the id automatically
    del revision_details.id
    revisions.insert(revision_details)

    page = revision_details.page
    sess["last_added_page"] = page

    notification = Toast(
        f"Sucessfully added revision for page {page}",
        alert_cls=AlertT.success,
        cls=(ToastVT.top, ToastHT.center, "z-20"),
    )
    return notification, Titled(
        "Add Revision", fill_form(create_revision_form("add"), {"page": page + 1})
    )


@app.get("/revision/bulk_add")
def get(page: int, date: str = None):

    def _render_row(current_page):
        def _render_radio(o):
            label, value = o
            is_checked = True if value == "1" else False
            return FormLabel(
                Radio(
                    id=f"rating-{current_page}",
                    value=value,
                    checked=is_checked,
                ),
                Span(label),
                cls="space-x-2",
            )

        return Tr(
            Td(P(current_page, cls="text-xl")),
            Td(
                Div(
                    *map(
                        _render_radio,
                        {"✅ Good": "1", "😄 Ok": "0", "❌ Bad": "-1"}.items(),
                    ),
                    cls=(FlexT.block, FlexT.row, FlexT.wrap, "gap-x-6 gap-y-4"),
                )
            ),
        )

    last_page = page + 5
    table = Table(
        Thead(Tr(Th("page"), Th("rating"))),
        Tbody(*[_render_row(i) for i in range(page, last_page)]),
    )

    action_buttons = Div(
        Button(
            "Save",
            type="button",
            hx_post="/revision/bulk_add",
            target_id="main",
            cls=ButtonT.primary,
        ),
        A(Button("Cancel", type="button", cls=ButtonT.secondary), href=revision),
        cls=(FlexT.block, FlexT.around, FlexT.middle, "w-full"),
    )

    # TODO: Later handle the user selection by session, for now temporarily setting it to siraj
    try:
        user_id = users(where="name='Siraj'")[0].id
    except IndexError:
        user_id = 1

    return Titled(
        "Bulk Revision",
        Form(
            Hidden(id="user_id", value=user_id),
            Hidden(name="last_page", value=last_page),
            LabelInput("Date", type="date", value=(date or current_time("%Y-%m-%d"))),
            table,
            action_buttons,
        ),
    )


@rt("/revision/bulk_add")
async def post(user_id: int, date: str, last_page: int, sess, req):
    form_data = await req.form()

    parsed_data = [
        Revision(
            page=int(page.split("-")[1]),
            rating=int(rating),
            user_id=user_id,
            revision_date=date,
        )
        for page, rating in form_data.items()
        if page.startswith("rating-")
    ]
    revisions.insert_all(parsed_data)

    sess["last_added_page"] = parsed_data[-1].page

    return RedirectResponse(
        f"/revision/bulk_add?page={last_page}&date={date}", status_code=303
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
        hx_post=import_csv,
    )
    return Titled("Upload CSV", form)


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


serve()
