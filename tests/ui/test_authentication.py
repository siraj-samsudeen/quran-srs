"""
Phase 1: User Authentication

Tests for user signup, login, and logout flows.
"""

from playwright.sync_api import expect


def test_signup_page_displays_form(page):
    # User visits signup page
    page.goto("http://localhost:5001/users/signup")

    # Page displays "User Registration" heading
    expect(page.get_by_role("heading", name="User Registration")).to_be_visible()

    # Form contains Name input field
    expect(page.get_by_label("Name")).to_be_visible()

    # Form contains Email input field
    expect(page.get_by_label("Email")).to_be_visible()

    # Form contains Password input field
    expect(page.get_by_label("Password", exact=True)).to_be_visible()

    # Form contains Confirm Password input field
    expect(page.get_by_label("Confirm Password")).to_be_visible()

    # Form contains Signup button
    expect(page.get_by_role("button", name="Signup")).to_be_visible()

    # Page shows link to login for existing users
    expect(page.get_by_role("link", name="Login")).to_be_visible()
