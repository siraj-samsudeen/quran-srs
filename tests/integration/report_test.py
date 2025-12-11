"""Integration tests for report page counting functionality."""

import re
from datetime import datetime


def test_datewise_summary_counts_page_parts_as_fraction_not_full_pages():
    """
    BUG TEST: datewise_summary_table counts page parts as full pages.

    When a page is split into 2 parts, revising both parts should count as 1 page,
    not 2 pages. This test verifies the total count in the report.
    """
    from database import items, hafizs, revisions, hafizs_items, users, db
    from app.home_view import datewise_summary_table

    # Arrange: Find a page with 2 parts
    pages_with_parts = db.q("""
        SELECT page_id, COUNT(*) as part_count
        FROM items
        WHERE active = 1
        GROUP BY page_id
        HAVING COUNT(*) > 1
        LIMIT 1
    """)

    assert pages_with_parts, "Test requires a page with multiple parts in the database"

    test_page_id = pages_with_parts[0]["page_id"]
    part_count = pages_with_parts[0]["part_count"]

    # Get the item IDs for this page's parts
    page_part_items = items(where=f"page_id = {test_page_id} AND active = 1")
    assert len(page_part_items) == part_count

    # Create a test user
    test_email = f"report_test_{datetime.now().timestamp()}@example.com"
    user_id = users.insert(email=test_email, password="test123", name="Report Test User").id

    try:
        # Create a test hafiz
        hafiz_id = hafizs.insert(
            name="Report Test Hafiz",
            user_id=user_id,
            daily_capacity=5,
            current_date="2024-01-15"
        ).id

        # Create hafiz_items for each part
        for item in page_part_items:
            hafizs_items.insert(
                hafiz_id=hafiz_id,
                item_id=item.id,
                memorized=True,
                mode_code="FC"
            )

        # Create revisions for all parts of this page on the same date
        test_date = "2024-01-15"
        for item in page_part_items:
            revisions.insert(
                hafiz_id=hafiz_id,
                item_id=item.id,
                mode_code="FC",
                revision_date=test_date,
                rating=1
            )

        # Act: Generate the datewise summary table
        result = datewise_summary_table(show=1, hafiz_id=hafiz_id)
        result_str = str(result)

        # Extract the Total Count value from the HTML
        # The format is: td((VALUE,),{'rowspan': '1', ...}) where VALUE is the count
        # The "Total Count" column is the second td in the row
        total_count_match = re.search(r"td\(\((\d+),\),\{'rowspan':", result_str)
        assert total_count_match, "Could not find Total Count in HTML output"

        total_count = int(total_count_match.group(1))

        # Assert: Total count should be 1 (one full page), not part_count (items)
        # BUG: Currently shows part_count because len() is used instead of get_page_count()
        assert total_count == 1, (
            f"Bug detected: Total Count shows {total_count} (item count) instead of 1 (page count). "
            f"The datewise_summary_table is counting items, not pages. "
            f"Page {test_page_id} has {part_count} parts, so revising all parts = 1 page."
        )

    finally:
        # Cleanup: Delete test data (cascades to hafiz, hafiz_items, revisions)
        users.delete(user_id)
