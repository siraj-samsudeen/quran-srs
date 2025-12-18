"""Integration tests for REP_MODES_CONFIG and graduation logic.

Tests the configuration consistency and graduation chain.
Full graduation behavior is tested via E2E tests which have proper authentication context.
"""

import time
import pytest
from constants import (
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
    FULL_CYCLE_MODE_CODE,
)
from app.fixed_reps import REP_MODES_CONFIG, set_next_review, update_rep_item


class TestRepModesConfigStructure:
    """Test REP_MODES_CONFIG structure and values."""

    def test_all_rep_modes_have_config(self):
        """All rep modes have configuration entries."""
        expected_modes = [
            DAILY_REPS_MODE_CODE,
            WEEKLY_REPS_MODE_CODE,
            FORTNIGHTLY_REPS_MODE_CODE,
            MONTHLY_REPS_MODE_CODE,
        ]
        for mode in expected_modes:
            assert mode in REP_MODES_CONFIG

    def test_config_has_required_fields(self):
        """Each config has interval, threshold, and next_mode_code."""
        for mode_code, config in REP_MODES_CONFIG.items():
            assert "interval" in config, f"{mode_code} missing interval"
            assert "threshold" in config, f"{mode_code} missing threshold"
            assert "next_mode_code" in config, f"{mode_code} missing next_mode_code"


class TestGraduationChainConfig:
    """Test the graduation chain is configured correctly."""

    def test_daily_to_weekly(self):
        """Daily mode graduates to Weekly."""
        assert REP_MODES_CONFIG[DAILY_REPS_MODE_CODE]["next_mode_code"] == WEEKLY_REPS_MODE_CODE
        assert REP_MODES_CONFIG[DAILY_REPS_MODE_CODE]["interval"] == 1

    def test_weekly_to_fortnightly(self):
        """Weekly mode graduates to Fortnightly."""
        assert REP_MODES_CONFIG[WEEKLY_REPS_MODE_CODE]["next_mode_code"] == FORTNIGHTLY_REPS_MODE_CODE
        assert REP_MODES_CONFIG[WEEKLY_REPS_MODE_CODE]["interval"] == 7

    def test_fortnightly_to_monthly(self):
        """Fortnightly mode graduates to Monthly."""
        assert REP_MODES_CONFIG[FORTNIGHTLY_REPS_MODE_CODE]["next_mode_code"] == MONTHLY_REPS_MODE_CODE
        assert REP_MODES_CONFIG[FORTNIGHTLY_REPS_MODE_CODE]["interval"] == 14

    def test_monthly_to_full_cycle(self):
        """Monthly mode graduates to Full Cycle."""
        assert REP_MODES_CONFIG[MONTHLY_REPS_MODE_CODE]["next_mode_code"] == FULL_CYCLE_MODE_CODE
        assert REP_MODES_CONFIG[MONTHLY_REPS_MODE_CODE]["interval"] == 30

    def test_all_thresholds_are_seven(self):
        """All modes use threshold of 7."""
        for mode_code, config in REP_MODES_CONFIG.items():
            assert config["threshold"] == 7, f"{mode_code} threshold is not 7"


