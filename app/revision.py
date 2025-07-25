from fasthtml.common import *
from monsterui.all import *
from utils import *
from app.common_function import *

db = get_database_connection()

revisions = db.t.revisions
items = db.t.items
hafizs_items = db.t.hafizs_items
pages = db.t.pages

(Revision, Item, Hafiz_Items, Page) = (
    revisions.dataclass(),
    items.dataclass(),
    hafizs_items.dataclass(),
    pages.dataclass(),
)

revision_app, rt = create_app_with_auth()


def update_stats_and_interval(item_id: int, mode_id: int, current_date: str):
    populate_hafizs_items_stat_columns(item_id=item_id)
    if mode_id == 5:
        recalculate_intervals_on_srs_records(item_id=item_id, current_date=current_date)


def get_item_id(page_number: int, not_memorized_only: bool = False):
    """
    This function will lookup the page_number in the `hafizs_items` table
    if there is no record for that page and then create new records for that page
    by looking up the `items` table

    Each page may contain more than one record (including the page_part)

    Then filter out the in_active hafizs_items and return the item_id

    Returns:
    list of item_id
    """

    qry = f"page_number = {page_number}"
    hafiz_data = hafizs_items(where=qry)

    if not hafiz_data:
        page_items = items(where=f"page_id = {page_number} AND active = 1")
        for item in page_items:
            hafizs_items.insert(
                Hafiz_Items(
                    item_id=item.id,
                    page_number=item.page_id,
                    mode_id=1,
                )
            )
    hafiz_data = (
        # Filtered only `Not Started`
        hafizs_items(where=f"{qry} AND status_id = 6")
        if not_memorized_only
        else hafizs_items(where=qry)
    )
    item_ids = [
        hafiz_item.item_id
        for hafiz_item in hafiz_data
        if items[hafiz_item.item_id].active
    ]
    return sorted(item_ids)


def action_buttons():
    # Enable and Disable the button based on the checkbox selection in the revision table
    dynamic_enable_button_hyperscript = "on checkboxChanged if first <input[type=checkbox]:checked/> remove @disabled else add @disabled"
    import_export_buttons = DivLAligned(
        Button(
            "Bulk Edit",
            hx_post="/revision/bulk_edit",
            hx_push_url="true",
            hx_include="closest form",
            hx_target="body",
            cls="toggle_btn",  # To disable and enable the button based on the checkboxes (Don't change, it is referenced in hyperscript)
            disabled=True,
            _=dynamic_enable_button_hyperscript,
        ),
        Button(
            "Bulk Delete",
            hx_delete="/revision",
            hx_confirm="Are you sure you want to delete these revisions?",
            hx_target="body",
            cls=("toggle_btn", ButtonT.destructive),
            disabled=True,
            _=dynamic_enable_button_hyperscript,
        ),
        A(
            Button("Export", type="button"),
            href="tables/revisions/export",
            hx_boost="false",
        ),
    )
    return DivFullySpaced(
        Div(),
        import_export_buttons,
        cls="flex-wrap gap-4 mb-3",
    )


@rt("/entry")
def post(type: str, page: str, plan_id: int):
    print(plan_id)
    if type == "bulk":
        return Redirect(f"/revision/bulk_add?page={page}&plan_id={plan_id}")
    elif type == "single":
        return Redirect(f"/revision/add?page={page}&plan_id={plan_id}")


