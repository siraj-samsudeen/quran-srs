from fasthtml.common import *
from monsterui.all import *
from utils import *
from app.common_function import *
from app.revision_view import *
from app.revision_model import *
from globals import *

revision_app, rt = create_app_with_auth()


@rt("/entry")
def post(type: str, page: str, plan_id: int):
    if type == "bulk":
        return Redirect(f"/revision/bulk_add?page={page}&plan_id={plan_id}")
    elif type == "single":
        return Redirect(f"/revision/add?page={page}&plan_id={plan_id}")


@revision_app.get("/")
def revision(auth, idx: int | None = 1):
    return render_revision_table(auth, idx)


@rt("/edit/{revision_id}")
def get(revision_id: int, auth, req):
    current_revision = get_revision_by_id(revision_id).__dict__
    # Convert rating to string in order to make the `fill_form` to select the option.
    current_revision["rating"] = str(current_revision["rating"])
    item_id = current_revision["item_id"]
    form = create_revision_form(
        "edit", auth=auth, backlink=req.headers.get("referer", "/")
    )
    return main_area(
        Titled(
            (
                "Edit => ",
                get_page_description(item_id),
                f" - {items[item_id].start_text}",
            ),
            fill_form(form, current_revision),
        ),
        active="Revision",
        auth=auth,
    )


@rt("/edit")
def post(revision_details: Revision, backlink: str, auth):
    # setting the plan_id to None if it is 0
    # as it get defaults to 0 if the field is empty.
    revision_details.plan_id = set_zero_to_none(revision_details.plan_id)
    current_revision = update_revision(revision_details)
    update_stats_and_interval(
        item_id=current_revision.item_id,
        mode_id=current_revision.mode_id,
        current_date=get_current_date(auth),
    )
    return Redirect(backlink)


@rt("/delete/{revision_id}")
def delete(revision_id: int, auth):
    current_revision = get_revision_by_id(revision_id)
    delete_revision(revision_id)
    update_stats_and_interval(
        item_id=current_revision.item_id,
        mode_id=current_revision.mode_id,
        current_date=get_current_date(auth),
    )


@revision_app.delete("/")
def revision_delete_all(ids: List[int], auth):
    for id in ids:
        current_revision = revisions[id]
        revisions.delete(id)
        update_stats_and_interval(
            item_id=current_revision.item_id,
            mode_id=current_revision.mode_id,
            current_date=get_current_date(auth),
        )
    return RedirectResponse(revision, status_code=303)


# This is to handle the checkbox on revison page as it was coming as individual ids.
# eg: ids=1&ids=2&ids=3 -> ids=1,2,3
@revision_app.post("/bulk_edit")
def bulk_edit_redirect(ids: List[str]):
    return RedirectResponse(f"/revision/bulk_edit?ids={','.join(ids)}", status_code=303)


@revision_app.get("/bulk_edit")
def bulk_edit_view(ids: str, auth):
    ids = ids.split(",")

    # Sort the ids based on the page number
    ids.sort(key=lambda id: get_page_number(revisions[id].item_id))

    # Get the default values from the first selected revision
    first_revision = revisions[ids[0]]

    def _render_row(id):
        current_revision = revisions[id]
        current_item_id = current_revision.item_id
        item_details = items[current_item_id]
        return Tr(
            Td(get_page_description(current_item_id)),
            Td(P(item_details.start_text, cls=TextT.lg)),
            Td(
                CheckboxX(
                    name="ids",
                    value=id,
                    cls="revision_ids",
                    # _at_ is a alias for @ (alpine.js)
                    _at_click="handleCheckboxClick($event)",  # To handle `shift+click` selection
                )
            ),
            Td(
                rating_dropdown(
                    default_mode=str(current_revision.rating),
                    name=f"rating-{id}",
                    is_label=False,
                ),
                cls="min-w-32",
            ),
        )

    table = Table(
        Thead(
            Tr(
                Th("Page"),
                Th("Start Text"),
                Th(
                    CheckboxX(
                        cls="select_all",
                        x_model="selectAll",  # To update the current status of the checkbox (checked or unchecked)
                        _at_change="toggleAll()",  # based on that update the status of all the checkboxes
                    )
                ),
                Th("Rating"),
            )
        ),
        Tbody(*[_render_row(i) for i in ids]),
        x_data=select_all_checkbox_x_data(class_name="revision_ids"),
        # initializing the toggleAll function to select all the checkboxes by default.
        x_init="toggleAll()",
    )

    action_buttons = Div(
        Button("Save", cls=ButtonT.primary),
        Button(
            "Cancel", type="button", cls=ButtonT.secondary, onclick="history.back()"
        ),
        Button(
            "Delete",
            hx_delete="/revision/",
            hx_confirm="Are you sure you want to delete these revisions?",
            hx_target="body",
            hx_push_url="true",
            cls=ButtonT.destructive,
        ),
        cls=(FlexT.block, FlexT.around, FlexT.middle, "w-full"),
    )

    return main_area(
        H1("Bulk Edit Revision"),
        Form(
            Div(
                LabelInput(
                    "Revision Date",
                    name="revision_date",
                    type="date",
                    value=first_revision.revision_date,
                    cls="space-y-2 w-full",
                ),
            ),
            Div(table, cls="uk-overflow-auto"),
            action_buttons,
            action="/revision/",
            method="POST",
        ),
        active="Revision",
        auth=auth,
    )


