"""
Hafiz Service Module

Business logic and workflows for hafiz operations.
Orchestrates model functions to implement complex use cases.
"""

from .hafiz_model import populate_hafiz_items, create_new_plan

__all__ = [
    "setup_new_hafiz",
]


def setup_new_hafiz(hafiz_id: int) -> None:
    """
    Setup workflow for a newly created hafiz.

    Performs initial setup by:
    1. Populating hafizs_items for all active Quran items
    2. Creating initial Full Cycle revision plan

    Args:
        hafiz_id: ID of the newly created hafiz

    Note:
        This is a business logic function that orchestrates multiple model operations.
        Call this after inserting a new hafiz record.
    """
    populate_hafiz_items(hafiz_id)
    create_new_plan(hafiz_id)
