from fasthtml.common import *
from monsterui.all import *
from utils import *
from app.common_function import *
from globals import *

DEFAULT_RATINGS = {
    "new_memorization": 1,
}

profile_app, rt = create_app_with_auth()


def memorized_checkbox(items):
    if not items:
        status = False
    else:
        num_memorized = sum(item.get("memorized", 0) for item in items)
        total_items = len(items)

        if num_memorized == total_items:
            status = True
        elif num_memorized == 0:
            status = False
        else:
            status = None  # Indeterminate

    return CheckboxX(
        name="selected_memorized_status",
        checked=status,
        cls=(
            "bg-[image:var(--uk-form-checkbox-image-indeterminate)]"
            if status is None
            else ""
        ),
    )


def render_type_description(list, _type=""):
    first_description = list[0]
    last_description = list[-1]

    if _type == "Surah":
        _type = ""
        first_description = surahs[first_description].name
        last_description = surahs[last_description].name

    if len(list) == 1:
        return f"{_type} {first_description}"
    return (
        f"{_type}{"" if _type == "" else "s"} {first_description} – {last_description}"
    )


@profile_app.get("/{current_type}")
def show_page_status(current_type: str, auth, status: str = ""):
    memorized_filter = None  # Initially we didn't apply filter
    if status == "memorized":
        memorized_filter = True
    elif status == "not_memorized":
        memorized_filter = False

    def render_row_based_on_type(type_number: str, records: list, current_type):
        memorized_value = records[0]["memorized"]
        if memorized_filter is not None and memorized_filter != memorized_value:
            return None

        _surahs = sorted({r["surah_id"] for r in records})
        _pages = sorted([r["page_number"] for r in records])
        _juzs = sorted({r["juz_number"] for r in records})

        surah_range = render_type_description(_surahs, "Surah")
        page_range = render_type_description(_pages, "Page")
        juz_range = render_type_description(_juzs, "Juz")

        if current_type == "juz":
            details = [surah_range, page_range]
            details_str = f"{surah_range} ({page_range})"
        elif current_type == "surah":
            details = [juz_range, page_range]
            details_str = f"{juz_range} ({page_range})"
        elif current_type == "page":
            details = [juz_range, surah_range]
            details_str = f"{juz_range} | {surah_range}"

        title = (
            f"{current_type.capitalize()} {type_number}"
            if current_type != "surah"
            else surahs[type_number].name
        )
        item_length = 1

        memorized_filter_str = f"memorized = {memorized_value}"

        if current_type == "page":
            where_clause = f"page_number={type_number} and hafiz_id={auth}"
            if status:
                where_clause += f" and {memorized_filter_str}"
            item_length = len(hafizs_items(where=where_clause) or [])

        elif current_type in ("surah", "juz"):
            item_ids = grouped.get(type_number, [])
            if item_ids:
                if len(item_ids) > 1:
                    item_id_list = ",".join(str(i["id"]) for i in item_ids)
                    where_clause = f"item_id IN ({item_id_list}) and hafiz_id={auth}"
                    if status:
                        where_clause += f" and {memorized_filter_str}"
                    item_length = len(hafizs_items(where=where_clause) or [])

        show_customize_button = item_length > 1
        return Tr(
            Td(title),
            Td(details[0]),
            Td(details[1]),
            Td(
                Form(
                    Hidden(name="filter_status", value=status),
                    memorized_checkbox(records),
                    hx_post=f"/profile/update_status/{current_type}/{type_number}",
                    hx_target=f"#{current_type}-{type_number}",
                    hx_select=f"#{current_type}-{type_number}",
                    hx_select_oob="#stats_info",
                    hx_swap="outerHTML",
                    hx_trigger="change",
                )
            ),
            (
                Td(
                    A("Customize ➡️"),
                    cls=(AT.classic, "text-right"),
                    hx_get=f"/profile/custom_status_update/{current_type}/{type_number}"
                    + (f"?status={status}" if status else ""),
                    hx_vals={
                        "title": title,
                        "description": details_str,
                        "filter_status": status,
                    },
                    target_id="my-modal-body",
                    data_uk_toggle="target: #my-modal",
                )
                if show_customize_button
                else Td("")
            ),
            id=f"{current_type}-{type_number}",
            data_testid=f"{current_type}-{type_number}-row",
        )

    if not current_type:
        current_type = "juz"

    def render_navigation_item(_type: str):
        return Li(
            A(
                f"by {_type}",
                href=f"/profile/{_type}" + (f"?status={status}" if status else ""),
            ),
            cls=("uk-active" if _type == current_type else None),
        )

    qry = f"""SELECT items.id, items.surah_id, pages.page_number, pages.juz_number, hafizs_items.memorized FROM items 
                          LEFT JOIN pages ON items.page_id = pages.id
                          LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
                          WHERE items.active != 0;"""
    if status in ["memorized", "not_memorized"]:
        memorized_condition = f" AND hafizs_items.memorized = {memorized_filter}"
    else:
        memorized_condition = ""
    query_with_status = qry.replace(";", f" {memorized_condition};")

    qry_data = db.q(query_with_status if status else qry)

    grouped = group_by_type(qry_data, current_type)
    rows = [
        render_row_based_on_type(type_number, records, current_type)
        for type_number, records in grouped.items()
    ]

    def render_filter_btn(text):
        return Label(
            text,
            hx_get=f"/profile/{current_type}?status={standardize_column(text)}",
            hx_target="body",
            hx_push_url="true",
            cls=(
                "cursor-pointer",
                (
                    LabelT.primary
                    if status == standardize_column(text)
                    else LabelT.secondary
                ),
            ),
        )

    filter_btns = DivLAligned(
        P("Status Filter:", cls=TextPresets.muted_sm),
        *map(
            render_filter_btn,
            ["Memorized", "Not Memorized"],
        ),
        (
            Label(
                "X",
                hx_get=f"/profile/{current_type}",
                hx_target="body",
                hx_push_url="true",
                cls=(
                    "cursor-pointer",
                    TextT.xs,
                    LabelT.destructive,
                    (None if status else "invisible"),
                ),
            )
        ),
    )

    # For memorization progress
    unfiltered_data = db.q(qry)
    page_stats = defaultdict(lambda: {"memorized": 0, "total": 0})
    for item in unfiltered_data:
        page = item["page_number"]
        page_stats[page]["total"] += 1
        if item["memorized"]:
            page_stats[page]["memorized"] += 1

    total_memorized_pages = 0
    for page, stats in page_stats.items():
        total_memorized_pages += stats["memorized"] / stats["total"]

    progress_bar_with_stats = (
        DivCentered(
            P(
                f"Memorization Progress: {format_number(total_memorized_pages)}/604 Pages ({int(total_memorized_pages/604*100)}%)",
                cls="font-bold text-sm sm:text-lg ",
            ),
            Progress(value=f"{total_memorized_pages}", max="604"),
            cls="space-y-2",
            id="stats_info",
        ),
    )

    modal = Div(
        ModalContainer(
            ModalDialog(
                ModalHeader(
                    ModalTitle(id="my-modal-title"),
                    P(cls=TextPresets.muted_sm, id="my-modal-description"),
                    ModalCloseButton(),
                    cls="space-y-3",
                ),
                Form(
                    ModalBody(
                        Div(id="my-modal-body"),
                        data_uk_overflow_auto=True,
                    ),
                    ModalFooter(
                        Div(id="my-modal-footer"),
                    ),
                    Div(id="my-modal-link"),
                ),
                cls="uk-margin-auto-vertical",
            ),
            id="my-modal",
        ),
        id="modal-container",
    )

    type_details = {
        "page": ["Juz", "Surah"],
        "surah": ["Juz", "Page"],
        "juz": ["Surah", "Page"],
    }

    details = type_details.get(current_type, ["", ""])
    return main_area(
        Div(
            progress_bar_with_stats,
            DividerLine(),
            DivFullySpaced(
                filter_btns,
            ),
            Div(
                TabContainer(
                    *map(render_navigation_item, ["juz", "surah", "page"]),
                ),
                Div(
                    Table(
                        Thead(
                            Tr(
                                Th(current_type.title()),
                                *map(Th, details),
                                Th("Status"),
                                Th(""),
                            )
                        ),
                        Tbody(*rows),
                        x_data=select_all_checkbox_x_data(
                            class_name="profile_rows", is_select_all="false"
                        ),
                        x_init="updateSelectAll()",
                    ),
                    cls="h-[68vh] overflow-auto uk-overflow-auto",
                ),
                cls="space-y-5",
            ),
            Div(modal),
            cls="space-y-5",
        ),
        auth=auth,
        active="Memorization Status",
    )


