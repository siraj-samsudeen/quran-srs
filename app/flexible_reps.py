from app.common_function import *


def get_srs_table(auth):
    srs_table, srs_items = make_summary_table(
        mode_ids=[str(SRS_MODE_ID)], route="srs", auth=auth
    )

    srs_target = get_page_count(item_ids=srs_items)

    return srs_table, srs_target


def update_hafiz_item_for_srs(rev):
    hafiz_items_details = get_hafizs_items(rev.item_id)
    current_date = get_current_date(rev.hafiz_id)
    end_interval = srs_booster_pack[
        hafiz_items_details.srs_booster_pack_id
    ].end_interval
    next_interval = get_next_interval(item_id=rev.item_id, rating=rev.rating)

    hafiz_items_details.last_interval = hafiz_items_details.next_interval
    if end_interval > next_interval:
        hafiz_items_details.next_interval = next_interval
        hafiz_items_details.next_review = add_days_to_date(current_date, next_interval)
    else:
        hafiz_items_details.mode_id = FULL_CYCLE_MODE_ID
        hafiz_items_details.status_id = 1
        hafiz_items_details.last_interval = calculate_days_difference(
            hafiz_items_details.last_review, current_date
        )
        hafiz_items_details.next_interval = None
        hafiz_items_details.next_review = None
        hafiz_items_details.srs_booster_pack_id = None
        hafiz_items_details.srs_start_date = None

    hafizs_items.update(hafiz_items_details)

    # Update the next_interval of the revision record
    rev.next_interval = next_interval
    revisions.update(rev, rev.id)


def start_srs_for_bad_streak_items(auth):
    current_date = get_current_date(auth)
    # Get the full-cycle today revised pages which have 1 or more bad streak
    qry = f"""
        SELECT revisions.item_id FROM revisions
        LEFT JOIN hafizs_items ON revisions.item_id = hafizs_items.item_id AND hafizs_items.hafiz_id = {auth}
        WHERE hafizs_items.bad_streak >= 1 AND revisions.mode_id = {FULL_CYCLE_MODE_ID} AND revisions.hafiz_id = {auth} AND revisions.revision_date = '{current_date}'
    """
    for items in db.q(qry):
        start_srs(items["item_id"], auth)


def display_srs_pages_recorded_today(auth):
    current_date = get_current_date(auth)

    # List all the records that are recorded today with the interval details as a table
    srs_records = db.q(
        f"""
    SELECT revisions.item_id, hafizs_items.next_interval as previous_interval,
    revisions.rating, hafizs_items.srs_booster_pack_id as pack_id FROM revisions 
    LEFT JOIN hafizs_items ON hafizs_items.item_id = revisions.item_id AND hafizs_items.hafiz_id = revisions.hafiz_id
    WHERE revisions.revision_date = '{current_date}' AND revisions.mode_id = {SRS_MODE_ID}
    """
    )

    def render_srs_records(srs_record):
        pack_details = srs_booster_pack[srs_record["pack_id"]]
        end_interval = pack_details.end_interval
        next_interval = get_next_interval(srs_record["item_id"], srs_record["rating"])
        if next_interval > end_interval:
            next_interval = "Graduation"
        return Tr(
            Td(get_page_description(srs_record["item_id"])),
            Td(srs_record["previous_interval"]),
            Td(get_actual_interval(srs_record["item_id"])),
            Td(next_interval),
            Td(render_rating(srs_record["rating"])),
        )

    srs_records_table = Table(
        Thead(
            Tr(
                Th("Item Id"),
                Th("Last Interval"),
                Th("Actual Interval"),
                Th("Next Interval"),
                Th("Rating"),
            )
        ),
        Tbody(*map(render_srs_records, srs_records)),
    )

    # Confirmation and cancel buttons
    action_buttons = DivLAligned(
        Button(
            "Confirm",
            hx_post="close_date",
            hx_target="body",
            hx_push_url="true",
            hx_disabled_elt="this",
            cls=(ButtonT.primary, "p-2"),
        ),
        Button(
            "Cancel",
            onclick="history.back()",
            cls=(ButtonT.default, "p-2"),
        ),
    )

    header = Div(
        Strong("Current Date: "),
        Span(render_date(current_date)),
    )
    body = Div(
        H2("SRS Records"),
        srs_records_table,
        cls="uk-overflow-auto space-y-2",
    )
    footer = action_buttons

    return main_area(
        Div(header, body, footer, cls="space-y-4"),
        active="Home",
        auth=auth,
    )