@revision_app.post("/")
async def bulk_edit_save(revision_date: str, req, auth):
    form_data = await req.form()
    ids_to_update = form_data.getlist("ids")

    for name, value in form_data.items():
        if name.startswith("rating-"):
            current_id = name.split("-")[1]
            if current_id in ids_to_update:
                current_revision = update_revision(
                    Revision(
                        id=int(current_id),
                        rating=int(value),
                        revision_date=revision_date,
                    )
                )
                update_stats_and_interval(
                    item_id=current_revision.item_id,
                    mode_id=current_revision.mode_id,
                    current_date=get_current_date(auth),
                )

    return RedirectResponse("/revision/", status_code=303)


def parse_page_string(page_str: str):
    """
    Formats supported:
    - "5" -> (5, 0, 0)
    - "5.2" -> (5, 2, 0)
    - "5-10" -> (5, 0, 10)
    - "5.2-10" -> (5, 2, 10)
    """
    page = page_str
    part = 0
    length = 0

    # Extract length if present
    if "-" in page:
        page, length_str = page.split("-")
        length = int(length_str) if length_str else length

    # Extract part if present
    if "." in page:
        page, part_str = page.split(".")
        part = int(part_str) if part_str else part

    return int(page), part, length


def validate_page_revision(sess, item_id, page, plan_id):
    """Show error message for invalid inputs, such as pages already revised or not yet memorized"""
    if not hafizs_items(where=f"item_id = {item_id} AND memorized = 1"):
        error_toast(sess, f"Given page '{page}' is not yet memorized!")
        return False
    if revisions(where=f"item_id = {item_id} AND plan_id = {plan_id}"):
        error_toast(sess, f"Given page '{page}' is already revised under current plan!")
        return False
    return True


@rt("/add")
def get(
    auth,
    sess,
    plan_id: int,
    item_id: int = None,
    page: str = None,
    max_page: int = 605,
    date: str = None,
):
    if item_id is not None:
        page = get_page_number(item_id)
    elif page is not None:
        # for the single entry, we don't need to use length
        page, page_part, length = parse_page_string(page)
        if page >= max_page:
            return Redirect("/")
        item_list = get_item_ids_by_page(page)
        # To start the page from beginning even if there is multiple parts
        item_id = item_list[0]

        if page_part:
            if page_part == 0 or len(item_list) < page_part:
                item_id = item_list[0]
                return Redirect(
                    f"/revision/bulk_add?item_id={item_id}&plan_id={plan_id}&is_part=1"
                )
            else:
                current_page_part = get_items_by_page_id(page)
                # get the given page_part using index
                # eg: if page_part is 2 then it will get the first(2-1=1) index
                item_id = current_page_part[page_part - 1].id
        else:
            # Show all the parts if page_part is not specified in the input
            if len(item_list) > 1:
                return Redirect(
                    f"/revision/bulk_add?item_id={item_id}&plan_id={plan_id}&is_part=1"
                )
    else:
        return Redirect("/")
    if not validate_page_revision(sess, item_id, page, plan_id):
        return Redirect("/")
    return main_area(
        Titled(
            get_page_description(
                item_id, is_bold=False, custom_text=f" - {items[item_id].start_text}"
            ),
            fill_form(
                create_revision_form("add", auth=auth),
                {
                    "item_id": item_id,
                    "plan_id": plan_id,
                    "revision_date": date,
                },
            ),
        ),
        active="Home",
        auth=auth,
    )


@rt("/add")
def post(revision_details: Revision):
    # The id is set to zero in the form, so we need to delete it
    # before inserting to generate the id automatically
    del revision_details.id
    revision_details.plan_id = set_zero_to_none(revision_details.plan_id)
    revision_details.mode_id = FULL_CYCLE_MODE_ID

    item_id = revision_details.item_id

    rev = insert_revision(revision_details)
    populate_hafizs_items_stat_columns(item_id=item_id)

    next_item_id = find_next_memorized_item_id(item_id)

    next_page_item_ids = get_item_ids_by_page(get_page_number(next_item_id))
    is_next_page_is_part = len(next_page_item_ids) > 1

    if is_next_page_is_part:
        return Redirect(
            f"/revision/bulk_add?item_id={next_item_id}&revision_date={rev.revision_date}&plan_id={rev.plan_id}&is_part=1"
        )

    return Redirect(
        f"/revision/add?item_id={find_next_memorized_item_id(item_id)}&date={rev.revision_date}&plan_id={rev.plan_id}"
    )


