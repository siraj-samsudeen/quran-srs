"""
Smoke test to verify Playwright and authentication setup is working.
"""

from playwright.sync_api import expect


def test_user_can_login(page, db_connection):
    """
    Smoke test: Verify basic login flow works end-to-end.

    This validates:
    - Playwright is installed correctly
    - Browser launches successfully
    - FastHTML server is running
    - Database connection works
    - Authentication flow works
    - Session management works

    UI Testing Rules (Phoenix-style):
    - Setup: Can seed test data via DB (arrange phase)
    - Action: Interact through browser only
    - Assertion: Verify UI elements only (no DB assertions)
    """
    # Arrange: Create test user via DB (setup is allowed)
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO users (id, email, password, name)
        VALUES (999, 'smoke_test@example.com', 'testpass123', 'Smoke Test User')
    """)
    db_connection.commit()

    # Act: Login via UI (browser interactions)
    page.goto("/users/login")
    page.fill("input[name='email']", "smoke_test@example.com")
    page.fill("input[name='password']", "testpass123")
    page.click("button[type='submit']")

    # Assert: Verify UI shows we're logged in (no DB assertions!)
    # After login, should redirect to hafiz selection page
    expect(page).to_have_url("http://localhost:5001/users/hafiz_selection")

    # Verify we see the hafiz selection page title
    expect(page.locator("text=Hafiz Selection")).to_be_visible()

    # Cleanup: Remove test user
    cursor.execute("DELETE FROM users WHERE id = 999")
    db_connection.commit()
