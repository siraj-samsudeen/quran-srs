from fasthtml.common import *
from monsterui.all import *
from utils import *
from constants import *
from app.common_function import *
from database import *


page_details_app, rt = create_app_with_auth()


@page_details_app.get("/")
def page_details_view(auth):
    mode_code_list, mode_name_list = get_mode_name_and_code()

    # To get the count of the records under each modes to display
    mode_case_statements = []
    for mode_code in mode_code_list:
        case_stmt = f"COALESCE(SUM(CASE WHEN revisions.mode_code = '{mode_code}' THEN 1 END), '-') AS '{mode_code}'"
        mode_case_statements.append(case_stmt)
    mode_cases = ",\n".join(mode_case_statements)

    display_pages_query = f"""SELECT 
                            items.id,
                            items.surah_id,
                            pages.page_number,
                            pages.juz_number,
                            {mode_cases},
                            SUM(revisions.rating) AS rating_summary
                        FROM revisions
                        LEFT JOIN items ON revisions.item_id = items.id
                        LEFT JOIN pages ON items.page_id = pages.id
                        WHERE revisions.hafiz_id = {auth} AND items.active != 0
                        GROUP BY items.id
                        ORDER BY pages.page_number;"""
    hafiz_items_with_details = db.q(display_pages_query)
    grouped = group_by_type(hafiz_items_with_details, "id")

    def render_row_based_on_type(
        records: list,
        row_link: bool = True,
    ):
        r = records[0]

        get_page = f"/page_details/{r['id']}"  # item_id

        hx_attrs = (
            {
                "hx_get": get_page,
                "hx_target": "body",
                "hx_replace_url": "true",
                "hx_push_url": "true",
            }
            if row_link
            else {}
        )
        rating_summary = r["rating_summary"]

        return Tr(
            Td(get_page_description(item_id=r["id"], link="#")),
            *map(lambda code: Td(r[code]), mode_code_list),
            Td(rating_summary),
            Td(
                A(
                    "See Details ➡️",
                    cls=AT.classic,
                ),
                cls="text-right",
            ),
            **hx_attrs,
        )

    rows = [
        render_row_based_on_type(records)
        for type_number, records in list(grouped.items())
    ]
    table = Table(
        Thead(
            Tr(
                Th("Page"),
                *map(Th, mode_name_list),
                Th("Rating Summary"),
                Th(""),
                cls="sticky top-16 z-25 bg-white",
            )
        ),
        Tbody(*rows),
    )

    return main_area(
        Title("Page Details"),
        table,
        active="Page Details",
        auth=auth,
    )