# This is to update the rating from the summary tables
@revision_app.put("/{rev_id}")
def update_revision_rating(rev_id: int, rating: int):
    update_revision_rating_only(rev_id, rating)


@revision_app.get("/bulk_add")
def get(
    auth,
    sess,
    plan_id: int,
    item_id: int = None,
    page: str = None,
    length: int = 0,
    # is_part is to determine whether it came from single entry page or not
    is_part: bool = False,
    revision_date: str = None,
    max_item_id: int = get_last_item_id(),
    max_page_id: int = 605,
):
    if revision_date is None:
        revision_date = get_current_date(auth)

    if not length or length < 0:
        length = get_full_cycle_daily_limit(auth)

    if item_id is not None:
        page = get_page_number(item_id)
        item_id = get_item_ids_by_page(page)[0]
    elif page is not None:
        page, part, length = parse_page_string(page)

        if page >= max_page_id:
            return Redirect("/")

        # TODO: Later: handle this in the parse_page_string function
        if not length or length <= 0:
            length = int(get_full_cycle_daily_limit(auth))

        item_list = get_item_ids_by_page(page)
        item_id = item_list[0]

        if part:
            if part == 0 or len(item_list) < part:
                item_id = item_id
            else:
                current_page_part = get_items_by_page_id(page)
                item_id = current_page_part[part - 1].id

    if not validate_page_revision(sess, item_id, page, plan_id):
        return Redirect("/")
    # This is to show only one page if it came from single entry
    if is_part:
        length = 1

    def get_item_ids_from_page_start(auth, plan_id, start_page, length):
        """Returns a list of unrevised and memorized item IDs for a specific user,
        starting from a given page number with given length."""
        qry = f"""
        SELECT hafizs_items.item_id, hafizs_items.page_number
        FROM hafizs_items
        LEFT JOIN revisions ON revisions.item_id = hafizs_items.item_id AND revisions.plan_id = {plan_id} AND revisions.hafiz_id = {auth}
        WHERE hafizs_items.memorized = 1 AND hafizs_items.hafiz_id = {auth} AND revisions.item_id IS NULL AND hafizs_items.page_number >= {start_page}
        ORDER BY hafizs_items.page_number ASC
        LIMIT {length};
        """
        rows = db.q(qry)
        return [row["item_id"] for row in rows]

    item_ids = get_item_ids_from_page_start(
        auth=auth, plan_id=plan_id, start_page=page, length=length
    )

    # To start from the not added item id
    if item_id in item_ids:
        item_ids = item_ids[item_ids.index(item_id) :]

    # This is to set the upper limit for continuation logic
    # To prevent the user from adding already added pages twice
    if max_item_id in item_ids:
        if not item_ids[-1] == max_item_id:
            item_ids = item_ids[: item_ids.index(max_item_id)]

    _temp_item_ids = []
    page_surah = get_surah_name(item_id=item_id)
    page_juz = get_juz_name(item_id=item_id)

    for _item_id in item_ids:
        current_surah = get_surah_name(item_id=_item_id)
        current_juz = get_juz_name(item_id=_item_id)

        if current_surah != page_surah and current_juz != page_juz:
            _temp_item_ids.append(f"{page_surah} surah and Juz {page_juz} ends")
            page_surah, page_juz = current_surah, current_juz
        elif current_surah != page_surah:
            _temp_item_ids.append(f"{page_surah} surah ends")
            page_surah = current_surah
        elif current_juz != page_juz:
            _temp_item_ids.append(f"Juz {page_juz} ends")
            page_juz = current_juz

        _temp_item_ids.append(_item_id)

    if _temp_item_ids:
        item_ids = _temp_item_ids

    def _render_row(current_item_id):
        if isinstance(current_item_id, str):
            return Tr(Td(P(current_item_id), colspan="5", cls="text-center"))

        current_page_details = items[current_item_id]
        return Tr(
            Td(get_page_description(current_item_id)),
            Td(P(current_page_details.start_text, cls=(TextT.lg))),
            Td(
                CheckboxX(
                    name="ids",
                    value=current_item_id,
                    cls="revision_ids",
                    _at_click="handleCheckboxClick($event)",
                )
            ),
            Td(
                rating_dropdown(is_label=False, name=f"rating-{current_item_id}"),
                cls="!pr-0 min-w-32",
            ),
        )

    table = Table(
        Thead(
            Tr(
                Th("Page"),
                Th("Start Text"),
                Th(
                    CheckboxX(
                        cls="select_all", x_model="selectAll", _at_change="toggleAll()"
                    )
                ),
                Th("Rating"),
            )
        ),
        Tbody(*map(_render_row, item_ids)),
        x_data=select_all_checkbox_x_data(
            class_name="revision_ids",
            is_select_all="false" if is_part else "true",
        ),
        x_init="toggleAll()",
    )

    action_buttons = Div(
        Button(
            "Save",
            cls=ButtonT.primary,
        ),
        A(Button("Cancel", type="button", cls=ButtonT.secondary), href="/"),
        cls=(FlexT.block, FlexT.around, FlexT.middle, "w-full"),
    )

    def get_description(type):
        get_type_function = {
            "surah": get_surah_name,
            "juz": get_juz_name,
            "page": get_page_number,
        }
        if type not in get_type_function.keys():
            return ""

        unique_type = list(
            dict.fromkeys(
                [
                    get_type_function[type](item_id=item_id)
                    for item_id in item_ids
                    if isinstance(item_id, int)
                ]
            )
        )
        if len(unique_type) == 1:
            return unique_type[0]
        else:
            return f"{unique_type[0]} => {unique_type[-1]}"

    surah_description = get_description("surah")
    juz_description = get_description("juz")
    page_description = get_description("page")

    return main_area(
        Div(
            # This will show in the desktop view
            H1(
                f"{page_description} - {surah_description} - Juz {juz_description}",
                cls="hidden md:block",
            ),
            # This will show in the mobile view
            Div(
                H2(page_description),
                H2(surah_description),
                H2(f"Juz {juz_description}"),
                cls="[&>*]:font-extrabold space-y-2 block md:hidden",
            ),
            id="header_area",
        ),
        Form(
            Hidden(name="is_part", value=str(is_part)),
            Hidden(name="plan_id", value=plan_id),
            Hidden(name="max_item_id", value=max_item_id),
            LabelInput(
                "Revision Date",
                name="revision_date",
                type="date",
                value=revision_date,
                cls=("space-y-2 col-span-2"),
            ),
            Div(table, cls="uk-overflow-auto", id="table-container"),
            action_buttons,
            action="/revision/bulk_add",
            method="POST",
            onkeydown="if(event.key === 'Enter') event.preventDefault();",
        ),
        Script(src="/public/script.js"),
        active="Home",
        auth=auth,
    )


