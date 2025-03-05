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
    return Titled("User", A("Back", href=index))


@rt
def revision():
    return Titled("Revision", A("Back", href=index))


serve()
