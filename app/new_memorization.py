from fasthtml.common import *
from monsterui.all import *
from utils import *
from datetime import datetime
from app.common_function import *

DEFAULT_RATINGS = {
    "new_memorization": 1,
}


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

new_memorization_app, rt = create_app_with_auth()


def get_closest_unmemorized_item_id(auth, last_newly_memorized_item_id: int):
    not_memorized = get_not_memorized_records(auth)
    grouped_by_item_id = group_by_type(not_memorized, "id")
    not_memorized_item_ids = list(grouped_by_item_id.keys())

    def get_next_item_id(not_memorized_item_ids, last_newly_memorized_item_id):
        sorted_item_ids = sorted(not_memorized_item_ids)
        for item_id in sorted_item_ids:
            if item_id > last_newly_memorized_item_id:
                return item_id
        return None

    next_item_id = get_next_item_id(
        not_memorized_item_ids, last_newly_memorized_item_id
    )
    if next_item_id is None:
        display_next = "No more pages"
    else:
        display_next = get_page_description(next_item_id, is_link=False)

    return next_item_id, display_next


def render_new_memorization_checkbox(
    auth, item_id=None, page_id=None, label_text=None, **kwrgs
):
    label = label_text or ""

    if page_id is not None:
        item_id_list = items(where=f"page_id = {page_id} AND active != 0")
        item_ids = []
        for i in item_id_list:
            item_ids.append(i.id)
        check_form = Form(
            LabelCheckboxX(
                label,
                hx_get=f"/new_memorization/expand/page/{page_id}",
                checked=False,
                hx_trigger="click",
                onClick="return false",
            ),
            hx_vals='{"title": "CURRENT_TITLE", "description": "CURRENT_DETAILS"}'.replace(
                "CURRENT_TITLE", ""
            ).replace(
                "CURRENT_DETAILS", ""
            ),
            target_id="modal-body",
            data_uk_toggle="target: #modal",
        )
    else:
        current_revision_data = revisions(
            where=f"item_id = {item_id} AND mode_id = 2 AND hafiz_id = {auth};"
        )
        check_form = Form(
            LabelCheckboxX(
                label,
                name=f"is_checked",
                value="1",
                hx_post=f"/new_memorization/update_as_newly_memorized/{item_id}",
                **kwrgs,
                checked=True if current_revision_data else False,
            )
        )
    return check_form


def render_navigation_item(
    _type: str,
    current_type: str,
):
    return Li(
        A(
            f"by {_type}",
            href=f"/new_memorization/{_type}",
        ),
        cls=("uk-active" if _type == current_type else None),
    )


def render_row_based_on_type(
    auth,
    type_number: str,
    records: list,
    current_type,
    row_link: bool = True,
):
    _surahs = sorted({r["surah_id"] for r in records})
    _pages = sorted([r["page_number"] for r in records])
    _juzs = sorted({r["juz_number"] for r in records})

    def render_range(list, _type=""):
        first_description = list[0]
        last_description = list[-1]

        if _type == "Surah":
            _type = ""
            first_description = surahs[first_description].name
            last_description = surahs[last_description].name

        if len(list) == 1:
            return f"{_type} {first_description}"
        return f"{_type}{"" if _type == "" else "s"} {first_description} – {last_description}"

    surah_range = render_range(_surahs, "Surah")
    page_range = render_range(_pages, "Page")
    juz_range = render_range(_juzs, "Juz")

    if current_type == "juz":
        details = f"{surah_range} ({page_range})"
    elif current_type == "surah":
        details = f"{juz_range} ({page_range})"
    elif current_type == "page":
        details = f"{juz_range} | {surah_range}"
    title = (
        f"{current_type.capitalize()} {type_number}"
        if current_type != "surah"
        else surahs[type_number].name
    )

    filter_url = f"/new_memorization/expand/{current_type}/{type_number}"
    if current_type == "page":
        item_ids = [item.id for item in items(where=f"page_id = {type_number}")]
        get_page = (
            # FIXME: This route not exist as it was
            f"/new_memorization/add/{current_type}?item_id={item_ids[0]}"
            if len(item_ids) == 1
            else filter_url
        )
    else:
        get_page = filter_url

    hx_attrs = {
        "hx_get": get_page,
        "hx_vals": '{"title": "CURRENT_TITLE", "description": "CURRENT_DETAILS"}'.replace(
            "CURRENT_TITLE", title or ""
        ).replace(
            "CURRENT_DETAILS", details or ""
        ),
        "target_id": "modal-body",
        "data_uk_toggle": "target: #modal",
    }

    if current_type != "page":
        link_text = "Show Pages ➡️"
    else:
        link_text = "Set as Newly Memorized"
    item_ids = [item.id for item in items(where=f"page_id = {type_number}")]
    render_attrs = {
        "hx_select": f"#new_memorization_{current_type}-{type_number}",
        "hx_target": f"#new_memorization_{current_type}-{type_number}",
        "hx_swap": "outerHTML",
        "hx_select_oob": "#recently_memorized_table",
    }
    if len(item_ids) == 1 and not row_link and current_type == "page":
        link_content = render_new_memorization_checkbox(
            auth=auth, item_id=item_ids[0], **render_attrs
        )
    elif len(item_ids) > 1 and current_type == "page":
        link_content = render_new_memorization_checkbox(
            auth=auth, page_id=type_number, **render_attrs
        )
    else:
        link_content = A(
            link_text,
            cls=AT.classic,
            hx_attrs={**hx_attrs},
        )

    hx_attributes = hx_attrs if current_type != "page" else {} if row_link else {}
    return Tr(
        Td(title),
        Td(details),
        Td(link_content),
        **hx_attributes,
        id=f"new_memorization_{current_type}-{type_number}",
    )


