"""
User Model - Database operations for users and hafizs

Provides CRUD operations and query helpers for user and hafiz management.
Organized by domain: users first, then hafizs, then initialization utilities.
"""

from datetime import datetime
from dataclasses import dataclass
from constants import *
from database import *
from app.common_function import *


# ============================================================================
# DATACLASSES & TYPES
# ============================================================================

@dataclass
class User:
    id: int | None = None
    name: str | None = None
    email: str | None = None
    password: str | None = None


@dataclass
class Login:
    email: str
    password: str


# ============================================================================
# USER OPERATIONS
# ============================================================================

def create_user(email: str, password: str, name: str) -> int:
    """Create new user and return user_id"""
    new_user = users.insert(email=email, password=password, name=name)
    return new_user.id


def get_user_by_email(email: str):
    try:
        return users(where=f"email = '{email}'")[0]
    except IndexError:
        return None
