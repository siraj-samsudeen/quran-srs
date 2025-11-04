from datetime import datetime
from dataclasses import dataclass
from globals import *
from app.common_function import *


@dataclass
class Login:
    email: str
    password: str


# Database operations (CRUD only)
def get_user_by_email(email: str):
    """Get user by email address"""
    try:
        return users(where=f"email = '{email}'")[0]
    except IndexError:
        return None


def insert_user(user: User):
    """Insert new user record"""
    return users.insert(user)


def delete_user(user_id: int):
    """Delete user record"""
    users.delete(user_id)


def cleanup_orphaned_hafizs():
    qry = """DELETE FROM hafizs
    WHERE id NOT IN (
        SELECT DISTINCT hafiz_id FROM hafizs_users
    );"""
    db.q(qry)


def get_hafizs_for_user(user_id: int):
    """Get all hafizs associated with a user"""
    return [h for h in hafizs_users() if h.user_id == user_id]


def insert_hafiz(hafiz: Hafiz):
    """Insert new hafiz record"""
    return hafizs.insert(hafiz)


def insert_hafiz_user_relationship(hafiz_id: int, user_id: int, relationship: str):
    """Create relationship between hafiz and user"""
    return hafizs_users.insert(
        hafiz_id=hafiz_id,
        user_id=user_id,
        relationship=relationship,
        granted_by_user_id=user_id,
        granted_at=datetime.now().strftime("%d-%m-%y %H:%M:%S"),
    )


def get_hafiz_by_id(hafiz_id: int):
    """Get hafiz record by ID"""
    return hafizs[hafiz_id]


def reset_table_filters():
    """Reset xtra attributes to show data for all records"""
    revisions.xtra()
    hafizs_users.xtra()


def populate_hafiz_items(hafiz_id: int):
    # Reset xtra attributes
    hafizs_items.xtra()
    # This query will return all the missing items for that hafiz or all items for new hafiz
    # and we will add the items in to the hafizs_items table
    qry = f"""
    SELECT items.id from items
    LEFT JOIN hafizs_items ON items.id = hafizs_items.item_id AND hafizs_items.hafiz_id = {hafiz_id} 
    WHERE items.active <> 0 AND hafizs_items.item_id IS Null;
    """
    ct = db.q(qry)
    missing_item_ids = [r["id"] for r in ct]

    if missing_item_ids:
        for missing_item_id in missing_item_ids:
            hafizs_items.insert(
                hafiz_id=hafiz_id,
                item_id=missing_item_id,
                page_number=get_page_number(missing_item_id),
                mode_code=FULL_CYCLE_MODE_CODE,  # TODO: Confirm that full cycle mode is appropriate here.
                # Missing items are currently assumed to belong to the "full-cycle" mode.
            )


def create_new_plan(hafiz_id: int):
    # Reset xtra attributes
    plans.xtra()
    return plans.insert(
        hafiz_id=hafiz_id,
        start_date=get_current_date(hafiz_id),
        start_page=2,
        completed=0,
    )