# this function is used to create infinite scroll for the revisions table
def generate_revision_table_part(part_num: int = 1, size: int = 20) -> Tuple[Tr]:
    start = (part_num - 1) * size
    end = start + size
    data = revisions(order_by="id desc")[start:end]

    def _render_rows(rev: Revision):
        item_id = rev.item_id
        item_details = items[item_id]
        page = item_details.page_id
        return Tr(
            Td(
                CheckboxX(
                    name="ids",
                    value=rev.id,
                    cls="revision_ids",
                    # To trigger the checkboxChanged event to the bulk edit and bulk delete buttons
                    _="on click send checkboxChanged to .toggle_btn",
                    _at_click="handleCheckboxClick($event)",
                )
            ),
            Td(
                A(
                    page,
                    href=f"/revision/edit/{rev.id}",
                    cls=AT.muted,
                )
            ),
            Td(item_details.part),
            Td(rev.mode_id),
            Td(rev.plan_id),
            Td(render_rating(rev.rating)),
            Td(get_surah_name(item_id=item_id)),
            Td(pages[page].juz_number),
            Td(date_to_human_readable(rev.revision_date)),
            Td(
                A(
                    "Delete",
                    hx_delete=f"/revision/delete/{rev.id}",
                    target_id=f"revision-{rev.id}",
                    hx_swap="outerHTML",
                    hx_confirm="Are you sure?",
                    cls=AT.muted,
                ),
            ),
            id=f"revision-{rev.id}",
        )

    paginated = [_render_rows(i) for i in data]

    if len(paginated) == 20:
        paginated[-1].attrs.update(
            {
                "get": f"revision?idx={part_num + 1}",
                "hx-trigger": "revealed",
                "hx-swap": "afterend",
                "hx-select": "tbody > tr",
            }
        )
    return tuple(paginated)


@revision_app.get
def revision(auth, idx: int | None = 1):
    table = Table(
        Thead(
            Tr(
                Th(),  # empty header for checkbox
                Th("Page"),
                Th("Part"),
                Th("Mode"),
                Th("Plan Id"),
                Th("Rating"),
                Th("Surah"),
                Th("Juz"),
                Th("Revision Date"),
                Th("Action"),
            )
        ),
        Tbody(*generate_revision_table_part(part_num=idx)),
        x_data=select_all_checkbox_x_data(class_name="revision_ids"),
    )
    return main_area(
        # To send the selected revision ids for bulk delete and bulk edit buttons
        Form(
            action_buttons(),
            Div(table, cls="uk-overflow-auto"),
        ),
        active="Revision",
        auth=auth,
    )


def create_revision_form(type, auth, backlink="/"):

    def _option(obj):
        return Option(
            f"{obj.id} ({obj.name})",
            value=obj.id,
            # FIXME: Temp condition for selecting siraj, later it should be handled by sess
            # Another caviat is that siraj should be in the top of the list of users
            # or else the edit functionality will not work properly.
            selected=True if "siraj" in obj.name.lower() else False,
        )

    additional_fields = (
        LabelInput(
            "Revision Date",
            name="revision_date",
            type="date",
            value=get_current_date(auth),
            cls="space-y-2 col-span-2",
        ),
    )

    return Form(
        Hidden(name="id"),
        Hidden(name="item_id"),
        Hidden(name="plan_id"),
        # Hide the User selection temporarily
        LabelSelect(
            *map(_option, hafizs()), label="Hafiz Id", name="hafiz_id", cls="hidden"
        ),
        *additional_fields,
        rating_radio(),
        Div(
            Button("Save", name="backlink", value=backlink, cls=ButtonT.primary),
            A(Button("Cancel", type="button", cls=ButtonT.secondary), href=backlink),
            cls="flex justify-around items-center w-full",
        ),
        action=f"/revision/{type}",
        method="POST",
    )


@rt("/edit/{revision_id}")
def get(revision_id: int, auth, req):
    current_revision = revisions[revision_id].__dict__
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
    current_revision = revisions.update(revision_details)
    update_stats_and_interval(
        item_id=current_revision.item_id,
        mode_id=current_revision.mode_id,
        current_date=get_current_date(auth),
    )
    return Redirect(backlink)