class TestSetNextReview:
    """Test the set_next_review helper function."""

    def test_sets_next_interval(self):
        """set_next_review sets next_interval on hafiz_item."""

        class MockHafizItem:
            next_interval = None
            next_review = None

        hafiz_item = MockHafizItem()
        set_next_review(hafiz_item, 7, "2024-01-15")

        assert hafiz_item.next_interval == 7

    def test_sets_next_review_date(self):
        """set_next_review sets next_review date."""

        class MockHafizItem:
            next_interval = None
            next_review = None

        hafiz_item = MockHafizItem()
        set_next_review(hafiz_item, 7, "2024-01-15")

        assert hafiz_item.next_review == "2024-01-22"  # 15 + 7 days

    def test_daily_interval(self):
        """Daily mode sets 1-day interval."""

        class MockHafizItem:
            next_interval = None
            next_review = None

        hafiz_item = MockHafizItem()
        interval = REP_MODES_CONFIG[DAILY_REPS_MODE_CODE]["interval"]
        set_next_review(hafiz_item, interval, "2024-01-15")

        assert hafiz_item.next_interval == 1
        assert hafiz_item.next_review == "2024-01-16"

    def test_fortnightly_interval(self):
        """Fortnightly mode sets 14-day interval."""

        class MockHafizItem:
            next_interval = None
            next_review = None

        hafiz_item = MockHafizItem()
        interval = REP_MODES_CONFIG[FORTNIGHTLY_REPS_MODE_CODE]["interval"]
        set_next_review(hafiz_item, interval, "2024-01-15")

        assert hafiz_item.next_interval == 14
        assert hafiz_item.next_review == "2024-01-29"

    def test_monthly_interval(self):
        """Monthly mode sets 30-day interval."""

        class MockHafizItem:
            next_interval = None
            next_review = None

        hafiz_item = MockHafizItem()
        interval = REP_MODES_CONFIG[MONTHLY_REPS_MODE_CODE]["interval"]
        set_next_review(hafiz_item, interval, "2024-01-15")

        assert hafiz_item.next_interval == 30
        assert hafiz_item.next_review == "2024-02-14"


# === Integration Tests for update_rep_item() Graduation Logic ===


@pytest.fixture
def graduation_test_hafiz(client):
    """Create a test user and hafiz for graduation tests.

    IMPORTANT: This fixture creates a fresh hafiz with items that have NO revisions.
    Each test should use different items to avoid conflicts between tests.
    """
    from app.users_model import create_user
    from database import users, hafizs, hafizs_items, revisions

    test_email = f"graduation_test_{int(time.time() * 1000)}@example.com"
    user_id = create_user(test_email, "password123", "Graduation Test User")

    login_response = client.post(
        "/users/login",
        data={"email": test_email, "password": "password123"},
        follow_redirects=False,
    )
    client.cookies = login_response.cookies

    client.post(
        "/hafiz/add",
        data={"name": "Test Hafiz"},
        follow_redirects=False,
    )

    user_hafizs = hafizs(where=f"user_id={user_id}")
    hafiz_id = user_hafizs[0].id
    select_response = client.post(
        "/hafiz/selection",
        data={"current_hafiz_id": hafiz_id},
        follow_redirects=False,
    )
    client.cookies = select_response.cookies

    # Get all test items for this hafiz
    test_items = hafizs_items(where=f"hafiz_id={hafiz_id}")

    yield {
        "client": client,
        "user_id": user_id,
        "hafiz_id": hafiz_id,
        "email": test_email,
        "items": test_items,
    }

    # Cleanup: delete all revisions for this hafiz's items before deleting user
    for item in test_items:
        for rev in revisions(where=f"item_id={item.item_id} AND hafiz_id={hafiz_id}"):
            revisions.delete(rev.id)

    users.delete(user_id)


