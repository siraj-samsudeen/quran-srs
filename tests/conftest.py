import os
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
