from database import db, items, modes, revisions, pages
from app.common_model import get_hafizs_items, get_actual_interval, get_prev_next_item_ids
from constants import RATING_MAP
from utils import date_to_human_readable, destandardize_text
from fasthtml.common import NotFoundError

def get_mode_name_and_code():
    all_modes = modes()
    mode_code_list = [mode.code for mode in all_modes]
    mode_name_list = [mode.name for mode in all_modes]
    return mode_code_list, mode_name_list

def get_page_details_summary(auth):
    mode_code_list, _ = get_mode_name_and_code()
    
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
    return db.q(display_pages_query)

def get_item_details(item_id):
    return items[item_id]

def get_mode_details(mode_code):
    try:
        return modes[mode_code]
    except NotFoundError:
        return None

def get_first_revision(item_id, auth, mode_codes):
    mode_codes_str = ", ".join([repr(code) for code in mode_codes])
    return revisions(
        where=f"item_id = {item_id} and hafiz_id = {auth} and mode_code IN ({mode_codes_str})",
        order_by="revision_date ASC",
        limit=1,
    )

def get_revision_history(item_id, auth, mode_codes):
    mode_codes_str = ", ".join(repr(code) for code in mode_codes)
    query = f"""
            SELECT
                ROW_NUMBER() OVER (ORDER BY revision_date ASC) AS s_no,
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
            WHERE item_id = {item_id} AND hafiz_id = {auth} AND revisions.mode_code IN ({mode_codes_str})
            ORDER BY revision_date ASC;"""
    return db.q(query)

def get_mode_name(mode_code):
    try:
        return modes[mode_code].name
    except NotFoundError:
        return mode_code

def update_item_description(item_id, description, start_text):
    items.update({"description": description, "start_text": start_text}, item_id)

def is_item_active(item_id):
    return bool(items(where=f'id = {item_id} and active != 0'))