@rt("/delete/{revision_id}")
def delete(revision_id: int, auth):
    current_revision = revisions[revision_id]
    revisions.delete(revision_id)
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
            hx_delete="/revision",
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
            action="/revision",
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
                current_revision = revisions.update(
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

    return RedirectResponse("/revision", status_code=303)


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


@rt("/add")
def get(
    auth,
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
        item_list = get_item_id(page_number=page)
        # To start the page from beginning even if there is multiple parts
        item_id = item_list[0]

        if page_part:
            if page_part == 0 or len(item_list) < page_part:
                item_id = item_list[0]
                return Redirect(
                    f"/revision/bulk_add?item_id={item_id}&plan_id={plan_id}&is_part=1"
                )
            else:
                current_page_part = items(where=f"page_id = {page} and active = 1")
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
    revision_details.mode_id = 1

    item_id = revision_details.item_id

    # Even if the item_id is in other mode, if the records is added then it is considered as a 'memorised'
    hafizs_items_id = hafizs_items(where=f"item_id = {item_id}")[0].id
    hafizs_items.update({"status_id": 1}, hafizs_items_id)

    rev = revisions.insert(revision_details)
    populate_hafizs_items_stat_columns(item_id=item_id)

    next_item_id = find_next_item_id(item_id)

    next_page_item_ids = get_item_id(page_number=get_page_number(next_item_id))
    is_next_page_is_part = len(next_page_item_ids) > 1

    if is_next_page_is_part:
        return Redirect(
            f"/revision/bulk_add?item_id={next_item_id}&revision_date={rev.revision_date}&plan_id={rev.plan_id}&is_part=1"
        )

    return Redirect(
        f"/revision/add?item_id={find_next_item_id(item_id)}&date={rev.revision_date}&plan_id={rev.plan_id}"
    )


# This is to update the rating from the summary tables
@revision_app.put("/{rev_id}")
def update_revision_rating(rev_id: int, rating: int):
    revisions.update({"rating": rating}, rev_id)

    current_revision = revisions[rev_id]
    item_id = current_revision.item_id
    if current_revision.mode_id == 5:
        next_interval = get_interval_based_on_rating(item_id, rating, is_edit=True)

        # next_interval column only change based on the rating
        revisions.update({"next_interval": next_interval}, rev_id)

        current_hafiz_item = get_hafizs_items(item_id)
        current_hafiz_item.next_interval = next_interval
        current_hafiz_item.next_review = add_days_to_date(
            current_revision.revision_date, next_interval
        )
        hafizs_items.update(current_hafiz_item)
    populate_hafizs_items_stat_columns(item_id=item_id)


@revision_app.get("/bulk_add")
def get(
    auth,
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
        length = get_display_count(auth)

    if item_id is not None:
        page = get_page_number(item_id)
        item_id = get_item_id(page_number=page)[0]
    elif page is not None:
        page, part, length = parse_page_string(page)

        if page >= max_page_id:
            return Redirect("/")

        # TODO: Later: handle this in the parse_page_string function
        if not length or length <= 0:
            length = int(get_display_count(auth))

        item_list = get_item_id(page_number=page)
        item_id = item_list[0]

        if part:
            if part == 0 or len(item_list) < part:
                item_id = item_id
            else:
                current_page_part = items(where=f"page_id = {page} and active = 1")
                item_id = current_page_part[part - 1].id

    # This is to show only one page if it came from single entry
    if is_part:
        length = 1

    last_page = page + length

    item_ids = flatten_list(
        [get_item_id(page_number=p) for p in range(page, last_page)]
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
                hafizs_items_id = hafizs_items(where=f"item_id = {item_id}")[0].id
                hafizs_items.update({"status_id": 1}, hafizs_items_id)
                parsed_data.append(
                    Revision(
                        item_id=int(item_id),
                        rating=int(value),
                        hafiz_id=auth,
                        revision_date=revision_date,
                        mode_id=1,
                        plan_id=plan_id,
                    )
                )

    revisions.insert_all(parsed_data)

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

    next_item_id = find_next_item_id(last_item_id)

    # To handle the upper limit
    if next_item_id is None or next_item_id >= max_item_id:
        return Redirect("/")

    next_page_item_ids = get_item_id(page_number=get_page_number(next_item_id))
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