@new_memorization_app.post("/update_as_newly_memorized/{item_id}")
def update_status_as_newly_memorized(
    auth, request, item_id: str, is_checked: bool = False, rating: int = None
):
    qry = f"item_id = {item_id} AND mode_id = 2;"
    revisions_data = revisions(where=qry)
    current_date = get_current_date(auth)
    if not revisions_data and is_checked:
        revisions.insert(
            hafiz_id=auth,
            item_id=item_id,
            revision_date=current_date,
            rating=(
                DEFAULT_RATINGS.get("new_memorization") if rating is None else rating
            ),
            mode_id=2,
        )
        try:
            hafizs_items_id = hafizs_items(where=f"item_id = {item_id}")[0]
        except IndexError:
            hafizs_items.insert(
                Hafiz_Items(item_id=item_id, page_number=items[item_id].page_id)
            )
        hafizs_items_id = hafizs_items(where=f"item_id = {item_id}")[0].id
        hafizs_items.update(
            {
                "status_id": 4,
                "mode_id": 2,
            },
            hafizs_items_id,
        )
    elif revisions_data and not is_checked:
        revisions.delete(revisions_data[0].id)
        hafizs_items_data = hafizs_items(
            where=f"item_id = {item_id} AND hafiz_id= {auth}"
        )[0]
        hafizs_items_data.status_id = 6
        hafizs_items_data.mode_id = 1
        hafizs_items.update(hafizs_items_data)

    populate_hafizs_items_stat_columns(item_id=item_id)
    referer = request.headers.get("Referer")
    return RedirectResponse(referer, status_code=303)


@new_memorization_app.post("/bulk_update_as_newly_memorized")
def bulk_update_status_as_newly_memorized(
    request, item_ids: list[int], auth, rating: int = None
):
    current_date = get_current_date(auth)

    for item_id in item_ids:
        revisions.insert(
            hafiz_id=auth,
            item_id=item_id,
            revision_date=current_date,
            rating=(
                DEFAULT_RATINGS.get("new_memorization") if rating is None else rating
            ),
            mode_id=2,
        )

        try:
            hafizs_items_id = hafizs_items(where=f"item_id = {item_id}")[0]
        except IndexError:
            hafizs_items.insert(
                Hafiz_Items(item_id=item_id, page_number=items[item_id].page_id)
            )
        hafizs_items_id = hafizs_items(where=f"item_id = {item_id}")[0].id
        hafizs_items.update(
            {
                "status_id": 4,
                "mode_id": 2,
            },
            hafizs_items_id,
        )
        populate_hafizs_items_stat_columns(item_id=item_id)
    referer = request.headers.get("Referer")
    return Redirect(referer)


@new_memorization_app.delete("/update_as_newly_memorized/{item_id}")
def delete(auth, request, item_id: str):
    qry = f"item_id = {item_id} AND mode_id = 2;"
    revisions_data = revisions(where=qry)
    revisions.delete(revisions_data[0].id)
    hafizs_items_data = hafizs_items(where=f"item_id = {item_id} AND hafiz_id= {auth}")[
        0
    ]
    hafizs_items_data.status_id = 6
    hafizs_items_data.mode_id = 1
    hafizs_items.update(hafizs_items_data)
    populate_hafizs_items_stat_columns(item_id=item_id)

    referer = request.headers.get("Referer")
    return Redirect(referer)


