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
        return Tr(Td(user.id), Td(user.name), Td(user.email), Td(user.password))

    table = Table(
        Thead(Tr(Th("ID"), Th("Name"), Th("Email"), Th("Password"))),
        Tbody(*map(_render_user, users())),
    )
    return Titled("User", A("Back", href=index), Div(table))


@rt
def revision():
    return Titled("Revision", A("Back", href=index))


serve()