@rt("/bulk_add")
async def post(
    revision_date: str,
    plan_id: int,
    is_part: bool,
    max_item_id: int,
    auth,
    req,
    length: int = 0,
):
    plan_id = set_zero_to_none(plan_id)
    form_data = await req.form()
    item_ids = form_data.getlist("ids")

    parsed_data = []
    for name, value in form_data.items():
        if name.startswith("rating-"):
            item_id = name.split("-")[1]
            if item_id in item_ids:
                hafizs_items_id = get_hafiz_item_by_item_id(item_id).id
                parsed_data.append(
                    Revision(
                        item_id=int(item_id),
                        rating=int(value),
                        hafiz_id=auth,
                        revision_date=revision_date,
                        mode_id=FULL_CYCLE_MODE_ID,
                        plan_id=plan_id,
                    )
                )

    insert_revisions_bulk(parsed_data)

    for rec in parsed_data:
        populate_hafizs_items_stat_columns(item_id=rec.item_id)

    if parsed_data:
        last_item_id = parsed_data[-1].item_id
    else:
        # If none were selected, then navigate to next set of pages
        rating_date = [
            name for name, value in form_data.items() if name.startswith("rating-")
        ][::-1]
        if rating_date:
            last_item_id = int(rating_date[0].split("-")[1])
        else:
            return Redirect("/")

    next_item_id = find_next_memorized_item_id(last_item_id)

    # To handle the upper limit
    if next_item_id is None or next_item_id >= max_item_id:
        return Redirect("/")

    next_page_item_ids = get_item_ids_by_page(get_page_number(next_item_id))
    is_next_page_is_part = len(next_page_item_ids) > 1
    if is_part and not is_next_page_is_part:
        return Redirect(
            f"/revision/add?item_id={next_item_id}&date={revision_date}&plan_id={plan_id}"
        )

    if is_part and is_next_page_is_part:
        return Redirect(
            f"/revision/bulk_add?item_id={next_item_id}&revision_date={revision_date}&plan_id={plan_id}&is_part=1"
        )
    return Redirect(
        f"/revision/bulk_add?item_id={next_item_id}&revision_date={revision_date}&length={length}&plan_id={plan_id}&max_item_id={max_item_id}"
    )
