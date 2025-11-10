"""
Phase 0: Smoke Test

Verifies basic setup and auth beforeware.
"""

from playwright.sync_api import expect


def test_home_page_redirects_to_login(page):
    """
    RED: Home page redirects unauthenticated users to login.

    Expected behavior (from master):
    - User visits "/" without authentication
    - Auth beforeware redirects to "/users/login"
    - Login page displays
    """
    page.goto("http://localhost:5001/")

    expect(page).to_have_url("http://localhost:5001/users/login")
    expect(page.locator("h1")).to_contain_text("Login")
