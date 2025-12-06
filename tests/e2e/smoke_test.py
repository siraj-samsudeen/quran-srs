"""
Phase 0: Smoke Test

Verifies basic setup and auth beforeware.
"""

from playwright.sync_api import expect


def test_home_page_redirects_to_login(page):
    # User visits home page without authentication
    page.goto("http://localhost:5001/")

    # Auth beforeware redirects to login page
    expect(page).to_have_url("http://localhost:5001/users/login")

    # Login page displays
    expect(page.get_by_role("heading", name="Login")).to_be_visible()
