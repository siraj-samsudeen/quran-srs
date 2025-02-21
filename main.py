from fasthtml.common import *
from utils import standardize_column, convert_time

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
Revision, User = revisions.dataclass(), users.dataclass()


column_headers = [
    "Page",
    "Revision Time",
    "Rating",
    "Created By",
    "Created At",
    "Last Modified By",
    "Last Modified At",
]

column_standardized = list(map(standardize_column, column_headers))
date_columns = [
    c for c in column_standardized if c.endswith("time") or c.endswith("at")
]


def render_revision_row(revision):
    # Convert the revision object to a dictionary to easily access its attributes by column names
    rev_dict = vars(revision)

    def render_cell(column, value):
        if column in date_columns:
            return Td(convert_time(value))
        return Td(value)

    return Tr(*[render_cell(c, rev_dict[c]) for c in column_standardized])


@rt
def index():
    return Titled(
        "Quran SRS Home",
        Div("Fresh start with FastHTML"),
        Div("Nav: ", A("Revision", href=revision)),
    )


@rt
def revision():
    table = (
        Table(
            Thead(Tr(*map(Th, column_headers))),
            Tbody(*map(render_revision_row, revisions())),
        ),
    )
    return Titled("Quran SRS Revision", table)


serve()
