"""
Test dataclass consistency between explicit definitions and database-generated ones.

Ensures that dataclasses explicitly defined in model files match the auto-generated
dataclasses from database.py. This catches schema drift and type mismatches.
"""

from dataclasses import fields
from app.users_model import User
from app.hafiz_model import Hafiz
from database import users, hafizs


def fields_match(dataclass, table):
    """Check if dataclass fields match database table fields."""
    return [(f.name, f.type) for f in fields(dataclass)] == [
        (f.name, f.type) for f in fields(table.dataclass())
    ]


def test_dataclasses_matches_database():
    """Ensure that explicitly defined dataclasses matches database tables"""
    assert fields_match(User, users)
    assert fields_match(Hafiz, hafizs)
