"""Integration tests for report page functionality."""

import time


# ============================================================================
# Datewise Summary Report Tests
# ============================================================================


def test_report_counts_page_parts_correctly(client):
    """Report counts page parts as fractions, not full pages.

    When a page is split into 2 parts, revising both parts should count as 1 page.
    """
    from database import items, hafizs, revisions, hafizs_items, users, db

    # Find a page with multiple parts
    pages_with_parts = db.q("""
        SELECT page_id, COUNT(*) as part_count
        FROM items
        WHERE active = 1
        GROUP BY page_id
        HAVING COUNT(*) > 1
        LIMIT 1
    """)
    assert pages_with_parts, "Test requires a page with multiple parts"

    test_page_id = pages_with_parts[0]["page_id"]
    part_count = pages_with_parts[0]["part_count"]
    page_part_items = items(where=f"page_id = {test_page_id} AND active = 1")

    # Create test user via route
    test_email = f"report_test_{int(time.time() * 1000)}@example.com"
    signup_response = client.post(
        "/users/signup",
        data={
            "name": "Report Test User",
            "email": test_email,
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=False,
    )
    assert signup_response.status_code in (302, 303)

    # Login
    login_response = client.post(
        "/users/login",
        data={"email": test_email, "password": "password123"},
        follow_redirects=False,
    )
    client.cookies = login_response.cookies

    # Create hafiz via route
    hafiz_response = client.post(
        "/hafiz/add",
        data={"name": "Report Test Hafiz", "daily_capacity": 5},
        follow_redirects=False,
    )

    # Get the created hafiz
    user = users(where=f"email = '{test_email}'")[0]
    user_hafizs = hafizs(where=f"user_id = {user.id}")
    assert len(user_hafizs) > 0
    hafiz_id = user_hafizs[0].id

    # Select hafiz
    select_response = client.post(
        "/hafiz/selection",
        data={"current_hafiz_id": hafiz_id},
        follow_redirects=False,
    )
    client.cookies = select_response.cookies

    # Set a fixed date for the hafiz
    test_date = "2024-01-15"
    hafizs.update({"current_date": test_date}, hafiz_id)

    # Create hafiz_items and revisions for all parts of the page
    for item in page_part_items:
        hafizs_items.insert(
            hafiz_id=hafiz_id,
            item_id=item.id,
            memorized=True,
            mode_code="FC"
        )
        revisions.insert(
            hafiz_id=hafiz_id,
            item_id=item.id,
            mode_code="FC",
            revision_date=test_date,
            rating=1
        )

    # Act: Access the report page
    report_response = client.get("/report")

    assert report_response.status_code == 200

    # Assert: Check that page count is 1, not part_count
    # The report should show "1" (one full page) not "2" (two items)
    response_text = report_response.text

    # The count appears in the table - we should see "1" for the total
    # If buggy, we'd see the part_count (e.g., "2")
    assert ">1<" in response_text or ">1.0<" in response_text, (
        f"Expected page count of 1 in report, but page {test_page_id} with "
        f"{part_count} parts may be incorrectly counted as {part_count} items"
    )

    # Cleanup: Delete user (cascades to hafiz, revisions, etc.)
    users.delete(user.id)