class TestUpdateRepItemGraduation:
    """Test update_rep_item() graduation across all rep modes.

    These tests verify that:
    1. Items stay in mode when below threshold (7 reviews)
    2. Items graduate to next mode when threshold is reached
    3. next_review and next_interval are correctly updated
    4. memorized flag is set correctly on Full Cycle graduation

    Note: Tests set revisions.xtra() to filter by hafiz_id, simulating the
    beforeware behavior that occurs in production requests.
    """

    def test_daily_stays_in_mode_below_threshold(self, graduation_test_hafiz):
        """Item in Daily mode stays in Daily with correct interval below threshold."""
        from database import hafizs, hafizs_items, revisions

        hafiz_id = graduation_test_hafiz["hafiz_id"]
        items_list = graduation_test_hafiz["items"]
        test_item = items_list[0]
        item_id = test_item.item_id

        # Set xtra filter to simulate beforeware (required for get_mode_count)
        revisions.xtra(hafiz_id=hafiz_id)
        hafizs_items.xtra(hafiz_id=hafiz_id)

        # Set item to Daily mode with initial values
        hafizs_items.update({
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_interval": 1,
            "next_review": "2024-01-15",
            "memorized": False,
        }, test_item.id)

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Add 3 revisions (below threshold of 7)
        for i in range(3):
            revisions.insert(
                item_id=item_id,
                hafiz_id=hafiz_id,
                mode_code=DAILY_REPS_MODE_CODE,
                revision_date=f"2024-01-{10+i:02d}",
                rating=1,
            )

        # Create revision object for update_rep_item
        rev = revisions.insert(
            item_id=item_id,
            hafiz_id=hafiz_id,
            mode_code=DAILY_REPS_MODE_CODE,
            revision_date="2024-01-15",
            rating=1,
        )

        update_rep_item(rev)

        # Verify: should stay in Daily mode
        updated_item = hafizs_items(where=f"item_id={item_id}")[0]
        assert updated_item.mode_code == DAILY_REPS_MODE_CODE
        assert updated_item.next_interval == 1
        assert updated_item.next_review == "2024-01-16"  # current_date + 1
        assert updated_item.memorized == 0

        # Clear xtra filter
        revisions.xtra()
        hafizs_items.xtra()

    def test_daily_graduates_to_weekly_at_threshold(self, graduation_test_hafiz):
        """Item in Daily mode graduates to Weekly after 7 reviews."""
        from database import hafizs, hafizs_items, revisions

        hafiz_id = graduation_test_hafiz["hafiz_id"]
        items_list = graduation_test_hafiz["items"]
        test_item = items_list[1]
        item_id = test_item.item_id

        # Set xtra filter to simulate beforeware
        revisions.xtra(hafiz_id=hafiz_id)
        hafizs_items.xtra(hafiz_id=hafiz_id)

        # Set item to Daily mode
        hafizs_items.update({
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_interval": 1,
            "next_review": "2024-01-15",
            "memorized": False,
        }, test_item.id)

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Add 6 revisions (one more to reach threshold)
        for i in range(6):
            revisions.insert(
                item_id=item_id,
                hafiz_id=hafiz_id,
                mode_code=DAILY_REPS_MODE_CODE,
                revision_date=f"2024-01-{8+i:02d}",
                rating=1,
            )

        # 7th revision triggers graduation
        rev = revisions.insert(
            item_id=item_id,
            hafiz_id=hafiz_id,
            mode_code=DAILY_REPS_MODE_CODE,
            revision_date="2024-01-15",
            rating=1,
        )

        update_rep_item(rev)

        # Verify: should graduate to Weekly mode
        updated_item = hafizs_items(where=f"item_id={item_id}")[0]
        assert updated_item.mode_code == WEEKLY_REPS_MODE_CODE
        assert updated_item.next_interval == 7
        assert updated_item.next_review == "2024-01-22"  # current_date + 7
        assert updated_item.memorized == 0

        # Clear xtra filter
        revisions.xtra()
        hafizs_items.xtra()

    def test_weekly_graduates_to_fortnightly_at_threshold(self, graduation_test_hafiz):
        """Item in Weekly mode graduates to Fortnightly after 7 reviews."""
        from database import hafizs, hafizs_items, revisions

        hafiz_id = graduation_test_hafiz["hafiz_id"]
        items_list = graduation_test_hafiz["items"]
        test_item = items_list[2]
        item_id = test_item.item_id

        # Set xtra filter to simulate beforeware
        revisions.xtra(hafiz_id=hafiz_id)
        hafizs_items.xtra(hafiz_id=hafiz_id)

        # Set item to Weekly mode
        hafizs_items.update({
            "mode_code": WEEKLY_REPS_MODE_CODE,
            "next_interval": 7,
            "next_review": "2024-01-15",
            "memorized": False,
        }, test_item.id)

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Add 6 revisions in Weekly mode
        for i in range(6):
            revisions.insert(
                item_id=item_id,
                hafiz_id=hafiz_id,
                mode_code=WEEKLY_REPS_MODE_CODE,
                revision_date=f"2023-12-{1+i*7:02d}",
                rating=1,
            )

        # 7th revision triggers graduation
        rev = revisions.insert(
            item_id=item_id,
            hafiz_id=hafiz_id,
            mode_code=WEEKLY_REPS_MODE_CODE,
            revision_date="2024-01-15",
            rating=1,
        )

        update_rep_item(rev)

        # Verify: should graduate to Fortnightly mode
        updated_item = hafizs_items(where=f"item_id={item_id}")[0]
        assert updated_item.mode_code == FORTNIGHTLY_REPS_MODE_CODE
        assert updated_item.next_interval == 14
        assert updated_item.next_review == "2024-01-29"  # current_date + 14
        assert updated_item.memorized == 0

        # Clear xtra filter
        revisions.xtra()
        hafizs_items.xtra()

    def test_fortnightly_graduates_to_monthly_at_threshold(self, graduation_test_hafiz):
        """Item in Fortnightly mode graduates to Monthly after 7 reviews."""
        from database import hafizs, hafizs_items, revisions

        hafiz_id = graduation_test_hafiz["hafiz_id"]
        items_list = graduation_test_hafiz["items"]
        test_item = items_list[3]
        item_id = test_item.item_id

        # Set xtra filter to simulate beforeware
        revisions.xtra(hafiz_id=hafiz_id)
        hafizs_items.xtra(hafiz_id=hafiz_id)

        # Set item to Fortnightly mode
        hafizs_items.update({
            "mode_code": FORTNIGHTLY_REPS_MODE_CODE,
            "next_interval": 14,
            "next_review": "2024-01-15",
            "memorized": False,
        }, test_item.id)

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Add 6 revisions in Fortnightly mode
        for i in range(6):
            revisions.insert(
                item_id=item_id,
                hafiz_id=hafiz_id,
                mode_code=FORTNIGHTLY_REPS_MODE_CODE,
                revision_date=f"2023-{11+i//2:02d}-{1+(i%2)*14:02d}",
                rating=1,
            )

        # 7th revision triggers graduation
        rev = revisions.insert(
            item_id=item_id,
            hafiz_id=hafiz_id,
            mode_code=FORTNIGHTLY_REPS_MODE_CODE,
            revision_date="2024-01-15",
            rating=1,
        )

        update_rep_item(rev)

        # Verify: should graduate to Monthly mode
        updated_item = hafizs_items(where=f"item_id={item_id}")[0]
        assert updated_item.mode_code == MONTHLY_REPS_MODE_CODE
        assert updated_item.next_interval == 30
        assert updated_item.next_review == "2024-02-14"  # current_date + 30
        assert updated_item.memorized == 0

        # Clear xtra filter
        revisions.xtra()
        hafizs_items.xtra()

    def test_monthly_graduates_to_full_cycle_at_threshold(self, graduation_test_hafiz):
        """Item in Monthly mode graduates to Full Cycle after 7 reviews."""
        from database import hafizs, hafizs_items, revisions

        hafiz_id = graduation_test_hafiz["hafiz_id"]
        items_list = graduation_test_hafiz["items"]
        test_item = items_list[4]
        item_id = test_item.item_id

        # Set xtra filter to simulate beforeware
        revisions.xtra(hafiz_id=hafiz_id)
        hafizs_items.xtra(hafiz_id=hafiz_id)

        # Set item to Monthly mode
        hafizs_items.update({
            "mode_code": MONTHLY_REPS_MODE_CODE,
            "next_interval": 30,
            "next_review": "2024-01-15",
            "memorized": False,
        }, test_item.id)

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Add 6 revisions in Monthly mode
        for i in range(6):
            revisions.insert(
                item_id=item_id,
                hafiz_id=hafiz_id,
                mode_code=MONTHLY_REPS_MODE_CODE,
                revision_date=f"2023-{7+i:02d}-15",
                rating=1,
            )

        # 7th revision triggers graduation to Full Cycle
        rev = revisions.insert(
            item_id=item_id,
            hafiz_id=hafiz_id,
            mode_code=MONTHLY_REPS_MODE_CODE,
            revision_date="2024-01-15",
            rating=1,
        )

        update_rep_item(rev)

        # Verify: should graduate to Full Cycle mode
        updated_item = hafizs_items(where=f"item_id={item_id}")[0]
        assert updated_item.mode_code == FULL_CYCLE_MODE_CODE
        # Full Cycle clears scheduling fields
        assert updated_item.next_interval is None
        assert updated_item.next_review is None
        # memorized flag is set to True for Full Cycle
        assert updated_item.memorized == 1

        # Clear xtra filter
        revisions.xtra()
        hafizs_items.xtra()

    def test_unknown_mode_returns_early(self, graduation_test_hafiz):
        """update_rep_item returns early for unknown mode codes."""
        from database import hafizs, hafizs_items, revisions

        hafiz_id = graduation_test_hafiz["hafiz_id"]
        items_list = graduation_test_hafiz["items"]
        test_item = items_list[5]
        item_id = test_item.item_id

        # Set xtra filter to simulate beforeware
        revisions.xtra(hafiz_id=hafiz_id)
        hafizs_items.xtra(hafiz_id=hafiz_id)

        # Set item to Full Cycle mode (not in REP_MODES_CONFIG)
        original_mode = FULL_CYCLE_MODE_CODE
        hafizs_items.update({
            "mode_code": original_mode,
            "next_interval": None,
            "next_review": None,
            "memorized": True,
        }, test_item.id)

        # Set hafiz current_date
        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Create revision with mode not in REP_MODES_CONFIG
        rev = revisions.insert(
            item_id=item_id,
            hafiz_id=hafiz_id,
            mode_code=FULL_CYCLE_MODE_CODE,  # Not in REP_MODES_CONFIG
            revision_date="2024-01-15",
            rating=1,
        )

        # This should return early without changes
        update_rep_item(rev)

        # Verify: item should be unchanged
        updated_item = hafizs_items(where=f"item_id={item_id}")[0]
        assert updated_item.mode_code == original_mode

        # Clear xtra filter
        revisions.xtra()
        hafizs_items.xtra()


