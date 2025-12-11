import os
import pytest
from dotenv import load_dotenv

# Set test environment BEFORE any imports
os.environ["ENV"] = "test"

# Load .env file
load_dotenv()


@pytest.fixture(scope="session")
def base_url():
    """Override pytest-playwright's base_url with our env var."""
    return os.getenv("BASE_URL", "http://localhost:5001")
