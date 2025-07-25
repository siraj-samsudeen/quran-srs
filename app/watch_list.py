from fasthtml.common import *
from monsterui.all import *
from utils import get_database_connection, day_diff, date_to_human_readable
from app.common_function import (
    main_area,
    get_current_date,
    get_page_description,
    create_app_with_auth,
    get_mode_count,
    get_start_text,
    graduate_the_item_id,
    render_rating,
    rating_dropdown,
    rating_radio,
    populate_hafizs_items_stat_columns,
    update_review_dates,
)

db = get_database_connection()

revisions = db.t.revisions
items = db.t.items
hafizs_items = db.t.hafizs_items

(Revision, Item, Hafiz_Items) = (
    revisions.dataclass(),
    items.dataclass(),
    hafizs_items.dataclass(),
)

watch_list_app, rt = create_app_with_auth()


@watch_list_app.get("/")
def watch_list_view(auth):
    current_date = get_current_date(auth)
    week_column = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6", "Week 7"]

    # This is to only get the watch_list item_id (which are not graduated yet)
    hafiz_items_data = hafizs_items(
        where=f"(mode_id = 4 OR watch_list_graduation_date IS NOT NULL) AND hafiz_id = {auth}",
        order_by="mode_id DESC, next_review ASC, item_id ASC",
    )

    def graduate_btn_watch_list(
        item_id, is_graduated=False, is_disabled=False, **kwargs
    ):
        return Switch(
            hx_vals={"item_id": item_id},
            hx_post=f"/watch_list/graduate",
            checked=is_graduated,
            name=f"is_checked",
            id=f"graduate-btn-{item_id}",
            cls=("hidden" if is_disabled else ""),
            **kwargs,
        )

    def render_row(hafiz_item):
        item_id = hafiz_item.item_id
        is_graduated = hafiz_item.mode_id == 1
        last_review = hafiz_item.last_review

        watch_list_revisions = revisions(
            where=f"item_id = {item_id} AND mode_id = 4", order_by="revision_date ASC"
        )
        weeks_revision_excluded = week_column[len(watch_list_revisions) :]

        revision_count = get_mode_count(item_id, 4)

        if not is_graduated:
            due_day = day_diff(last_review, current_date)
        else:
            due_day = 0

        def render_checkbox(_):
            return Td(
                CheckboxX(
                    hx_post=f"/watch_list/add",
                    hx_vals={"item_id": item_id},
                    hx_include="#global_rating, #global_date",
                    hx_swap="outerHTML",
                    target_id=f"row-{item_id}",
                    hx_select=f"#row-{item_id}",
                ),
                cls="text-center",
            )

        def render_hyphen(_):
            return Td(
                Span("-"),
                cls="text-center",
            )

        def render_rev(rev: Revision):
            rev_date = rev.revision_date
            ctn = (
                render_rating(rev.rating).split()[0],
                (
                    f" {date_to_human_readable(rev_date)}"
                    if not (rev_date == current_date)
                    else None
                ),
            )
            return Td(
                (
                    A(
                        *ctn,
                        hx_get=f"/watch_list/edit/{rev.id}",
                        target_id="my-modal-body",
                        data_uk_toggle="target: #my-modal",
                        cls=AT.classic,
                    )
                    if not is_graduated
                    else Span(*ctn)
                ),
                cls="text-center",
            )

        if is_graduated or revision_count >= 7:
            due_day_message = ""
        elif due_day >= 7:
            due_day_message = due_day - 7
        else:
            due_day_message = "-"

        return Tr(
            Td(get_page_description(item_id), cls="sticky left-0 z-20 bg-white"),
            Td(get_start_text(item_id), cls=TextT.lg),
            Td(revision_count, cls="text-center"),
            Td(
                date_to_human_readable(hafiz_item.next_review)
                if (not is_graduated) and revision_count < 7
                else ""
            ),
            Td(due_day_message),
            Td(
                graduate_btn_watch_list(
                    item_id,
                    is_graduated=is_graduated,
                    is_disabled=(revision_count == 0),
                ),
                cls=(FlexT.block, FlexT.center, FlexT.middle, "min-h-11"),
            ),
            *map(render_rev, watch_list_revisions),
            *map(
                render_checkbox,
                ([weeks_revision_excluded.pop(0)] if due_day >= 7 else []),
            ),
            *map(render_hyphen, weeks_revision_excluded),
            id=f"row-{item_id}",
        )

    table = Table(
        Thead(
            Tr(
                Th("Pages", cls="min-w-28 sm:min-w-36 sticky left-0 z-20 bg-white"),
                Th("Start Text", cls="min-w-28"),
                Th("Count"),
                Th("Next Review", cls="min-w-28 "),
                Th("Due day"),
                Th("Graduate", cls="column_to_scroll"),
                *[Th(week, cls="!text-center sm:min-w-28") for week in week_column],
            )
        ),
        Tbody(*map(render_row, hafiz_items_data)),
        cls=(TableT.middle, TableT.divider, TableT.hover, TableT.sm, TableT.justify),
    )
    modal = ModalContainer(
        ModalDialog(
            ModalHeader(ModalCloseButton()),
            ModalBody(
                Div(id="my-modal-body"),
                data_uk_overflow_auto=True,
            ),
            ModalFooter(),
            cls="uk-margin-auto-vertical",
        ),
        id="my-modal",
    )

    content_body = Div(
        H2("Watch List"),
        Div(
            rating_dropdown(
                id="global_rating",
                cls="flex-1",
            ),
            LabelInput(
                "Revision Date",
                name="revision_date",
                type="date",
                value=current_date,
                id="global_date",
                cls="flex-1",
            ),
            cls=(FlexT.block, FlexT.middle, "w-full gap-3"),
        ),
        Div(
            table,
            modal,
            cls="uk-overflow-auto",
            id="watch_list_table_area",
        ),
        cls="text-xs sm:text-sm",
        # Currently this variable is not being used but it is needed for alpine js attributes
        x_data="{ showAll: false }",
    )

    return main_area(
        content_body,
        Script(src="/public/watch_list_logic.js"),
        active="Home",
        auth=auth,
    )