@new_memorization_app.get("/{current_type}")
def new_memorization(auth, current_type: str):
    if not current_type:
        current_type = "surah"
    ct = get_not_memorized_records(auth)
    grouped = group_by_type(ct, current_type)
    not_memorized_rows = [
        render_row_based_on_type(
            auth=auth,
            type_number=type_number,
            records=records,
            current_type=current_type,
            row_link=False,
        )
        for type_number, records in list(grouped.items())
    ]
    not_memorized_table = Div(
        Table(
            Thead(
                Tr(
                    Th("Name"),
                    Th("Range / Details"),
                    Th("Set As Newly Memorized"),
                ),
            ),
            Tbody(*not_memorized_rows),
        ),
        cls="uk-overflow-auto h-[45vh] p-4",
    )
    modal = ModalContainer(
        ModalDialog(
            ModalHeader(
                ModalTitle(id="modal-title"),
                P(cls=TextPresets.muted_sm, id="modal-description"),
                ModalCloseButton(),
                cls="space-y-3",
            ),
            ModalBody(
                Div(id="modal-body"),
                data_uk_overflow_auto=True,
            ),
            ModalFooter(),
            cls="uk-margin-auto-vertical",
        ),
        id="modal",
    )

    where_query = f"""
    revisions.mode_id = 2 AND revisions.hafiz_id = {auth} AND items.active != 0 
    ORDER BY revisions.revision_date DESC, revisions.id DESC 
    LIMIT 10;
    """
    print(auth)
    newly_memorized = get_not_memorized_records(auth, where_query)
    grouped = group_by_type(newly_memorized, "item_id")

    # Sort grouped items by earliest revision_date in each list of records
    sorted_grouped_items = sorted(
        grouped.items(),
        key=lambda item: max(
            (datetime.strptime(rec["revision_date"], "%Y-%m-%d"), rec["revision_id"])
            for rec in item[1]
        ),
        reverse=True,
    )

    def render_recently_memorized_row(type_number: str, records: list, auth):
        revision_date = records[0]["revision_date"]

        next_page_item_id, display_next = (0, "")
        if type_number:
            next_page_item_id, display_next = get_closest_unmemorized_item_id(
                auth, type_number
            )
        render_attrs = {
            "hx_select": f"#recently_memorized_table",
            "hx_target": f"#recently_memorized_table",
            "hx_swap": "outerHTML",
            "hx_select_oob": "#new_memorization_table",
        }
        return Tr(
            Td(get_page_description(records[0]["item_id"])),
            Td(date_to_human_readable(revision_date)),
            Td(
                render_new_memorization_checkbox(
                    auth=auth,
                    item_id=next_page_item_id,
                    label_text=display_next,
                    **render_attrs,
                )
                if next_page_item_id
                else display_next
            ),
            Td(
                A(
                    "Delete",
                    hx_delete=f"/new_memorization/update_as_newly_memorized/{type_number}",
                    hx_confirm="Are you sure? This page might be available in other modes.",
                ),
                cls=AT.muted,
            ),
        )

    newly_memorized_rows = [
        render_recently_memorized_row(
            type_number,
            records,
            auth=auth,
        )
        for type_number, records in sorted_grouped_items
        if type_number is not None
    ]
    recent_newly_memorized_table = Div(
        Table(
            Thead(
                Tr(
                    Th("Name"),
                    Th("Revision Date"),
                    Th("Set As Newly Memorized"),
                    Th("Action"),
                ),
            ),
            Tbody(*newly_memorized_rows),
        ),
        cls="uk-overflow-auto h-[25vh] p-4",
    )

    return main_area(
        H1("New Memorization", cls="uk-text-center"),
        Div(
            Div(
                H4("Recently Memorized Pages"),
                recent_newly_memorized_table,
                cls="mt-4",
                id="recently_memorized_table",
            ),
            Div(
                H4("Select a Page Not Yet Memorized"),
                TabContainer(
                    *map(
                        lambda nav: render_navigation_item(nav, current_type),
                        ["juz", "surah", "page"],
                    ),
                ),
                not_memorized_table,
                id="new_memorization_table",
            ),
            cls="space-y-4",
        ),
        Div(modal),
        active="Home",
        auth=auth,
    )


@new_memorization_app.get("/expand/{current_type}/{type_number}")
def load_descendant_items_for_new_memorization(
    auth, current_type: str, type_number: int, title: str, description: str
):
    if current_type == "juz":
        condition = f"pages.juz_number = {type_number}"
    elif current_type == "surah":
        condition = f"items.surah_id = {type_number}"
    elif current_type == "page":
        condition = f"pages.page_number = {type_number}"
    else:
        return "Invalid current_type"

    qry = f"""SELECT items.id, items.surah_id, pages.page_number, pages.juz_number, hafizs_items.status_id FROM items
                          LEFT JOIN pages ON items.page_id = pages.id
                          LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
                          WHERE items.active != 0 AND hafizs_items.status_id = 6 AND {condition}"""
    ct = db.q(qry)

    def render_row(record):
        return Tr(
            Td(
                # This hidden input is to send the id to the backend even if it is unchecked
                CheckboxX(
                    name=f"item_ids",
                    value=record["id"],
                    cls="partial_rows",  # Alpine js reference
                    _at_click="handleCheckboxClick($event)",
                ),
            ),
            Td(record["page_number"]),
            Td(surahs[record["surah_id"]].name),
            Td(f"Juz {record['juz_number']}"),
        )

    table = Div(
        Table(
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
                )
            ),
            Tbody(*map(render_row, ct)),
            x_data=select_all_checkbox_x_data(
                class_name="partial_rows", is_select_all="false"
            ),
            x_init="updateSelectAll()",
        ),
        cls="uk-overflow-auto max-h-[75vh] p-4",
    )

    return (
        Form(
            table,
            Button("Set as Newly Memorized", cls="bg-green-600 text-white"),
            hx_post=f"/new_memorization/bulk_update_as_newly_memorized",
            cls="space-y-2",
        ),
        ModalTitle(
            "" if title == "" else f"{title} - Select Memorized Page",
            id="modal-title",
            hx_swap_oob="true",
        ),
        P(
            description,
            id="modal-description",
            hx_swap_oob="true",
            cls=TextPresets.muted_lg,
        ),
    )