class TestFullGraduationChain:
    """Test the complete graduation chain from Daily to Full Cycle."""

    def test_full_graduation_chain(self, graduation_test_hafiz):
        """Test progression through all modes: DR → WR → FR → MR → FC."""
        from database import hafizs, hafizs_items, revisions

        hafiz_id = graduation_test_hafiz["hafiz_id"]
        items_list = graduation_test_hafiz["items"]
        test_item = items_list[6]
        item_id = test_item.item_id

        # Set xtra filter to simulate beforeware
        revisions.xtra(hafiz_id=hafiz_id)
        hafizs_items.xtra(hafiz_id=hafiz_id)

        # Start in Daily mode
        hafizs_items.update({
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_interval": 1,
            "next_review": "2024-01-01",
            "memorized": False,
        }, test_item.id)

        graduation_chain = [
            (DAILY_REPS_MODE_CODE, WEEKLY_REPS_MODE_CODE, 7),
            (WEEKLY_REPS_MODE_CODE, FORTNIGHTLY_REPS_MODE_CODE, 14),
            (FORTNIGHTLY_REPS_MODE_CODE, MONTHLY_REPS_MODE_CODE, 30),
            (MONTHLY_REPS_MODE_CODE, FULL_CYCLE_MODE_CODE, None),
        ]

        for current_mode, next_mode, expected_interval in graduation_chain:
            # Set hafiz current_date
            hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

            # Add 7 revisions to trigger graduation
            for i in range(7):
                rev = revisions.insert(
                    item_id=item_id,
                    hafiz_id=hafiz_id,
                    mode_code=current_mode,
                    revision_date=f"2024-01-{8+i:02d}",
                    rating=1,
                )

            # Last revision triggers graduation
            update_rep_item(rev)

            # Verify graduation
            updated_item = hafizs_items(where=f"item_id={item_id}")[0]
            assert updated_item.mode_code == next_mode, f"Expected {next_mode}, got {updated_item.mode_code}"

            if next_mode == FULL_CYCLE_MODE_CODE:
                assert updated_item.next_interval is None
                assert updated_item.next_review is None
                assert updated_item.memorized == 1
            else:
                assert updated_item.next_interval == expected_interval

            # Update item mode for next iteration
            hafizs_items.update({"mode_code": next_mode}, test_item.id)

            # Clean up revisions for next mode test
            for rev_to_del in revisions(where=f"item_id={item_id}"):
                revisions.delete(rev_to_del.id)

        # Clear xtra filter
        revisions.xtra()
        hafizs_items.xtra()


