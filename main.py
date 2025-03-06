from fasthtml.common import *
from monsterui.all import *

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


@rt
def index():
    return Titled(
        "Quran SRS", A("User", href=user), " | ", A("Revision", href=revision)
    )


@rt
def user():
    def _render_user(user):
        return Tr(
            Td(user.id),
            Td(user.name),
            Td(user.email),
            Td(user.password),
            Td(
                A("Edit", href=f"/user/edit/{user.id}"),
                " | ",
                A(
                    "Delete",
                    hx_delete=f"/user/delete/{user.id}",
                    target_id=f"user-{user.id}",
                    hx_swap="outerHTML",
                    hx_confirm="Are you sure?",
                ),
            ),
            id=f"user-{user.id}",
        )

    table = Table(
        Thead(Tr(Th("id"), Th("name"), Th("email"), Th("password"), Th("Action"))),
        Tbody(*map(_render_user, users())),
    )
    return Titled(
        "User", A("Back", href=index), " | ", A("Add", href="/user/add"), Div(table)
    )


def create_user_form(url):
    return Form(
        Hidden(name="id"),
        LabelInput("Name"),
        LabelInput("Email"),
        LabelInput("Password"),
        DivFullySpaced(Button("Save"), A(Button("Discard", type="button"), href=user)),
        method="POST",
        action=url,
    )


@rt("/user/edit/{user_id}")
def get(user_id: int):
    current_user = users[user_id]
    form = create_user_form(f"/user/edit")
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
    return Titled("Add User", create_user_form("/user/add"))


@rt("/user/add")
def post(user_details: User):
    del user_details.id
    users.insert(user_details)
    return Redirect(user)


@rt
def revision():
    def _render_revision(user):
        return Tr(
            Td(user.id),
            Td(user.user_id),
            Td(user.page),
            Td(user.revision_date),
            Td(user.rating),
            Td(
                A("Edit", href=f"/revision/edit/{user.id}"),
                " | ",
                A(
                    "Delete",
                    hx_delete=f"/revision/delete/{user.id}",
                    target_id=f"revision-{user.id}",
                    hx_swap="outerHTML",
                    hx_confirm="Are you sure?",
                ),
            ),
            id=f"revision-{user.id}",
        )

    table = Table(
        Thead(
            Tr(
                Th("id"),
                Th("user_id"),
                Th("page"),
                Th("revision_date"),
                Th("rating"),
                Th("Action"),
            )
        ),
        Tbody(*map(_render_revision, revisions())),
    )
    return Titled(
        "Revision",
        A("Back", href=index),
        " | ",
        A("Add", href="/revision/add"),
        Div(table),
    )


def create_revision_form(url):
    return Form(
        Hidden(name="id"),
        LabelInput("User_Id", type="number"),
        LabelInput("Page", type="number"),
        LabelInput("Revision_Date", type="date"),
        LabelInput("Rating", type="number"),
        DivFullySpaced(
            Button("Save"), A(Button("Discard", type="button"), href=revision)
        ),
        method="POST",
        action=url,
    )


@rt("/revision/edit/{revision_id}")
def get(revision_id: int):
    current_revision = revisions[revision_id]
    form = create_revision_form(f"/revision/edit")
    return Titled("Edit Revision", fill_form(form, current_revision))


@rt("/revision/edit")
def post(revision_details: Revision):
    revisions.update(revision_details)
    return Redirect(revision)


@rt("/revision/delete/{revision_id}")
def delete(revision_id: int):
    revisions.delete(revision_id)


@rt("/revision/add")
def get():
    return Titled("Add Revision", create_revision_form(f"/revision/add"))


@rt("/revision/add")
def post(revision_details: Revision):
    del revision_details.id
    revisions.insert(revision_details)
    return Redirect(revision)


serve()