@page_details_app.get("/{item_id}")
def display_page_level_details(auth, item_id: int):
    # Prevent editing description for inactive items
    is_active_item = bool(items(where=f"id = {item_id} and active != 0"))
    if not is_active_item:
        return Redirect("/page_details")

    mode_code_list, _mode_name_list = get_mode_name_and_code()

    # Avoid showing nav buttons (if the page has is no revision)
    rev_data = revisions(where=f"item_id = {item_id}")
    is_show_nav_btn = bool(rev_data)

    def _render_row(data, columns):
        tds = []
        for col in columns:
            value = data.get(col, "")
            if col == "rating":
                value = RATING_MAP.get(str(value), value)
            if col == "revision_date":
                value = date_to_human_readable(str(value))
            tds.append(Td(value))
        return Tr(*tds)

    def make_mode_title_for_table(mode_code):
        try:
            mode_details = modes[mode_code]
            mode_name, mode_description = (mode_details.name, mode_details.description)
        except NotFoundError:
            mode_name, mode_description = ("", "")
        return H2(mode_name, Subtitle(mode_description))

    is_item_exist = items(where=f"id = {item_id}")
    if is_item_exist:
        page_description = get_page_description(item_id, is_bold=False, is_link=False)
        juz = f"Juz {get_juz_name(item_id=item_id)}"
    else:
        Redirect("/page_details")

    if not mode_code_list:
        memorization_summary = ""
    else:
        ctn = []

        first_revision_data = revisions(
            where=f"item_id = {item_id} and hafiz_id = {auth} and mode_code IN ({", ".join([repr(code) for code in mode_code_list])})",
            order_by="revision_date ASC",
            limit=1,
        )
        if first_revision_data:
            first_revision = first_revision_data[0]
            first_memorized_date = (
                first_revision.revision_date
                if first_revision
                else Redirect("/page_details")
            )
            first_memorized_mode_code = (
                first_revision.mode_code
                if first_revision
                else Redirect("/page_details")
            )
            first_memorized_mode_name, description = make_mode_title_for_table(
                first_memorized_mode_code
            )
            ctn.append(
                P(
                    "This page was added on: ",
                    Span(Strong(date_to_human_readable(first_memorized_date))),
                    " under ",
                    Span(Strong(first_memorized_mode_name)),
                )
            )

            hafiz_items_details = get_hafizs_items(item_id)
            if hafiz_items_details:
                stat_columns = [
                    "srs_start_date",
                    "last_review",
                    "next_review",
                    "memorized",
                    "mode_code",
                    "last_interval",
                    "actual_interval",
                    "next_interval",
                ]
                rename_columns = {
                    "mode_code": "current_mode",
                    "last_interval": "previous_interval",
                }

                # Table View
                def render_stats(col_name: str):
                    if col_name == "actual_interval":
                        value = get_actual_interval(item_id)
                    else:
                        value = hafiz_items_details.__dict__[col_name]
                        if col_name == "mode_code":
                            value = get_mode_name(value)
                        elif col_name == "memorized":
                            value = "Yes" if value else "No"
                        else:
                            value = str(value).capitalize()
                    return Tr(
                        Th(destandardize_text(rename_columns.get(col_name, col_name))),
                        Td(value),
                    )

                stats_table = Table(
                    Tbody(*map(render_stats, stat_columns)),
                    cls=(TableT.sm, TableT.responsive, TableT.justify),
                )
                ctn.append(
                    Div(
                        A(
                            "Refresh stats",
                            hx_get="/hafiz/update_stats_column",
                            hx_vals={"item_id": item_id},
                            hx_target="body",
                            cls=AT.classic,
                        ),
                        stats_table,
                        cls="max-w-80 space-y-1",
                    )
                )

        if ctn:
            memorization_summary = Div(H2("Summary"), Div(*ctn, cls="space-y-3"))
        else:
            memorization_summary = ""

    def build_revision_query(mode_codes, row_alias):
        return f"""
            SELECT
                ROW_NUMBER() OVER (ORDER BY revision_date ASC) AS {row_alias},
                revision_date,
                rating,
                modes.name AS mode_name,
                next_interval,
            CASE
                WHEN LAG(revision_date) OVER (ORDER BY revision_date) IS NULL THEN ''
                ELSE CAST(
                    JULIANDAY(revision_date) - JULIANDAY(LAG(revision_date) OVER (ORDER BY revision_date))
                    AS INTEGER
                )
            END AS intervals_since_last_revision
            FROM revisions
            JOIN modes ON revisions.mode_code = modes.code
            WHERE item_id = {item_id} AND hafiz_id = {auth} AND revisions.mode_code IN ({", ".join(repr(code) for code in mode_codes)})
            ORDER BY revision_date ASC;
        """

    def create_mode_table(mode_codes):
        query = build_revision_query(mode_codes, "s_no")
        data = db.q(query)
        # determine table visibility
        has_data = len(data) > 0
        # This is to render the srs table different from others
        cols = [
            "s_no",
            "revision_date",
            "rating",
            "mode_name",
            "intervals_since_last_revision",
            "next_interval",
        ]

        table = Div(
            Table(
                Thead(*(Th(col.replace("_", " ").title()) for col in cols)),
                Tbody(*[_render_row(row, cols) for row in data]),
            )
        )

        return has_data, table

    has_summary_data, summary_table = create_mode_table(mode_code_list)

    def create_nav_button(item_id, arrow, show_nav):
        return A(
            arrow if item_id and show_nav else "",
            href=f"/page_details/{item_id}" if item_id is not None else "#",
            cls="uk-button uk-button-default",
        )

    prev_id, next_id = get_prev_next_item_ids(auth, item_id)
    prev_pg = create_nav_button(prev_id, "⬅️", is_show_nav_btn)
    next_pg = create_nav_button(next_id, "➡️", is_show_nav_btn)

    item_details = items[item_id]
    description = item_details.description
    start_text = item_details.start_text

    edit_description = DivVStacked(
        Table(
            Tr(
                Td("Description: "),
                Td(description, id="description"),
            ),
            Tr(
                Td("Start Text: "),
                Td(start_text, id="start_text", cls=TextT.lg),
            ),
            Tr(
                Td(
                    Div(
                        Button(
                            "Edit",
                            hx_get=f"/page_details/edit/{item_id}",
                            cls=(ButtonT.default, ButtonT.xs),
                        ),
                        id="btns",
                    ),
                    colspan="2",
                ),
                cls="text-center",
            ),
            cls="max-w-xs",
            id="item_description_table",
        ),
    )
    return main_area(
        Div(
            Div(
                DivFullySpaced(
                    prev_pg,
                    Div(
                        DivVStacked(
                            H1(page_description, cls="uk-text-center"),
                        ),
                        id="page-details-header",
                    ),
                    next_pg,
                ),
                Subtitle(Strong(juz), cls="uk-text-center"),
                edit_description,
                cls="space-y-8",
            ),
            Div(
                memorization_summary,
                (
                    Div(H2("Revision History"), summary_table)
                    if has_summary_data
                    else None
                ),
                cls="space-y-6",
            ),
        ),
        active="Page Details",
        auth=auth,
    )


@page_details_app.get("/edit/{item_id}")
def page_description_edit_form(item_id: int):
    item_details = items[item_id]
    description = item_details.description
    start_text = item_details.start_text
    description_field = (
        LabelInput(
            "Description: ",
            name="description",
            value=description,
            id="description",
            hx_swap_oob="true",
            placeholder=description,
        ),
    )
    start_text_field = (
        LabelInput(
            "Start Text: ",
            name="start_text",
            value=start_text,
            id="start_text",
            hx_swap_oob="true",
            placeholder=start_text,
            cls=TextT.lg,
        ),
    )
    buttons = Div(
        Button(
            "Update",
            hx_put=f"/admin/tables/items/{item_id}",
            hx_vals={"redirect_link": f"/page_details/{item_id}"},
            hx_target="#item_description_table",
            hx_select="#item_description_table",
            hx_select_oob="#page-details-header",
            hx_include="#description, #start_text",
            cls=(ButtonT.default, ButtonT.xs),
        ),
        Button(
            "Cancel",
            type="button",
            hx_get=f"/page_details/{item_id}",
            hx_target="#item_description_table",
            hx_select="#item_description_table",
            cls=(ButtonT.default, ButtonT.xs),
        ),
        cls="space-x-4",
        hx_swap_oob="true",
        id="btns",
    )

    return description_field, start_text_field, buttons
