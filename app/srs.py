from fasthtml.common import *
from monsterui.all import *
from utils import *
from app.common_function import *

db = get_database_connection()

revisions = db.t.revisions
items = db.t.items
hafizs_items = db.t.hafizs_items

(Revision, Item, Hafiz_Items) = (
    revisions.dataclass(),
    items.dataclass(),
    hafizs_items.dataclass(),
)

srs_app, rt = create_app_with_auth()


@srs_app.get("/")
def srs_detailed_page_view(
    auth,
    sort_col: str = "last_review_date",
    sort_type: str = "desc",
    is_bad_streak: bool = True,
):
    current_date = get_current_date(auth)

    ##################### SRS Eligible Table #####################
    columns = [
        "Page",
        "Start Text",
        "Bad Streak",
        "Last Review Date",
        "Bad %",
        "Total Count",
        "Bad Count",
    ]
    bad_streak_items = hafizs_items(
        where=f"mode_id <> 5 AND status_id != 6 {"AND bad_streak > 0" if is_bad_streak else ""}",
        order_by="last_review DESC",
    )

    # sorted the records based on the sort_col and sort_type from the input, and after page sort to group them on main sort
    eligible_records = []
    for record in bad_streak_items:
        current_item_id = record.item_id
        total_count = record.count
        bad_count = record.bad_count
        bad_percent = (
            format_number((bad_count / total_count) * 100) if total_count > 0 else 0
        )
        eligible_records.append(
            {
                "page": current_item_id,
                "start_text": get_start_text(current_item_id),
                "bad_streak": record.bad_streak,
                "last_review_date": record.last_review,
                "bad_%": bad_percent,
                "total_count": total_count,
                "bad_count": bad_count,
            }
        )
    eligible_records = sorted(eligible_records, key=lambda x: x["page"])
    eligible_records = sorted(
        eligible_records, key=lambda x: x[sort_col], reverse=(sort_type == "desc")
    )

    def render_srs_eligible_rows(record: dict):
        current_item_id = record["page"]
        page_description = get_page_description(current_item_id)
        bad_percentage = (
            f"{record["bad_%"]}%"
            if isinstance(record["bad_%"], int)
            else record["bad_%"]
        )
        checkbox = CheckboxX(
            name=f"item_ids",
            value=current_item_id,
            cls="srs_eligible_table",
            _at_click="handleCheckboxClick($event)",  # To handle `shift+click` selection
        )
        return Tr(
            Td(page_description),
            Td(record["start_text"]),
            Td(checkbox),
            Td(record["bad_streak"]),
            Td(render_date(record["last_review_date"])),
            Td(bad_percentage),
            Td(record["total_count"]),
            Td(record["bad_count"]),
            id=f"srs_eligible_row_{current_item_id}",
        )

    sort_fields = Form(
        P("Sort Options: ", cls=TextT.bold),
        custom_select(name="sort_col", vals=columns, default_val=sort_col),
        custom_select(name="sort_type", vals=["ASC", "DESC"], default_val=sort_type),
        Hidden(name="is_bad_streak", value="False"),
        LabelSwitch(
            label="Bad Streak",
            id="is_bad_streak",
            cls=(FlexT.block, FlexT.center, FlexT.middle, "gap-2"),
            lbl_cls="leading-none md:leading-6",
            checked=is_bad_streak,
        ),
        P("Applying the sort...", cls="htmx-indicator"),
        cls=("w-full gap-1 md:gap-4", FlexT.block, FlexT.middle),
        hx_get="/srs",
        hx_target="#srs_eligible_table",
        hx_select="#srs_eligible_table",
        hx_swap="outerHTML",
        hx_trigger="change",
        hx_replace_url="true",
        hx_indicator=".htmx-indicator",
    )
    srs_start_btn = Button(
        "Start SRS",
        type="button",
        hx_post="/srs/start-srs",
        hx_target="body",
        cls=(ButtonT.xs, ButtonT.primary),
    )
    srs_eligible_table = Div(
        H4("Eligible Pages"),
        Div(
            sort_fields,
            Form(
                Div(
                    Table(
                        Thead(
                            Tr(
                                *map(Td, columns[:2]),
                                Td(
                                    CheckboxX(
                                        cls=("select_all"),
                                        x_model="selectAll",  # To update the current status of the checkbox (checked or unchecked)
                                        _at_change="toggleAll()",  # based on that update the status of all the checkboxes
                                    )
                                ),
                                *map(Td, columns[2:]),
                            ),
                            cls="sticky z-50 top-0 bg-white",
                        ),
                        Tbody(*map(render_srs_eligible_rows, eligible_records)),
                        x_data=select_all_with_shift_click_for_summary_table(
                            class_name="srs_eligible_table"
                        ),
                        x_init="updateSelectAll()",
                    ),
                    cls="space-y-2 uk-overflow-auto h-[32vh]",
                    id="srs_eligible_table",
                ),
                srs_start_btn,
                cls="space-y-2",
            ),
        ),
        cls="space-y-2 mt-4",
    )

    ############ Current SRS Table ############
    current_srs_items = [
        i.item_id
        for i in hafizs_items(
            where=f"mode_id = 5", order_by="next_review DESC, item_id ASC"
        )
    ]

    # To sort the current srs records by due date
    current_srs_records = []
    for item_id in current_srs_items:
        hafiz_items_data = hafizs_items(where=f"item_id = {item_id}")
        if hafiz_items_data:
            hafiz_items_data = hafiz_items_data[0]
            last_review = hafiz_items_data.last_review
            next_review = hafiz_items_data.next_review
            if next_review:
                due = calculate_days_difference(next_review, current_date)
            else:
                # this is to render the "-" if there is no next page
                due = -1
            last_interval = hafiz_items_data.last_interval
            current_interval = hafiz_items_data.current_interval
            next_interval = hafiz_items_data.next_interval

            current_srs_records.append(
                {
                    "page": item_id,
                    "start_text": get_start_text(item_id),
                    "last_review": last_review,
                    "next_review": next_review,
                    "due": due,
                    "last_interval": last_interval,
                    "current_interval": current_interval,
                    "next_interval": next_interval,
                }
            )
    current_srs_records = sorted(
        current_srs_records, key=lambda x: x["due"], reverse=True
    )

    def render_current_srs_rows(records: dict):
        due = records["due"]
        if due < 0:
            due = "-"

        return Tr(
            Td(get_page_description(records["page"])),
            Td(records["start_text"]),
            Td(render_date(records["last_review"])),
            Td(render_date(records["next_review"])),
            Td(due),
            Td(records["last_interval"]),
            Td(records["current_interval"]),
            Td(records["next_interval"]),
        )

    current_srs_table = Div(
        H4("SRS Pages"),
        Div(
            Table(
                Thead(
                    Tr(
                        Td("Page"),
                        Td("Start Text"),
                        Td("Last Review"),
                        Td("Next Review"),
                        Td("Due"),
                        # TODO: The column names are renamed temporarly for testing
                        Td("Previous Interval"),
                        Td("Actual Interval"),
                        Td("Next Interval"),
                    ),
                    cls="sticky z-50 top-0 bg-white",
                ),
                Tbody(*map(render_current_srs_rows, current_srs_records)),
            ),
            cls="space-y-2 uk-overflow-auto h-[32vh]",
            id="current_srs_table",
        ),
    )

    return main_area(
        Div(
            DivFullySpaced(
                H1(get_mode_name(5)),
                A(
                    "Refresh stats",
                    hx_get="/hafiz/update_stats_column",
                    hx_target="body",
                    cls=AT.classic,
                ),
            ),
            srs_eligible_table,
            Divider(cls=("mb-4", DividerT.icon)),
            current_srs_table,
        ),
        auth=auth,
        active="SRS",
    )


@srs_app.post("/start-srs")
async def start_srs_for_multiple_records(req, auth):
    form_data = await req.form()
    item_ids = form_data.getlist("item_ids")

    for item_id in item_ids:
        start_srs(item_id, auth)

    return RedirectResponse(req.headers.get("referer", "/srs"), status_code=303)
