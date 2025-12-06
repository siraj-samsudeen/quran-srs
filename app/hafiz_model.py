"""
Hafiz Model Module

Schema definition and data access for hafiz operations.
"""

from dataclasses import dataclass
from .globals import db


@dataclass
class Hafiz:
    """Hafiz profile belonging to a user."""

    id: int
    name: str | None = None
    daily_capacity: int | None = None
    user_id: int | None = None
    current_date: str | None = None  # Virtual date for this hafiz


# Get table reference and link schema
hafizs = db.t.hafizs
hafizs.cls = Hafiz


def get_hafiz(hafiz_id: int) -> Hafiz:
    return hafizs[hafiz_id]


def update_hafiz(hafiz_data: Hafiz, hafiz_id: int) -> None:
    hafizs.update(hafiz_data, hafiz_id)
