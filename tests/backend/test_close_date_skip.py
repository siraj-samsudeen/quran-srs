"""
Backend tests for Close Date skip-to-today logic.

Tests the business logic for automatically advancing current_date
to today when many days have elapsed.
"""

import os
from datetime import datetime, timedelta

# Set ENV before any imports
os.environ["ENV"] = "test"


def test_close_date_skips_to_today_when_many_days_elapsed(db_connection):
    """
    When current_date is more than 1 day behind today,
    close_date should skip directly to today.

    Backend Testing Rules:
    - Setup: Seed test data via DB
    - Action: Call business logic directly
    - Assert: Verify database state and return values
    """
    from globals import db, hafizs, users, hafizs_items
    from main import change_the_current_date

    # Get today's real date
    today = datetime.now().strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Clean up any existing test data first
    db.execute("DELETE FROM hafizs_items WHERE hafiz_id = 9001")
    db.execute("DELETE FROM hafizs WHERE id = 9001")
    db.execute("DELETE FROM users WHERE id = 9001")

    # Create test user using FastHTML database layer
    users.insert(id=9001, email='skip_test@example.com', password='testpass', name='Skip Test User')

    # Create test hafiz with old current_date using FastHTML database layer
    hafizs.insert(
        id=9001,
        name='Skip Test Hafiz',
        user_id=9001,
        current_date=thirty_days_ago,
        daily_capacity=20
    )

    # Verify the hafiz was created with the correct date
    hafiz = hafizs[9001]
    print(f"RIGHT AFTER INSERT: current_date = {hafiz.current_date}")
    print(f"Expected to be: {thirty_days_ago}")
    assert hafiz.current_date == thirty_days_ago, f"Setup failed: expected {thirty_days_ago}, got {hafiz.current_date}"

    # Create a hafizs_item in SRS mode with next_review in the past
    ten_days_ago = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    hafizs_items.insert(
        hafiz_id=9001,
        item_id=1,
        mode_code='SR',
        memorized=1,
        next_review=ten_days_ago,
        next_interval=7,
        page_number=1
    )

    # Act: Call close_date function
    print(f"BEFORE close_date: current_date = {hafizs[9001].current_date}")

    change_the_current_date(auth=9001)

    # Assert: Verify current_date has jumped to today (not just +1 day)
    hafiz_after = hafizs[9001]
    print(f"AFTER close_date: current_date = {hafiz_after.current_date}")
    print(f"TODAY: {today}")
    print(f"Expected jump from {thirty_days_ago} to {today}, but got {hafiz_after.current_date}")

    # This should fail because we haven't implemented the feature yet
    assert hafiz_after.current_date == today, f"Expected current_date to be {today}, but got {hafiz_after.current_date}"

    # Cleanup
    db.execute("DELETE FROM hafizs_items WHERE hafiz_id = 9001")
    db.execute("DELETE FROM hafizs WHERE id = 9001")
    db.execute("DELETE FROM users WHERE id = 9001")
