"""
E2E Test Fixtures with pytest marker-based authentication.

Fixtures automatically configure page based on test markers:
- @pytest.mark.requires_hafiz(hafiz_id=1) - Auto-login and select hafiz
"""

import os
import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def page(page, request):
    """Auto-configure page based on test markers."""

    # Check for authentication markers
    hafiz_marker = request.node.get_closest_marker("requires_hafiz")

    if hafiz_marker:
        hafiz_id = hafiz_marker.kwargs.get("hafiz_id", 1)
        email = os.getenv("TEST_EMAIL")
        password = os.getenv("TEST_PASSWORD")

        # Login as user
        page.goto("/users/login")
        page.fill("input[name='email']", email)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")

        # Select hafiz by ID
        page.click(f"button[data-testid='switch-hafiz-{hafiz_id}']")

        # Wait for home page
        page.wait_for_load_state("networkidle")

    yield page
