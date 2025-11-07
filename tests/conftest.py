"""
Pytest configuration and fixtures for Quran SRS tests.
"""

import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def browser():
    """
    Browser instance shared across all tests.
    Uses headless Chromium for speed.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser):
    """
    New page for each test (ensures test isolation).
    Base URL set to localhost:5001.
    """
    context = browser.new_context(base_url="http://localhost:5001")
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def db_connection():
    """
    Database connection for seeding test data and verification.
    """
    import sqlite3
    conn = sqlite3.connect("data/quran_v10.db")
    yield conn
    conn.close()
