import os
import pytest
import lxml.html
from dotenv import load_dotenv
from starlette.testclient import TestClient

# Set test environment before importing app
os.environ["ENV"] = "test"
load_dotenv()


# =============================================================================
# E2E Test Fixtures (Playwright)
# =============================================================================


@pytest.fixture(scope="session")
def base_url():
    """Override pytest-playwright's base_url with our env var."""
    return os.getenv("BASE_URL", "http://localhost:5001")


# =============================================================================
# Integration Test Fixtures (TestClient)
# =============================================================================


@pytest.fixture
def client():
    """Create test client for the app."""
    from main import app
    return TestClient(app)


@pytest.fixture
def auth_session(client):
    """Login and return authenticated session cookies."""
    response = client.post("/users/login", data={
        "email": os.getenv("TEST_EMAIL"),
        "password": os.getenv("TEST_PASSWORD"),
    })
    return response.cookies


@pytest.fixture
def hafiz_session(client, auth_session):
    """Select hafiz and return session with both user and hafiz auth."""
    response = client.post(
        "/users/hafiz_selection",
        data={"current_hafiz_id": "1"},
        cookies=auth_session,
        follow_redirects=False,
    )
    # Merge cookies from both auth and hafiz selection
    all_cookies = {**auth_session, **response.cookies}
    return all_cookies


@pytest.fixture
def parse_html():
    """Parse HTML response to lxml tree for XPath queries."""
    def _parse(response):
        return lxml.html.fromstring(response.text)
    return _parse
