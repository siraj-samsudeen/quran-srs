"""
Users Model Module

Schema definition and data access for user operations.
"""

from dataclasses import dataclass
from .globals import users, revisions

__all__ = [
    "Login",
    "get_user_by_email",
    "insert_user",
    "reset_table_filters",
]


@dataclass
class Login:
    email: str
    password: str


# =============================================================================
# User CRUD Operations
# =============================================================================


def get_user_by_email(email: str):
    """Get user by email address."""
    try:
        return users(where=f"email = '{email}'")[0]
    except IndexError:
        return None


def insert_user(user):
    """Insert new user record."""
    return users.insert(user)


# =============================================================================
# Utility Operations
# =============================================================================


def reset_table_filters():
    """Reset xtra attributes to show data for all records."""
    revisions.xtra()
