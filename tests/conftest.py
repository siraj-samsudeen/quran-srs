"""
Pytest configuration for Quran SRS tests.

Sets ENV=test before app imports and provides Playwright fixtures.
"""

import os
import pytest
from playwright.sync_api import sync_playwright

# Set test environment before any imports that use globals.py
os.environ["ENV"] = "test"


@pytest.fixture(scope="session")
def browser():
    """Browser instance shared across all tests (headed Chrome)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser):
    """New page for each test (ensures isolation)."""
    context = browser.new_context(base_url="http://localhost:5001")
    page = context.new_page()
    yield page
    context.close()