# ============================================================================
# Test Class: Custom Threshold Graduation
# ============================================================================


class TestCustomThresholdGraduation:
    """Test that graduation respects custom thresholds instead of defaults."""

    def test_daily_graduates_with_custom_threshold_3(self, graduation_test_hafiz):
        """Item with custom_daily_threshold=3 graduates to Weekly after 3 reviews."""
        from database import hafizs, hafizs_items, revisions

        hafiz_id = graduation_test_hafiz["hafiz_id"]
        items_list = graduation_test_hafiz["items"]
        test_item = items_list[7]
        item_id = test_item.item_id

        revisions.xtra(hafiz_id=hafiz_id)
        hafizs_items.xtra(hafiz_id=hafiz_id)

        # Set item to Daily mode with custom threshold of 3
        hafizs_items.update({
            "mode_code": DAILY_REPS_MODE_CODE,
            "next_interval": 1,
            "next_review": "2024-01-15",
            "memorized": True,
            "custom_daily_threshold": 3,
        }, test_item.id)

        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Add only 3 revisions (custom threshold)
        for i in range(2):
            revisions.insert(
                item_id=item_id,
                hafiz_id=hafiz_id,
                mode_code=DAILY_REPS_MODE_CODE,
                revision_date=f"2024-01-{12+i:02d}",
                rating=1,
            )

        # 3rd revision triggers graduation
        rev = revisions.insert(
            item_id=item_id,
            hafiz_id=hafiz_id,
            mode_code=DAILY_REPS_MODE_CODE,
            revision_date="2024-01-15",
            rating=1,
        )

        update_rep_item(rev)

        updated_item = hafizs_items(where=f"item_id={item_id}")[0]
        assert updated_item.mode_code == WEEKLY_REPS_MODE_CODE
        assert updated_item.next_interval == 7

        revisions.xtra()
        hafizs_items.xtra()

    def test_weekly_graduates_with_custom_threshold_10(self, graduation_test_hafiz):
        """Item with custom_weekly_threshold=10 graduates to Fortnightly after 10 reviews."""
        from database import hafizs, hafizs_items, revisions

        hafiz_id = graduation_test_hafiz["hafiz_id"]
        items_list = graduation_test_hafiz["items"]
        test_item = items_list[8]
        item_id = test_item.item_id

        revisions.xtra(hafiz_id=hafiz_id)
        hafizs_items.xtra(hafiz_id=hafiz_id)

        # Set item to Weekly mode with custom threshold of 10
        hafizs_items.update({
            "mode_code": WEEKLY_REPS_MODE_CODE,
            "next_interval": 7,
            "next_review": "2024-01-15",
            "memorized": True,
            "custom_weekly_threshold": 10,
        }, test_item.id)

        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Add 9 revisions
        for i in range(9):
            revisions.insert(
                item_id=item_id,
                hafiz_id=hafiz_id,
                mode_code=WEEKLY_REPS_MODE_CODE,
                revision_date=f"2023-{11+i//4:02d}-{1+(i%4)*7:02d}",
                rating=1,
            )

        # 10th revision triggers graduation
        rev = revisions.insert(
            item_id=item_id,
            hafiz_id=hafiz_id,
            mode_code=WEEKLY_REPS_MODE_CODE,
            revision_date="2024-01-15",
            rating=1,
        )

        update_rep_item(rev)

        updated_item = hafizs_items(where=f"item_id={item_id}")[0]
        assert updated_item.mode_code == FORTNIGHTLY_REPS_MODE_CODE
        assert updated_item.next_interval == 14

        revisions.xtra()
        hafizs_items.xtra()

    def test_fortnightly_graduates_with_custom_threshold_5(self, graduation_test_hafiz):
        """Item with custom_fortnightly_threshold=5 graduates to Monthly after 5 reviews."""
        from database import hafizs, hafizs_items, revisions

        hafiz_id = graduation_test_hafiz["hafiz_id"]
        items_list = graduation_test_hafiz["items"]
        test_item = items_list[9]
        item_id = test_item.item_id

        revisions.xtra(hafiz_id=hafiz_id)
        hafizs_items.xtra(hafiz_id=hafiz_id)

        # Set item to Fortnightly mode with custom threshold of 5
        hafizs_items.update({
            "mode_code": FORTNIGHTLY_REPS_MODE_CODE,
            "next_interval": 14,
            "next_review": "2024-01-15",
            "memorized": True,
            "custom_fortnightly_threshold": 5,
        }, test_item.id)

        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Add 4 revisions
        for i in range(4):
            revisions.insert(
                item_id=item_id,
                hafiz_id=hafiz_id,
                mode_code=FORTNIGHTLY_REPS_MODE_CODE,
                revision_date=f"2023-{11+i//2:02d}-{1+(i%2)*14:02d}",
                rating=1,
            )

        # 5th revision triggers graduation
        rev = revisions.insert(
            item_id=item_id,
            hafiz_id=hafiz_id,
            mode_code=FORTNIGHTLY_REPS_MODE_CODE,
            revision_date="2024-01-15",
            rating=1,
        )

        update_rep_item(rev)

        updated_item = hafizs_items(where=f"item_id={item_id}")[0]
        assert updated_item.mode_code == MONTHLY_REPS_MODE_CODE
        assert updated_item.next_interval == 30

        revisions.xtra()
        hafizs_items.xtra()

    def test_monthly_graduates_with_custom_threshold_12(self, graduation_test_hafiz):
        """Item with custom_monthly_threshold=12 graduates to Full Cycle after 12 reviews."""
        from database import hafizs, hafizs_items, revisions

        hafiz_id = graduation_test_hafiz["hafiz_id"]
        items_list = graduation_test_hafiz["items"]
        test_item = items_list[10]
        item_id = test_item.item_id

        revisions.xtra(hafiz_id=hafiz_id)
        hafizs_items.xtra(hafiz_id=hafiz_id)

        # Set item to Monthly mode with custom threshold of 12
        hafizs_items.update({
            "mode_code": MONTHLY_REPS_MODE_CODE,
            "next_interval": 30,
            "next_review": "2024-01-15",
            "memorized": True,
            "custom_monthly_threshold": 12,
        }, test_item.id)

        hafizs.update({"current_date": "2024-01-15"}, hafiz_id)

        # Add 11 revisions
        for i in range(11):
            revisions.insert(
                item_id=item_id,
                hafiz_id=hafiz_id,
                mode_code=MONTHLY_REPS_MODE_CODE,
                revision_date=f"2023-{1+i:02d}-15",
                rating=1,
            )

        # 12th revision triggers graduation
        rev = revisions.insert(
            item_id=item_id,
            hafiz_id=hafiz_id,
            mode_code=MONTHLY_REPS_MODE_CODE,
            revision_date="2024-01-15",
            rating=1,
        )

        update_rep_item(rev)

        updated_item = hafizs_items(where=f"item_id={item_id}")[0]
        assert updated_item.mode_code == FULL_CYCLE_MODE_CODE
        assert updated_item.next_interval is None
        assert updated_item.memorized == 1

        revisions.xtra()
        hafizs_items.xtra()
