"""
Smoke test to verify Playwright setup is working.
"""

from playwright.sync_api import expect


def test_can_navigate_to_login_page(page):
    """
    Smoke test: Verify we can navigate to the login page.

    This is the minimal test to verify:
    - Playwright is installed correctly
    - Browser launches successfully
    - FastHTML server is running
    - Basic page navigation works
    """
    # Navigate to login page
    page.goto("/users/login")

    # Verify we're on the login page
    expect(page).to_have_url("http://localhost:5001/users/login")

    # Verify login form exists
    expect(page.locator("input[name='email']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()
