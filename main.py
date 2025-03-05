from fasthtml.common import *

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

app, rt = fast_app()


@rt
def index():
    return Titled("Quran SRS", A("User", href=user), " ", A("Revision", href=revision))


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
        Thead(Tr(Th("ID"), Th("Name"), Th("Email"), Th("Password"), Th("Action"))),
        Tbody(*map(_render_user, users())),
    )
    return Titled(
        "User", A("Back", href=index), " | ", A("Add", href="/user/add"), Div(table)
    )


@rt("/user/edit/{user_id}")
def get(user_id: int):
    user = users[user_id]
    form = Form(
        Label("ID", Input(name="id")),
        Label("Name", Input(name="name")),
        Label("Email", Input(name="email")),
        Label("Password", Input(name="password")),
        Button("Save"),
        method="POST",
        action=f"/user/edit/{user_id}",
    )
    return Titled("Edit User", fill_form(form, user))


@rt("/user/edit/{user_id}")
def post(user_id: int, user_details: User):
    users.update(user_details, user_id)
    return Redirect(user)


@rt("/user/delete/{user_id}")
def delete(user_id: int):
    users.delete(user_id)


@rt("/user/add")
def get():
    form = form = Form(
        Label("id", Input(name="id")),
        Label("name", Input(name="name")),
        Label("email", Input(name="email")),
        Label("password", Input(name="password")),
        Button("Save"),
        method="POST",
        action=f"/user/add",
    )
    return Titled("Add User", form)


@rt("/user/add")
def post(user_details: User):
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
        )

    table = Table(
        Thead(
            Tr(Th("id"), Th("user_id"), Th("page"), Th("revision_date"), Th("rating"))
        ),
        Tbody(*map(_render_revision, revisions())),
    )
    return Titled("Revision", A("Back", href=index), Div(table))


serve()
