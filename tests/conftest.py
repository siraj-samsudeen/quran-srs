import os
import time
import pytest
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# No ENV setting - all tests use dev database with master data
# Integration tests will clean up test users, E2E tests use TEST_USER


@pytest.fixture(scope="session")
def base_url():
    """Override pytest-playwright's base_url with our env var."""
    return os.getenv("BASE_URL", "http://localhost:5001")


# === Integration Test Fixtures ===

@pytest.fixture
def auth_with_memorized_pages(client):
    """Authenticated hafiz with memorized pages (shared fixture for integration tests).

    Creates:
    - Test user with unique email
    - Test hafiz
    - Marks first 15 pages as memorized in FC mode

    Yields dict with: client, user_id, hafiz_id, email, memorized_item_ids

    Cleanup: Deletes test user (cascades to hafizs, hafizs_items, revisions)
    """
    from app.users_model import create_user
    from database import hafizs, hafizs_items, users

    # Create unique test user
    test_email = f"test_{int(time.time() * 1000)}@example.com"
    user_id = create_user(test_email, "password123", "Test User")

    # Login
    login_response = client.post(
        "/users/login",
        data={"email": test_email, "password": "password123"},
        follow_redirects=False,
    )
    client.cookies = login_response.cookies

    # Create and select hafiz
    client.post("/hafiz/add", data={"name": "Test Hafiz"}, follow_redirects=False)
    user_hafizs = hafizs(where=f"user_id={user_id}")
    hafiz_id = user_hafizs[0].id
    select_response = client.post(
        "/hafiz/selection",
        data={"current_hafiz_id": hafiz_id},
        follow_redirects=False,
    )
    client.cookies = select_response.cookies

    # Mark pages as memorized for Full Cycle eligibility
    memorized_items = hafizs_items(where=f"hafiz_id={hafiz_id}")[:15]
    for item in memorized_items:
        hafizs_items.update({"memorized": True, "mode_code": "FC"}, item.id)

    yield {
        "client": client,
        "user_id": user_id,
        "hafiz_id": hafiz_id,
        "email": test_email,
        "memorized_item_ids": [item.item_id for item in memorized_items],
    }

    # Cleanup
    users.delete(user_id)
