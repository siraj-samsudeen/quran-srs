from fasthtml.common import *
from monsterui.all import *
import pandas as pd
import time
from utils import get_database_connection
from app.common_function import (
    main_area,
    get_current_date,
    get_page_description,
    create_app_with_auth,
    get_mode_count,
    get_start_text,
    graduate_the_item_id,
    checkbox_update_logic,
)

db = get_database_connection()

revisions = db.t.revisions
items = db.t.items
surahs = db.t.surahs
hafizs_items = db.t.hafizs_items

(Revision, Item, Surah, Hafiz_Items) = (
    revisions.dataclass(),
    items.dataclass(),
    surahs.dataclass(),
    hafizs_items.dataclass(),
)

recent_review_app, rt = create_app_with_auth()


def graduate_btn_recent_review(
    item_id, is_graduated=False, is_disabled=False, **kwargs
):
    return Switch(
        hx_vals={"item_id": item_id},
        hx_post=f"/recent_review/graduate",
        checked=is_graduated,
        name=f"is_checked",
        id=f"graduate-btn-{item_id}",
        cls=("hidden" if is_disabled else ""),
        **kwargs,
    )


@recent_review_app.get("/")
def recent_review_view(auth):
    hafiz_items_data = hafizs_items(where="mode_id IN (2,3,4)", order_by="item_id ASC")
    items_id_with_mode = [
        {
            "item_id": hafiz_item.item_id,
            "mode_id": 3 if (hafiz_item.mode_id == 2) else hafiz_item.mode_id,
        }
        for hafiz_item in hafiz_items_data
    ]
    # custom sort order to group the graduated and ungraduated
    items_id_with_mode.sort(key=lambda x: (x["mode_id"], x["item_id"]))

    item_ids = [item["item_id"] for item in items_id_with_mode]
    qry = f"""
    SELECT MIN(revision_date) as earliest_date
    FROM revisions
    WHERE item_id IN ({", ".join(map(str, item_ids))})
    """
    ct = db.q(qry)
    earliest_date = ct[0]["earliest_date"]

    current_date = get_current_date(auth)
    # Change the date range to start from the earliest date
    date_range = pd.date_range(
        start=(earliest_date or current_date), end=current_date, freq="D"
    )[::-1]

    def render_row(o):
        item_id, mode_id = o["item_id"], o["mode_id"]

        def render_checkbox(date):
            formatted_date = date.strftime("%Y-%m-%d")
            current_revision_data = revisions(
                where=f"revision_date = '{formatted_date}' AND item_id = {item_id} AND mode_id IN (2,3);"
            )

            if current_revision_data:
                is_newly_memorized = current_revision_data[0].mode_id == 2
            else:
                is_newly_memorized = False

            return Td(
                Form(
                    Hidden(name="date", value=formatted_date),
                    CheckboxX(
                        name=f"is_checked",
                        value="1",
                        hx_post=f"/recent_review/update_status/{item_id}",
                        target_id=f"count-{item_id}",
                        checked=True if current_revision_data else False,
                        _at_change="updateVisibility($event.target)",
                        # This @click is to handle the shift+click.
                        _at_click=f"handleShiftClick($event, 'date-{formatted_date}')",
                        disabled=(mode_id == 4) or is_newly_memorized,
                        cls=(
                            "hidden",
                            "disabled:opacity-50",
                            # date-<class> is to identify the row for shift+click
                            f"date-{formatted_date}",
                            (
                                # If it is newly memorized then render the intermidiate checkbox icon
                                "checked:bg-[image:var(--uk-form-checkbox-image-indeterminate)]"
                                if is_newly_memorized
                                else ""
                            ),
                        ),
                    ),
                    cls="",
                ),
                Span("-", cls="hidden"),
                cls="text-center",
            )

        revision_count = get_mode_count(item_id, 3)

        return Tr(
            Td(get_page_description(item_id), cls="sticky left-0 z-20 bg-white"),
            Td(get_start_text(item_id), cls=TextT.lg),
            Td(
                revision_count,
                cls="text-center",
                id=f"count-{item_id}",
            ),
            Td(
                Div(
                    graduate_btn_recent_review(
                        item_id,
                        is_graduated=(mode_id == 4),
                        is_disabled=(revision_count == 0),
                    ),
                    cls=(FlexT.block, FlexT.center, FlexT.middle, "min-h-11"),
                )
            ),
            *map(render_checkbox, date_range),
            id=f"row-{item_id}",
        )

    table = Table(
        Thead(
            Tr(
                Th("Pages", cls="min-w-28 sm:min-w-36 sticky left-0 z-20 bg-white"),
                Th("Start Text", cls="min-w-28"),
                Th("Count"),
                Th("Graduate"),
                *[
                    Th(date.strftime("%b %d %a"), cls="!text-center sm:min-w-28")
                    for date in date_range
                ],
            )
        ),
        Tbody(*map(render_row, items_id_with_mode)),
        cls=(TableT.middle, TableT.divider, TableT.hover, TableT.sm, TableT.justify),
    )
    content_body = Div(
        H2("Recent Review"),
        Div(
            table,
            cls="uk-overflow-auto",
            id="recent_review_table_area",
        ),
        cls="text-xs sm:text-sm",
        # Currently this variable is not being used but it is needed for alpine js attributes
        x_data="{ showAll: false }",
    )

    return main_area(
        content_body,
        Script(src="/public/recent_review_logic.js"),
        active="Home",
        auth=auth,
    )


@recent_review_app.post("/update_status/{item_id}")
def update_status_for_recent_review(item_id: int, date: str, is_checked: bool = False):

    checkbox_update_logic(
        mode_id=3, rating=1, item_id=item_id, date=date, is_checked=is_checked
    )
    revision_count = get_mode_count(item_id, 3)

    if revision_count > 6:
        # We are redirecting to swap the entire row
        # as we want to render the disabled checkbox with graduated button
        return RedirectResponse(f"/recent_review/graduate?item_id={item_id}")

    return revision_count, graduate_btn_recent_review(
        item_id, is_disabled=(revision_count == 0), hx_swap_oob="true"
    )


@recent_review_app.post("/graduate")
def graduate_recent_review(item_id: int, auth, is_checked: bool = False):

    # Retry logic with 3 attempts and 50ms delay
    # To handle multiple simultaneous req from the user
    # typically when shift-clicking the checkbox where it will trigger multiple requests
    for attempt in range(3):
        try:
            graduate_the_item_id(
                item_id=item_id, mode_id=3, auth=auth, checked=is_checked
            )
            break  # Success, exit the loop
        except Exception as e:
            if attempt < 2:  # Only delay if not the last attempt
                time.sleep(0.05)

    # We can also use the route funtion to return the entire page as output
    # And the HTMX headers are used to change the (re)target,(re)select only the current row
    return recent_review_view(auth), HtmxResponseHeaders(
        retarget=f"#row-{item_id}",
        reselect=f"#row-{item_id}",
        reswap="outerHTML",
    )