@profile_app.get("/custom_status_update/{current_type}/{type_number}")
def load_descendant_items_for_profile(
    current_type: str,
    type_number: int,
    title: str,
    description: str,
    filter_status: str,
    auth,
    status: str = None,
):
    memorized_filter = None
    if status == "memorized":
        memorized_filter = True
    elif status == "not_memorized":
        memorized_filter = False

    if current_type == "juz":
        condition = f"pages.juz_number = {type_number}"
    elif current_type == "surah":
        condition = f"items.surah_id = {type_number}"
    elif current_type == "page":
        condition = f"pages.page_number = {type_number}"
    else:
        return "Invalid current_type"
    qry = f"""SELECT items.id, items.surah_id, pages.page_number, pages.juz_number, hafizs_items.memorized FROM items 
                          LEFT JOIN pages ON items.page_id = pages.id
                          LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
                          WHERE items.active != 0 AND {condition};"""

    if memorized_filter is not None:
        qry = qry.replace(";", f" AND hafizs_items.memorized = {memorized_filter};")
    ct = db.q(qry)

    def render_row(record):
        current_memorized_status = record["memorized"]
        current_id = record["id"]
        return Tr(
            Td(
                # This hidden input is to send the id to the backend even if it is unchecked
                Hidden(name=f"id-{current_id}", value="0"),
                CheckboxX(
                    name=f"id-{current_id}",
                    value="1",
                    checked=current_memorized_status,
                    cls="partial_rows",  # Alpine js reference
                    _at_click="handleCheckboxClick($event)",
                ),
            ),
            Td(record["page_number"]),
            Td(surahs[record["surah_id"]].name),
            Td(f"Juz {record['juz_number']}"),
            Td("Memorized" if current_memorized_status else "Not Memorized"),
        )

    table = Table(
        Thead(
            Tr(
                Th(
                    CheckboxX(
                        cls="select_all",
                        x_model="selectAll",
                        _at_change="toggleAll()",
                    )
                ),
                Th("Page"),
                Th("Surah"),
                Th("Juz"),
                Th("Status"),
            )
        ),
        Tbody(*map(render_row, ct)),
        x_data=select_all_checkbox_x_data(
            class_name="partial_rows", is_select_all="false"
        ),
        x_init="updateSelectAll()",
        id="filtered-table",
    )
    base = f"/profile/custom_status_update/{current_type}"
    if type_number is not None:
        base += f"/{type_number}"
    query = f"?status={status}&" if status else "?"
    query += f"title={title}&description={description}&filter_status={filter_status}"

    link = base + query

    def update_button(label, value, hx_select_id, hx_select_oob_id="", cls=""):
        return Button(
            label,
            hx_post=link,
            hx_select=hx_select_id,
            hx_target=hx_select_id,
            hx_swap="outerHTML",
            hx_select_oob=hx_select_oob_id,
            name="action",
            value=value,
            cls=("bg-green-600 text-white", cls),
        )

    return (
        table,
        ModalTitle(
            "" if title == "" else f"{title} - Select Memorized Page",
            id="my-modal-title",
            hx_swap_oob="true",
        ),
        P(
            description,
            id="my-modal-description",
            hx_swap_oob="true",
            cls=TextPresets.muted_lg,
        ),
        Div(
            update_button(
                label="Update and Close",
                value="close",
                hx_select_id=f"#{current_type}-{type_number}",
                hx_select_oob_id=f"#stats_info",
                cls="uk-modal-close",
            ),
            update_button(
                label="Update and Stay",
                value="stay",
                hx_select_id="#filtered-table",
                hx_select_oob_id="#filtered-table",
            ),
            Button("Cancel", cls=("bg-red-600 text-white", "uk-modal-close")),
            id="my-modal-footer",
            hx_swap_oob="true",
            cls=("space-x-2", "space-y-2"),
        ),
    )