def watch_list_form(item_id: int, min_date: str, _type: str, auth):
    page = items[item_id].page_id
    current_date = get_current_date(auth)

    return Container(
        H1(get_page_description(item_id), f" - {items[item_id].start_text}"),
        Form(
            LabelInput(
                "Revision Date",
                name="revision_date",
                min=min_date,
                max=current_date,
                type="date",
                value=current_date,
            ),
            Hidden(name="id"),
            Hidden(name="page_no", value=page),
            Hidden(name="mode_id", value=4),
            Hidden(name="item_id", value=item_id),
            rating_radio(),
            Div(
                Button("Save", cls=ButtonT.primary),
                (
                    Button(
                        "Delete",
                        cls=ButtonT.destructive,
                        hx_delete=f"/watch_list",
                        hx_swap="none",
                    )
                    if _type == "edit"
                    else None
                ),
                A(
                    Button("Cancel", type="button", cls=ButtonT.secondary),
                    href=f"/watch_list",
                ),
                cls="flex justify-around items-center w-full",
            ),
            action=f"/watch_list/{_type}",
            method="POST",
        ),
        cls=("mt-5", ContainerT.xl, "space-y-3"),
    )


@watch_list_app.get("/edit/{rev_id}")
def watch_list_edit_form(rev_id: int, auth):
    current_revision = revisions[rev_id].__dict__
    current_revision["rating"] = str(current_revision["rating"])
    return fill_form(
        watch_list_form(current_revision["item_id"], "", "edit", auth), current_revision
    )


@watch_list_app.post("/edit")
def watch_list_edit_data(revision_details: Revision):
    revisions.update(revision_details)
    item_id = revision_details.item_id
    update_review_dates(item_id, 4)
    populate_hafizs_items_stat_columns(item_id=item_id)
    return RedirectResponse(f"/watch_list", status_code=303)


@watch_list_app.delete("/")
def watch_list_delete_data(id: int, item_id: int):
    revisions.delete(id)
    update_review_dates(item_id, 4)
    populate_hafizs_items_stat_columns(item_id=item_id)
    return Redirect("/watch_list")


@watch_list_app.post("/add")
def watch_list_add_data(revision_details: Revision, auth):
    revision_details.mode_id = 4
    revisions.insert(revision_details)
    item_id = revision_details.item_id

    revision_count = get_mode_count(item_id, 4)

    if revision_count > 6:
        graduate_the_item_id(item_id=item_id, mode_id=4, auth=auth)
        return RedirectResponse(f"/watch_list", status_code=303)

    update_review_dates(item_id, 4)
    populate_hafizs_items_stat_columns(item_id=item_id)

    return RedirectResponse("/watch_list", status_code=303)


@watch_list_app.post("/graduate")
def graduate_watch_list(item_id: int, auth, is_checked: bool = False):

    graduate_the_item_id(item_id=item_id, mode_id=4, auth=auth, checked=is_checked)

    return watch_list_view(auth), HtmxResponseHeaders(
        retarget=f"#row-{item_id}",
        reselect=f"#row-{item_id}",
        reswap="outerHTML",
    )
