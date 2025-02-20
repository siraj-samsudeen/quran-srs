from fasthtml.common import *

app, rt = fast_app(live=True)


@rt
def index():
    return Titled("Quran SRS Home", Div("Fresh start with FastHTML"))


serve()
