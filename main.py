from fasthtml.common import *

app, rt = fast_app(live=True)

db = database("data/quran.db")

revisions, users = db.t.revisions, db.t.users
if revisions not in db.t:
    users.create(user_id=int, name=str, email=str, password=str, pk="user_id")
    revisions.create(
        id=int,
        user_id=int,
        page=int,
        revision_time=int,
        rating=str,
        created_by=str,
        created_at=int,
        last_modified_by=str,
        last_modified_at=int,
        pk="id",
    )


@rt
def index():
    return Titled("Quran SRS Home", Div("Fresh start with FastHTML"))


serve()
