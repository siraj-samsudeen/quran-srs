from datetime import datetime
from dataclasses import dataclass
from globals import *


@dataclass
class Login:
    email: str
    password: str


# Database connection and table setup
users = db.t.users
hafizs = db.t.hafizs
hafizs_users = db.t.hafizs_users
revisions = db.t.revisions

(Hafiz, User, Hafiz_Users, Revisions) = (
    hafizs.dataclass(),
    users.dataclass(),
    hafizs_users.dataclass(),
    revisions.dataclass(),
)


# Database operations (CRUD only)
def get_user_by_email(email: str):
    """Get user by email address"""
    try:
        return users(where=f"email = '{email}'")[0]
    except IndexError:
        return None


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
