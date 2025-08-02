from fasthtml.common import *
from monsterui.all import *
from utils import *
from app.common_function import *

db = get_database_connection()

revisions = db.t.revisions
items = db.t.items
statuses = db.t.statuses

(Revision, Item, Status) = (
    revisions.dataclass(),
    items.dataclass(),
    statuses.dataclass(),
)

page_details_app, rt = create_app_with_auth()


@page_details_app.get("/")
def page_details_view(auth):
    mode_id_list, mode_name_list = get_ordered_mode_name_and_id()

    # To get the count of the records under each modes to display
    mode_case_statements = []
    for mode_id in mode_id_list:
        case_stmt = f"COALESCE(SUM(CASE WHEN revisions.mode_id = {mode_id} THEN 1 END), '-') AS '{mode_id}'"
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
            *map(lambda id: Td(r[str(id)]), mode_id_list),
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

    mode_id_list, mode_name_list = get_ordered_mode_name_and_id()

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

    def make_mode_title_for_table(mode_id):
        mode_details = modes(where=f"id = {mode_id}")
        if mode_details:
            mode_details = mode_details[0]
            mode_name, mode_description = (mode_details.name, mode_details.description)
        else:
            mode_name, mode_description = ("", "")
        return H2(mode_name, Subtitle(mode_description))

    ###### Title and Juz
    is_item_exist = items(where=f"id = {item_id}")
    if is_item_exist:
        page_description = get_page_description(item_id, is_bold=False, is_link=False)
        juz = f"Juz {get_juz_name(item_id=item_id)}"
    else:
        Redirect("/page_details")

    ####### Summary of first memorization
    if not mode_id_list:
        memorization_summary = ""
    else:
        ctn = []

        first_revision_data = revisions(
            where=f"item_id = {item_id} and hafiz_id = {auth} and mode_id IN ({', '.join(map(str, mode_id_list))})",
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
            first_memorized_mode_id = (
                first_revision.mode_id if first_revision else Redirect("/page_details")
            )
            first_memorized_mode_name, description = make_mode_title_for_table(
                first_memorized_mode_id
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
                    "last_review",
                    "status_id",
                    "mode_id",
                    "last_interval",
                    "current_interval",
                    "next_interval",
                ]
                rename_columns = {
                    "mode_id": "current_mode",
                    "last_interval": "previous_interval",
                    "current_interval": "actual_interval",
                }

                # Table View
                def render_stats(col_name: str):
                    value = hafiz_items_details.__dict__[col_name]
                    if col_name == "mode_id":
                        value = get_mode_name(value)
                    elif col_name == "status_id":
                        value = statuses[value].name
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

    ########### Display Tables

    def build_revision_query(mode_ids, row_alias):
        """It fetch the revision data for the current item_id with specified mode_ids"""
        return f"""
            SELECT
                ROW_NUMBER() OVER (ORDER BY revision_date ASC) AS {row_alias},
                revision_date,
                rating,
                modes.name AS mode_name,
                last_interval AS previous_interval,
                current_interval AS actual_interval,
                next_interval,
            CASE
                WHEN LAG(revision_date) OVER (ORDER BY revision_date) IS NULL THEN ''
                ELSE CAST(
                    JULIANDAY(revision_date) - JULIANDAY(LAG(revision_date) OVER (ORDER BY revision_date))
                    AS INTEGER
                )
            END AS interval
            FROM revisions
            JOIN modes ON revisions.mode_id = modes.id
            WHERE item_id = {item_id} AND hafiz_id = {auth} AND revisions.mode_id IN ({", ".join(map(str, mode_ids))})
            ORDER BY revision_date ASC;
        """

    def create_mode_table(mode_ids, is_summary=False):
        """Generate a table for the specified mode, returning both its visibility status and the table itself"""
        query = build_revision_query(mode_ids, "s_no")
        data = db.q(query)
        # determine table visibility
        has_data = len(data) > 0
        # This is to render the srs table different from others
        if len(mode_ids) == 1 and 5 in mode_ids:
            cols = [
                "s_no",
                "revision_date",
                "rating",
                "previous_interval",
                "actual_interval",
                "next_interval",
            ]
        else:
            cols = ["s_no", "revision_date", "rating", "interval"]
        cls = "uk-overflow-auto max-h-[30vh] p-4"
        if is_summary:
            # summary table has all records regradless of mode, so we need to add mode_name column
            cols.insert(3, "mode_name")
            cls = ""

        table = Div(
            Table(
                Thead(*(Th(col.replace("_", " ").title()) for col in cols)),
                Tbody(*[_render_row(row, cols) for row in data]),
            ),
            cls=cls,
        )

        return has_data, table

    ########### Summary Table
    has_summary_data, summary_table = create_mode_table(mode_id_list, is_summary=True)

    ########### Mode specific tables
    # Dynamically generate tables for each specific revision mode
    mode_data_map = {}
    for mode_id in mode_id_list:
        has_data, table = create_mode_table([mode_id])
        mode_data_map[mode_id] = (has_data, table)

    # Create mode sections dynamically
    mode_sections = []
    for mode_id in mode_id_list:
        is_display, table = mode_data_map[mode_id]
        if is_display:
            mode_sections.append(Div(make_mode_title_for_table(mode_id), table))

    ########### Previous and Next Page Navigation
    def create_nav_button(item_id, arrow, show_nav):
        return A(
            arrow if item_id and show_nav else "",
            href=f"/page_details/{item_id}" if item_id is not None else "#",
            cls="uk-button uk-button-default",
        )

    def get_prev_next_item_ids(current_item_id):
        def build_nav_query(operator, sort_order):
            return f"""SELECT items.id, pages.page_number FROM revisions
                       LEFT JOIN items ON revisions.item_id = items.id
                       LEFT JOIN pages ON items.page_id = pages.id
                       WHERE revisions.hafiz_id = {auth} AND items.active != 0 AND items.id {operator} {current_item_id}
                       ORDER BY items.id {sort_order} LIMIT 1;"""

        prev_result = db.q(build_nav_query("<", "DESC"))
        next_result = db.q(build_nav_query(">", "ASC"))
        prev_id = prev_result[0]["id"] if prev_result else None
        next_id = next_result[0]["id"] if next_result else None
        return prev_id, next_id

    prev_id, next_id = get_prev_next_item_ids(item_id)
    prev_pg = create_nav_button(prev_id, "⬅️", is_show_nav_btn)
    next_pg = create_nav_button(next_id, "➡️", is_show_nav_btn)

    ########### Display Editable Description and Start Text
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
                Div(H2("Summary Table"), summary_table) if has_summary_data else None,
                *mode_sections,
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