@profile_app.post("/update_status/{current_type}/{type_number}")
def profile_page_status_update(
    current_type: str,
    type_number: int,
    req: Request,
    auth,
    selected_memorized_status: str = "off",
):
    selected_memorized_status = selected_memorized_status == "on"
    qry = f"""SELECT items.id, items.surah_id, pages.page_number, pages.juz_number FROM items 
                          LEFT JOIN pages ON items.page_id = pages.id
                          WHERE items.active != 0;"""
    ct = db.q(qry)
    is_newly_memorized = selected_memorized_status == False
    grouped = group_by_type(ct, current_type, feild="id")

    for item_id in grouped[type_number]:
        current_item = hafizs_items(where=f"item_id = {item_id} and hafiz_id = {auth}")
        current_item = current_item[0]
        hafizs_items.update({"memorized": selected_memorized_status}, current_item.id)
    referer = req.headers.get("referer", "/")
    return RedirectResponse(referer, status_code=303)


@profile_app.post("/custom_status_update/{current_type}/{type_number}")
async def profile_page_custom_status_update(
    current_type: str,
    type_number: int,
    req: Request,
    title: str,
    description: str,
    filter_status: str,
    action: str,
    auth,
    status: str = None,
):
    form_data = await req.form()

    item_statuses = {}
    for key in form_data:
        if key.startswith("id-"):
            try:
                item_id = int(key.split("-")[1])
                status_val = form_data.get(key) == "1"
                item_statuses[item_id] = status_val
            except (IndexError, ValueError):
                continue

    for item_id, new_memorized_status in item_statuses.items():
        current_item_list = hafizs_items(
            where=f"item_id = {item_id} and hafiz_id = {auth}"
        )

        current_memorized_status = None
        hafiz_item_id = None
        if current_item_list:
            current_item = current_item_list[0]
            current_memorized_status = current_item.memorized
            hafiz_item_id = current_item.id

        if new_memorized_status == current_memorized_status:
            continue  # No change

        if hafiz_item_id is None:
            # It doesn't exist, so we should create it.
            hafizs_items.insert(
                item_id=item_id, hafiz_id=auth, memorized=new_memorized_status
            )
        else:
            hafizs_items.update({"memorized": new_memorized_status}, hafiz_item_id)

    query_string = f"?status={status}&" if status else "?"
    query_string += (
        f"title={title}&description={description}&filter_status={filter_status}"
    )
    stay_url = (
        f"/profile/custom_status_update/{current_type}/{type_number}{query_string}"
    )
    close_url = f"/profile/{current_type}{query_string}"
    if action == "stay":
        return RedirectResponse(stay_url, status_code=303)
    elif action == "close":
        return RedirectResponse(close_url, status_code=303)
    else:
        return Redirect(close_url)
