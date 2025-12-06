from .globals import revisions, plans, hafizs_items, FULL_CYCLE_MODE_CODE, SRS_MODE_CODE


def get_revision_by_id(revision_id: int):
    return revisions[revision_id]


def update_revision(revision_details):
    revisions.update(revision_details, revision_details.id)
    return revisions[revision_details.id]


def delete_revision(revision_id: int):
    revisions.delete(revision_id)


def insert_revision(revision_details):
    return revisions.insert(revision_details)


def insert_revisions_bulk(revision_list):
    for revision in revision_list:
        revisions.insert(revision)


def get_revision_table_data(part_num: int = 1, size: int = 20):
    offset = (part_num - 1) * size
    all_revisions = revisions(order_by="revision_date DESC, id DESC")
    return all_revisions[offset : offset + size]


def cycle_full_cycle_plan_if_completed():
    """
    Check if current Full Cycle plan is completed.
    If all memorized items have been revised, mark plan as complete and create new plan.
    """
    from app.common_model import get_current_plan_id
    from app.users_model import create_new_plan

    plan_id = get_current_plan_id()
    if not plan_id:
        return

    # Get all memorized items that should be in Full Cycle
    memorized_items = hafizs_items(
        where=f"memorized = 1 AND mode_code IN ('{FULL_CYCLE_MODE_CODE}', '{SRS_MODE_CODE}')"
    )
    memorized_item_ids = {item.item_id for item in memorized_items}

    # Get items revised in current plan
    plan_revisions = revisions(
        where=f"plan_id = {plan_id} AND mode_code = '{FULL_CYCLE_MODE_CODE}'"
    )
    revised_item_ids = {rev.item_id for rev in plan_revisions}

    # Check if all memorized items have been revised
    if memorized_item_ids.issubset(revised_item_ids):
        # Mark plan as completed
        current_plan = plans[plan_id]
        current_plan.completed = 1
        plans.update(current_plan, plan_id)

        # Create new plan
        create_new_plan(current_plan.hafiz_id)
