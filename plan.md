# Playwright Python Testing Infrastructure Setup Plan

## Overview

**Goal**: Set up Python-based UI and Backend testing following Phoenix LiveView patterns, providing code coverage metrics for safe refactoring of the FastHTML application.

**Key Principles**:
- **Phoenix LiveView-Inspired**: Two-layer approach (UI tests + Backend tests)
- **UI tests browser-only assertions**: Setup via DB allowed, but NO database assertions
- **Backend tests for logic**: Direct function calls with database assertions
- **Minimal test suite**: Test each feature once, at the right layer
- **Focused tests** (not journey tests) for clear failure messages
- **Fast execution**: Target ~20-30s for UI suite, <5s for Backend

**Testing Philosophy**:
- Each feature tested once, no duplication across layers
- E2E tests are the source of truth for user-facing behavior
- Integration tests added reactively when E2E tests become slow or coverage shows gaps
- Unit tests added only for critical pure functions

---

## Prerequisites

✅ **Completed**:
- Branch `playwright-testing` created from updated master
- Dependencies installed: pytest, pytest-playwright, pytest-cov
- Chromium browser installed
- Test directories created: `tests/`, `tests/helpers/`

⏸️ **Blocked**: Waiting for pending changes to be merged to master

---

## File Structure (Phoenix LiveView Pattern)

```
tests/
├── ui/                            # UI Tests (Phoenix-style)
│   ├── conftest.py                # Playwright fixtures (browser, page)
│   ├── test_smoke.py              # ✅ Smoke test (login flow)
│   ├── test_hafiz_crud.py         # Hafiz CRUD operations
│   ├── test_review_flow.py        # Rating dropdown + HTMX
│   └── test_close_date.py         # Close Date button behavior
│
├── backend/                       # Backend Tests (Phoenix-style)
│   ├── test_mode_transitions.py   # Mode graduation logic
│   ├── test_srs_algorithm.py      # SRS interval calculations
│   └── test_close_date_engine.py  # Close Date processing logic
│
├── conftest.py                    # Shared fixtures (ENV=test, db_connection)
│
└── helpers/                       # Shared test helpers
    ├── database.py                # DB seeding helpers
    ├── auth.py                    # Login/navigation helpers (UI only)
    └── assertions.py              # Reusable assertions
```

**Key Differences from Traditional E2E/Integration:**
- **UI Tests**: Browser-based, UI-only assertions (like Phoenix LiveView tests)
- **Backend Tests**: Pure Python, database assertions allowed (like Phoenix Context tests)
- **No "integration" or "unit" terminology**: Using Phoenix's UI/Backend naming for clarity

---

## Step-by-Step Implementation Plan

### Phase 1: E2E Test Infrastructure (Foundation)

**Goal**: Set up the core testing infrastructure and write 6-8 E2E tests covering all critical user flows.

**Timeline**: 4-6 hours

---

#### Step 1.1: Create pytest configuration
**File**: `tests/conftest.py`

**Purpose**:
- Configure Playwright browser fixtures
- Set up database helper fixtures
- Configure test cleanup/teardown

**Implementation**:
```python
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser():
    """Browser instance shared across all tests"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser):
    """New page for each test (isolation)"""
    context = browser.new_context(base_url="http://localhost:5001")
    page = context.new_page()
    yield page
    context.close()

@pytest.fixture
def db_connection():
    """Database connection for seeding test data"""
    import sqlite3
    conn = sqlite3.connect("data/quran_v10.db")
    yield conn
    conn.close()
```

**Why this approach**:
- Session-scoped browser: Faster (reuse browser instance)
- Function-scoped page: Test isolation (each test gets fresh page)
- Database fixture: Direct DB access for fast test setup

---

#### Step 1.2: Create database helper functions
**File**: `tests/helpers/database.py`

**Purpose**:
- **Setup**: Seed test data directly in database (faster than UI navigation)
- **Cleanup**: Delete test data after tests (CASCADE handles related records)
- **Verification**: Query database for assertions (dual UI + DB verification)

**Important**: Use direct SQL helpers (NOT Factory Boy) for simplicity with small test suites.

**Implementation**:
```python
import sqlite3
from datetime import datetime

def create_test_hafiz(conn, name=None, user_id=1, daily_capacity=5):
    """
    Create a test hafiz and return its ID

    Args:
        conn: Database connection
        name: Hafiz name (auto-generated with timestamp if None)
        user_id: Owner user ID (default: 1)
        daily_capacity: Daily revision capacity

    Returns:
        int: Created hafiz_id
    """
    if name is None:
        name = f"E2E Test {int(datetime.now().timestamp() * 1000)}"

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO hafizs (name, user_id, daily_capacity, current_date) VALUES (?, ?, ?, DATE('now'))",
        (name, user_id, daily_capacity)
    )
    conn.commit()
    return cursor.lastrowid

def delete_hafiz_by_name(conn, name):
    """Delete hafiz and cascade delete related records"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM hafizs WHERE name = ?", (name,))
    conn.commit()
    return cursor.rowcount > 0

def get_hafiz_by_name(conn, name):
    """Retrieve hafiz details by name"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hafizs WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    return None

def seed_item_in_mode(conn, hafiz_id, item_id, mode_code, **kwargs):
    """
    Create or update hafizs_items record

    Args:
        conn: Database connection
        hafiz_id: Hafiz ID
        item_id: Item ID
        mode_code: Mode code ('FC', 'NM', 'DR', 'WR', 'SR')
        **kwargs: Additional fields (memorized, next_review, etc.)
    """
    # Check if record exists
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM hafizs_items WHERE hafiz_id = ? AND item_id = ?",
        (hafiz_id, item_id)
    )
    existing = cursor.fetchone()

    if existing:
        # Update existing record
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()] + ["mode_code = ?"])
        values = list(kwargs.values()) + [mode_code, existing[0]]
        cursor.execute(
            f"UPDATE hafizs_items SET {set_clause} WHERE id = ?",
            values
        )
    else:
        # Insert new record
        fields = ["hafiz_id", "item_id", "mode_code"] + list(kwargs.keys())
        placeholders = ", ".join(["?"] * len(fields))
        values = [hafiz_id, item_id, mode_code] + list(kwargs.values())
        cursor.execute(
            f"INSERT INTO hafizs_items ({', '.join(fields)}) VALUES ({placeholders})",
            values
        )

    conn.commit()

def seed_revision(conn, hafiz_id, item_id, mode_code, date, rating):
    """Insert a revision record"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO revisions (hafiz_id, item_id, mode_code, revision_date, rating) VALUES (?, ?, ?, ?, ?)",
        (hafiz_id, item_id, mode_code, date, rating)
    )
    conn.commit()

def set_hafiz_date(conn, hafiz_id, date_string):
    """Update hafiz's current_date"""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE hafizs SET current_date = ? WHERE id = ?",
        (date_string, hafiz_id)
    )
    conn.commit()
```

**Why this approach**:
- Direct DB seeding is faster than clicking through UI (10ms vs 2000ms)
- Timestamp-based names prevent test collisions
- Simple SQL is easier to maintain than Factory Boy for small suites
- CASCADE DELETE handles cleanup automatically

---

#### Step 1.3: Create authentication helper functions
**File**: `tests/helpers/auth.py`

**Purpose**:
- Encapsulate common user flows (DRY principle)
- Reduce test boilerplate
- Make tests more readable

**Implementation**:
```python
def login(page, email="seerajthepoet@gmail.com", password="test"):
    """
    Login to the application

    Args:
        page: Playwright page object
        email: User email
        password: User password
    """
    page.goto("/users/login")
    page.fill("input[name='email']", email)
    page.fill("input[name='password']", password)
    page.click("button:has-text('Login')")

    # Wait for redirect to hafiz selection
    page.wait_for_url("**/users/hafiz_selection")

def switch_hafiz(page, hafiz_name):
    """
    Switch to a specific hafiz by name

    Args:
        page: Playwright page object
        hafiz_name: Name of hafiz to switch to
    """
    # Navigate to hafiz selection if not already there
    if "/users/hafiz_selection" not in page.url:
        page.goto("/users/hafiz_selection")

    # Click the hafiz name button
    page.click(f"button[data-testid='switch-{hafiz_name}-hafiz-button']")

    # Wait for redirect to home
    page.wait_for_url("**/")
```

**Why this approach**:
- Encapsulates common flows (DRY principle)
- Uses data-testid for stability (resistant to UI text changes)
- Clear function signatures for readability

---

#### Step 1.4: Create assertion helper functions
**File**: `tests/helpers/assertions.py`

**Purpose**:
- Reusable assertions for common checks
- Better error messages than raw asserts

**Implementation**:
```python
def assert_hafiz_exists_in_db(conn, name):
    """Assert that a hafiz exists in the database"""
    from tests.helpers.database import get_hafiz_by_name

    hafiz = get_hafiz_by_name(conn, name)
    assert hafiz is not None, f"Hafiz '{name}' not found in database"
    return hafiz

def assert_hafiz_not_in_db(conn, name):
    """Assert that a hafiz does NOT exist in the database"""
    from tests.helpers.database import get_hafiz_by_name

    hafiz = get_hafiz_by_name(conn, name)
    assert hafiz is None, f"Hafiz '{name}' should not exist in database but was found"

def assert_hafiz_visible_on_page(page, hafiz_name):
    """Assert hafiz is visible in the hafiz selection list"""
    locator = page.locator(f"button[data-testid='switch-{hafiz_name}-hafiz-button']")
    assert locator.is_visible(), f"Hafiz '{hafiz_name}' not visible on page"

def assert_hafiz_not_visible_on_page(page, hafiz_name):
    """Assert hafiz is NOT visible in the hafiz selection list"""
    locator = page.locator(f"button[data-testid='switch-{hafiz_name}-hafiz-button']")
    assert not locator.is_visible(), f"Hafiz '{hafiz_name}' should not be visible on page"

def assert_item_in_mode(conn, hafiz_id, item_id, expected_mode):
    """Assert that an item is in a specific mode"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT mode_code FROM hafizs_items WHERE hafiz_id = ? AND item_id = ?",
        (hafiz_id, item_id)
    )
    row = cursor.fetchone()
    assert row is not None, f"Item {item_id} not found for hafiz {hafiz_id}"

    actual_mode = row[0]
    assert actual_mode == expected_mode, \
        f"Item {item_id} expected in mode '{expected_mode}', but was in '{actual_mode}'"
```

**Why this approach**:
- Descriptive error messages aid debugging
- Centralized assertion logic (easier to update if UI changes)
- Reusable across multiple tests

---

### Phase 2: Write E2E Tests (Core User Flows)

**Goal**: Write 6-8 focused E2E tests covering all critical user workflows.

**Strategy**: Hybrid approach - Arrange (DB setup), Act (UI), Assert (UI + DB)

---

#### Step 2.1: Hafiz CRUD Tests (3 tests)
**File**: `tests/e2e/test_hafiz_crud.py`

**Purpose**: Test user can manage hafiz profiles through the UI.

**Implementation**:
```python
import pytest
from playwright.sync_api import expect
from tests.helpers.auth import login, switch_hafiz
from tests.helpers.database import create_test_hafiz, delete_hafiz_by_name
from tests.helpers.assertions import (
    assert_hafiz_exists_in_db,
    assert_hafiz_not_in_db,
    assert_hafiz_visible_on_page,
    assert_hafiz_not_visible_on_page
)

class TestHafizCRUD:
    """Focused tests for Hafiz CRUD operations"""

    def test_create_hafiz_via_ui(self, page, db_connection):
        """Test: User can create a new hafiz through the UI"""
        # Arrange
        login(page)
        test_name = f"E2E Test {int(datetime.now().timestamp() * 1000)}"

        # Act
        page.fill("input[name='name']", test_name)
        page.fill("input[name='daily_capacity']", "5")
        page.click("button:has-text('Add Hafiz')")

        # Assert - UI shows new hafiz
        assert_hafiz_visible_on_page(page, test_name)

        # Assert - Database has new hafiz
        assert_hafiz_exists_in_db(db_connection, test_name)

        # Cleanup
        delete_hafiz_by_name(db_connection, test_name)

    def test_switch_hafiz(self, page, db_connection):
        """Test: User can switch to a different hafiz"""
        # Arrange - create test hafiz in DB (faster than UI)
        test_name = f"E2E Test {int(datetime.now().timestamp() * 1000)}"
        hafiz_id = create_test_hafiz(db_connection, name=test_name)

        login(page)

        # Act - switch to test hafiz
        switch_hafiz(page, test_name)

        # Assert - redirected to home page
        expect(page).to_have_url("/")

        # Assert - current hafiz indicator shows test hafiz
        # (Assuming there's a UI element showing current hafiz name)
        expect(page.locator("text=Current Hafiz:")).to_contain_text(test_name)

        # Cleanup
        delete_hafiz_by_name(db_connection, test_name)

    def test_delete_hafiz(self, page, db_connection):
        """Test: User can delete a non-current hafiz"""
        # Arrange - create two test hafizs
        hafiz1_name = f"E2E Test 1 {int(datetime.now().timestamp() * 1000)}"
        hafiz2_name = f"E2E Test 2 {int(datetime.now().timestamp() * 1000)}"

        create_test_hafiz(db_connection, name=hafiz1_name)
        create_test_hafiz(db_connection, name=hafiz2_name)

        login(page)

        # Switch to hafiz1 (makes it current)
        switch_hafiz(page, hafiz1_name)

        # Navigate back to hafiz selection
        page.goto("/users/hafiz_selection")

        # Act - delete hafiz2 (not current)
        delete_button = page.locator(f"button[data-testid='delete-{hafiz2_name}-button']")

        # Handle confirmation dialog
        page.on("dialog", lambda dialog: dialog.accept())
        delete_button.click()

        # Wait for HTMX to update
        page.wait_for_timeout(1000)

        # Assert - hafiz2 not visible in UI
        assert_hafiz_not_visible_on_page(page, hafiz2_name)

        # Assert - hafiz2 not in database
        assert_hafiz_not_in_db(db_connection, hafiz2_name)

        # Cleanup
        delete_hafiz_by_name(db_connection, hafiz1_name)

```

**Note**: Removed `test_cannot_delete_current_hafiz` to keep suite minimal. Business logic prevents deletion, UI test not critical.

---

#### Step 2.2: Review Flow Test (1 test)
**File**: `tests/e2e/test_review_flow.py`

**Purpose**: Test rating dropdown and HTMX auto-submit behavior.

**Implementation**:
```python
import pytest
from playwright.sync_api import expect
from datetime import datetime
from tests.helpers.auth import login, switch_hafiz
from tests.helpers.database import create_test_hafiz, seed_item_in_mode, set_hafiz_date

def test_review_item_with_rating_dropdown(page, db_connection):
    """Test: User can review an item via rating dropdown with HTMX auto-submit"""
    # Arrange - Setup test data via DB (fast)
    test_name = f"E2E Test {int(datetime.now().timestamp() * 1000)}"
    hafiz_id = create_test_hafiz(db_connection, name=test_name)

    # Seed item in Daily Reps mode, due today
    seed_item_in_mode(
        db_connection,
        hafiz_id,
        item_id=1,
        mode_code='DR',
        next_review='2025-11-07',
        memorized=True
    )
    set_hafiz_date(db_connection, hafiz_id, '2025-11-07')

    # Act - Use the UI to perform review
    login(page)
    switch_hafiz(page, test_name)

    # Select "Good" rating (value=1)
    page.select_option("select[data-testid='rating-1']", "1")

    # Wait for HTMX auto-submit
    page.wait_for_timeout(1000)

    # Assert - UI shows visual feedback (green row for good rating)
    row = page.locator("tr[data-item-id='1']")
    expect(row).to_have_class(/bg-green/)

    # Assert - DB has revision record
    cursor = db_connection.cursor()
    cursor.execute(
        "SELECT * FROM revisions WHERE hafiz_id=? AND item_id=? AND rating=1",
        (hafiz_id, 1)
    )
    revision = cursor.fetchone()
    assert revision is not None, "Revision record should exist in DB"

    # Cleanup
    delete_hafiz_by_name(db_connection, test_name)
```

**Why this test**:
- Tests HTMX auto-submit (UI-specific behavior)
- Dual assertion (UI feedback + DB persistence)
- Don't need 5 separate tests per mode (rating dropdown is same component)

---

#### Step 2.3: Close Date Tests (2-3 tests)
**File**: `tests/e2e/test_close_date.py`

**Purpose**: Test the "engine" of the app - Close Date processing and mode graduations.

**Implementation**:
```python
import pytest
from playwright.sync_api import expect
from datetime import datetime
from tests.helpers.auth import login, switch_hafiz
from tests.helpers.database import (
    create_test_hafiz,
    seed_item_in_mode,
    seed_revision,
    set_hafiz_date,
    delete_hafiz_by_name
)
from tests.helpers.assertions import assert_item_in_mode

def test_close_date_advances_date(page, db_connection):
    """Test: Close Date button advances hafiz current_date by 1 day"""
    # Arrange
    test_name = f"E2E Test {int(datetime.now().timestamp() * 1000)}"
    hafiz_id = create_test_hafiz(db_connection, name=test_name)
    set_hafiz_date(db_connection, hafiz_id, '2025-11-07')

    # Act
    login(page)
    switch_hafiz(page, test_name)
    page.click("button:has-text('Close Date')")

    # Handle confirmation dialog
    page.on("dialog", lambda dialog: dialog.accept())

    # Wait for processing
    page.wait_for_timeout(1000)

    # Assert - UI shows new date
    expect(page.locator("text=Current Date: 2025-11-08")).to_be_visible()

    # Assert - DB updated
    cursor = db_connection.cursor()
    cursor.execute("SELECT current_date FROM hafizs WHERE id=?", (hafiz_id,))
    current_date = cursor.fetchone()[0]
    assert current_date == '2025-11-08', "Date should advance by 1 day"

    # Cleanup
    delete_hafiz_by_name(db_connection, test_name)


def test_close_date_graduates_multiple_items(page, db_connection):
    """
    Test: Close Date processes multiple mode graduations in one operation
    This is the "engine test" - verifies the core workflow
    """
    # Arrange - Setup 3 items ready to graduate
    test_name = f"E2E Test {int(datetime.now().timestamp() * 1000)}"
    hafiz_id = create_test_hafiz(db_connection, name=test_name)
    set_hafiz_date(db_connection, hafiz_id, '2025-11-07')

    # Item 1: NM mode → should graduate to DR
    seed_item_in_mode(db_connection, hafiz_id, 1, 'NM', memorized=False)
    seed_revision(db_connection, hafiz_id, 1, 'NM', '2025-11-07', rating=1)

    # Item 2: DR mode with 7 reviews → should graduate to WR
    seed_item_in_mode(db_connection, hafiz_id, 2, 'DR', memorized=True)
    for i in range(7):
        seed_revision(db_connection, hafiz_id, 2, 'DR', f'2025-11-0{i+1}', rating=1)

    # Item 3: WR mode with 7 reviews → should graduate to FC
    seed_item_in_mode(db_connection, hafiz_id, 3, 'WR', memorized=True)
    for i in range(7):
        seed_revision(db_connection, hafiz_id, 3, 'WR', f'2025-10-{i+1:02d}', rating=1)

    # Act
    login(page)
    switch_hafiz(page, test_name)
    page.click("button:has-text('Close Date')")
    page.on("dialog", lambda dialog: dialog.accept())
    page.wait_for_timeout(2000)  # Wait for processing

    # Assert - All items graduated correctly
    assert_item_in_mode(db_connection, hafiz_id, 1, 'DR')  # NM → DR
    assert_item_in_mode(db_connection, hafiz_id, 2, 'WR')  # DR → WR
    assert_item_in_mode(db_connection, hafiz_id, 3, 'FC')  # WR → FC

    # Cleanup
    delete_hafiz_by_name(db_connection, test_name)


def test_bad_rating_demotes_to_srs_on_close_date(page, db_connection):
    """Test: Item with bad rating moves to SRS mode when date is closed"""
    # Arrange
    test_name = f"E2E Test {int(datetime.now().timestamp() * 1000)}"
    hafiz_id = create_test_hafiz(db_connection, name=test_name)
    set_hafiz_date(db_connection, hafiz_id, '2025-11-07')

    # Item in FC mode with bad_streak=0
    seed_item_in_mode(
        db_connection,
        hafiz_id,
        item_id=1,
        mode_code='FC',
        next_review='2025-11-07',
        bad_streak=0,
        memorized=True
    )

    # Act - Review with Bad rating
    login(page)
    switch_hafiz(page, test_name)
    page.select_option("select[data-testid='rating-1']", "-1")  # Bad rating
    page.wait_for_timeout(1000)

    # Close Date
    page.click("button:has-text('Close Date')")
    page.on("dialog", lambda dialog: dialog.accept())
    page.wait_for_timeout(2000)

    # Assert - Item moved to SRS mode
    assert_item_in_mode(db_connection, hafiz_id, 1, 'SR')

    # Assert - Bad streak incremented
    cursor = db_connection.cursor()
    cursor.execute(
        "SELECT bad_streak FROM hafizs_items WHERE hafiz_id=? AND item_id=?",
        (hafiz_id, 1)
    )
    bad_streak = cursor.fetchone()[0]
    assert bad_streak == 1, "Bad streak should increment"

    # Cleanup
    delete_hafiz_by_name(db_connection, test_name)
```

**Why these tests**:
- **Test 1**: Simplest Close Date behavior (date increment)
- **Test 2**: "Engine test" - all mode transitions at once (efficient)
- **Test 3**: SRS demotion logic (critical business rule)

**Total E2E Suite**: 6-7 tests covering all critical user flows.

---

### Phase 3: Coverage Analysis & Decision Point

**Goal**: Run E2E tests, analyze coverage, decide if integration tests are needed.

**Timeline**: 30 minutes

---

#### Step 3.1: Add coverage configuration
**File**: `pyproject.toml` (append to existing)

**Configuration**:
```toml
[tool.coverage.run]
source = [
    "main.py",
    "globals.py",
    "utils.py",
    "app/"
]
omit = [
    "tests/*",
    "migrations/*",
    "public/*"
]
branch = true

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false

[tool.coverage.html]
directory = "htmlcov"
```

**Why this configuration**:
- `source`: Only measure coverage for application code
- `omit`: Exclude tests, migrations, static files
- `branch`: Track branch coverage (if/else paths)
- `show_missing`: Show exact lines not covered
- `htmlcov`: Generate HTML report for visual review

---

#### Step 3.2: Run E2E tests with coverage

**Commands**:
```bash
# Start server in one terminal
uv run main.py

# Run tests in another terminal
uv run pytest tests/e2e --cov --cov-report=html --cov-report=term-missing
```

**Expected output**:
```
tests/e2e/test_hafiz_crud.py::test_create_hafiz_via_ui ........... PASSED (3.2s)
tests/e2e/test_hafiz_crud.py::test_switch_hafiz ................... PASSED (2.8s)
tests/e2e/test_hafiz_crud.py::test_delete_hafiz ................... PASSED (3.1s)
tests/e2e/test_review_flow.py::test_review_item ................... PASSED (2.5s)
tests/e2e/test_close_date.py::test_close_date_advances_date ....... PASSED (2.9s)
tests/e2e/test_close_date.py::test_close_date_graduates ........... PASSED (4.2s)
tests/e2e/test_close_date.py::test_bad_rating_to_srs .............. PASSED (3.8s)

============= 7 passed in 22.5s =============

Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
main.py                   120     28    77%   45-52, 89-95
app/users_controller.py    80     15    81%   67-72
app/revision.py           150     35    77%   ...
app/fixed_reps.py          95     20    79%   ...
app/srs_reps.py           110     25    77%   ...
-----------------------------------------------------
TOTAL                     850    180    79%
```

---

#### Step 3.3: Analyze coverage and decide next steps

**Decision Tree**:

**Scenario A: High Coverage (>75%), Fast Tests (<30s)**
→ ✅ **STOP HERE. E2E tests are sufficient.**
- You have confidence in user-facing features
- Tests are fast enough for TDD
- No need for integration tests

**Scenario B: Good Coverage (65-75%), But Specific Gaps**
→ ⚠️ **Consider selective integration tests**
- Example: SRS interval calculation has 10 edge cases but only 2 covered
- Action: Add `tests/integration/test_srs_intervals.py` for those 8 edge cases
- Keep E2E as source of truth, integration for exhaustive edge case coverage

**Scenario C: Low Coverage (<65%) in Critical Areas**
→ ❌ **Need integration tests for backend logic**
- Example: Close Date logic has 50% coverage
- Action: Extract `update_rep_item()`, `update_hafiz_item_for_srs()` to integration tests
- E2E tests the UI, integration tests the backend functions

**Scenario D: Tests Too Slow (>60s)**
→ ❌ **Extract slow parts to integration tests**
- Example: `test_close_date_graduates_multiple_items` takes 10s
- Action: Move graduation counting logic to integration test (0.5s)
- Keep one E2E test for the UI button behavior

---

#### Step 3.4: Success criteria - When to stop

**Minimum bar (ship with confidence)**:
- [ ] All E2E tests pass consistently
- [ ] Coverage > 70% overall
- [ ] Critical paths (Close Date, mode transitions) > 80% coverage
- [ ] Test suite runs in < 30s
- [ ] No flaky tests (100% pass rate across 5 runs)

**If these are met, E2E tests alone are sufficient. No integration tests needed.**

---

### Phase 4: Integration Tests (On-Demand Only)

**Only proceed to this phase if Phase 3 analysis shows one of these triggers:**
1. E2E coverage < 70% in critical backend logic
2. E2E tests > 60s runtime
3. Complex algorithm needs exhaustive edge case testing
4. TDD inner loop needs faster feedback for specific module

---

#### Step 4.1: Create integration test structure

**File structure**:
```
tests/integration/
├── test_srs_intervals.py      # SRS algorithm edge cases
├── test_mode_transitions.py   # Graduation counting logic
└── test_close_date_engine.py  # Backend Close Date processing
```

**Example integration test**:
```python
# tests/integration/test_srs_intervals.py
import pytest
from app.srs_reps import calculate_next_interval

def test_srs_interval_increases_on_good_rating():
    """Integration test: SRS algorithm increases interval on good performance"""
    # No UI, no browser - just test the function
    next_interval = calculate_next_interval(
        current_interval=7,
        rating=1,  # Good
        bad_streak=0
    )

    assert next_interval > 7, "Good rating should increase interval"
    assert next_interval <= 14, "Interval shouldn't double immediately"

def test_srs_interval_decreases_on_bad_rating():
    """Integration test: SRS algorithm decreases interval on bad performance"""
    next_interval = calculate_next_interval(
        current_interval=14,
        rating=-1,  # Bad
        bad_streak=1
    )

    assert next_interval < 14, "Bad rating should decrease interval"
    assert next_interval >= 1, "Interval shouldn't go below 1 day"
```

**Why integration tests**:
- Fast (<0.5s per test) for TDD inner loop
- Test backend functions directly (no browser overhead)
- Exhaustive edge case coverage without slow E2E tests
- Clear failure messages (pinpoint exact logic issue)

---

#### Step 4.2: Run combined test suite

**Command**:
```bash
# Run all tests with coverage
uv run pytest --cov --cov-report=html --cov-report=term-missing

# Run only integration tests (fast feedback)
uv run pytest tests/integration -v

# Run only E2E tests (full confidence)
uv run pytest tests/e2e -v
```

**Expected combined output**:
```
tests/integration/test_srs_intervals.py .................... 8 passed (2.1s)
tests/integration/test_mode_transitions.py ................. 5 passed (1.8s)
tests/e2e/test_hafiz_crud.py ............................... 3 passed (9.1s)
tests/e2e/test_review_flow.py .............................. 1 passed (2.5s)
tests/e2e/test_close_date.py ............................... 3 passed (12.8s)

============= 20 passed in 28.3s =============

Name                    Stmts   Miss  Cover
--------------------------------------------
main.py                   120      8    93%
app/fixed_reps.py          95      3    97%
app/srs_reps.py           110      5    95%
--------------------------------------------
TOTAL                     850     40    95%
```

---

## Summary: Testing Strategy

### E2E-First Philosophy

**Start with E2E tests** to understand the big picture and verify user-facing behavior:
1. Write 6-7 E2E tests covering critical flows (Hafiz CRUD, Review, Close Date)
2. Run coverage analysis
3. If coverage > 70% and tests < 30s → STOP (E2E alone is sufficient)
4. If gaps exist → Add integration tests selectively

**Only add integration/unit tests when:**
- E2E coverage < 70% in critical backend logic
- E2E tests too slow (> 60s) for TDD
- Complex algorithms need exhaustive edge case testing
- Specific module needs fast feedback loop for refactoring

### Test Layers & Responsibilities

| Layer | Purpose | When to Use | Example |
|-------|---------|-------------|---------|
| **E2E** | User-facing workflows | Always start here | Login, review flow, Close Date button |
| **Integration** | Backend logic | Only if E2E gaps/slow | SRS algorithm, mode counting |
| **Unit** | Pure utilities | Rarely needed | Date helpers (if complex) |

### Key Design Decisions

**✅ Hybrid E2E Strategy**:
- Arrange: DB seeding (fast setup)
- Act: UI interactions (realistic user behavior)
- Assert: UI + DB verification (full confidence)

**✅ Direct DB Helpers (NOT Factory Boy)**:
- Simple SQL for small test suites (< 20 tests)
- Factory Boy adds overhead for minimal benefit

**✅ Focused Tests (NOT Journey Tests)**:
- Each test covers one specific behavior
- Clear failure messages
- Can run independently

**✅ Test Each Feature Once**:
- E2E tests user workflows
- Integration tests backend logic (if needed)
- No duplication across layers

### Timeline Estimate

**Phase 1: E2E Infrastructure & Tests** (4-6 hours)
- Infrastructure setup (conftest, helpers)
- 6-7 E2E tests (Hafiz CRUD, Review, Close Date)

**Phase 2: Coverage Analysis** (30 minutes)
- Run tests, review coverage
- Decide: Stop or add integration tests?

**Phase 3: Integration Tests** (2-3 hours, only if needed)
- Add based on coverage gaps/speed issues
- Target specific backend functions

**Total**: 4-9 hours depending on coverage results

---

## Wallaby Deprecation

**Current state**: Wallaby (Elixir) tests exist in phoenix_migration worktree

**Migration plan**:
1. Start Playwright E2E tests (this plan)
2. Run both test suites in parallel until coverage parity
3. Compare coverage between Wallaby and Playwright
4. Deprecate Wallaby when Python E2E + integration >= Wallaby coverage
5. Delete phoenix_migration worktree (or keep for Phoenix migration only)

**Note**: Wallaby tests are good, but can't provide Python code coverage. Playwright tests solve this.

---

## Next Steps (After Merge)

1. ✅ Pull latest changes from master
2. ✅ Merge into `playwright-testing` branch
3. ✅ Create conftest.py with basic fixtures
4. ✅ Add ENV-based database configuration
5. ✅ Write smoke test to verify setup works
6. 🔄 Iterate based on feedback

---

## Running Tests

### Setup (One-time)

**Test database created from backup:**
```bash
cp data_backup/quran_v10.db data/quran_test.db
```

**Note**: `data/quran_test.db` is already in `.gitignore` (via `data/` entry), so it won't be committed.

### Running Tests

**Terminal 1: Start FastHTML server in test mode** (required for UI tests)
```bash
ENV=test uv run main.py
```

**Terminal 2: Run tests**
```bash
# Run all tests (UI + Backend)
uv run pytest -v

# Run only UI tests (requires running server)
uv run pytest tests/ui -v

# Run only Backend tests (no server needed, fast!)
uv run pytest tests/backend -v

# Run specific test file
uv run pytest tests/ui/test_smoke.py -v

# Run with coverage
uv run pytest --cov --cov-report=html --cov-report=term-missing
```

**Phoenix-Style Testing Rules**:
- **UI Tests**: Must assert on UI elements only (no DB assertions)
- **Backend Tests**: Can assert on database state directly
- **Both**: Can seed data via DB in setup phase

**How it works:**
- `globals.py` checks `ENV` environment variable
  - `ENV=test` → uses `data/quran_test.db`
  - `ENV=dev` (default) → uses `data/quran_v10.db`
  - `ENV=prod` → uses `data/quran_v10.db`
- `tests/conftest.py` automatically sets `ENV=test` when running pytest
- App and tests both use the same test database for E2E testing

### Resetting Test Database

If test data gets corrupted or you want a fresh start:

```bash
# Delete test DB
rm data/quran_test.db

# Recreate from backup
cp data_backup/quran_v10.db data/quran_test.db

# Or copy from current dev DB (if you want latest schema/data)
cp data/quran_v10.db data/quran_test.db
```

### Environment Variables Summary

| ENV Value | Database Path | Use Case |
|-----------|---------------|----------|
| `test` | `data/quran_test.db` | E2E tests (isolated from dev data) |
| `dev` (default) | `data/quran_v10.db` | Local development |
| `prod` | `data/quran_v10.db` | Production (future: separate path) |

---

## APPENDIX: Comprehensive Test Map & Stubs

This section provides a complete map of all tests needed for the Quran SRS application, organized by feature/mode. Tests are prioritized into phases.

### Phase 1: Core Infrastructure & Critical Flows (6-7 tests)

**START HERE** - These tests cover the minimal set for confidence in user-facing features.

#### 1. Authentication & Hafiz Management (3 tests)

```python
# tests/e2e/test_hafiz_crud.py

def test_create_hafiz_via_ui(page, db_connection):
    """
    Test: User can create a new hafiz profile through the UI

    Steps:
    1. Login with valid credentials
    2. Navigate to hafiz selection page
    3. Fill in hafiz name and daily_capacity
    4. Click "Add Hafiz" button
    5. Verify hafiz appears in selection list (UI)
    6. Verify hafiz exists in database (DB)
    7. Cleanup: Delete test hafiz

    Coverage: Hafiz CRUD, form submission, HTMX partial updates
    """
    pass

def test_switch_hafiz(page, db_connection):
    """
    Test: User can switch between hafiz profiles

    Steps:
    1. Seed test hafiz via DB (fast setup)
    2. Login
    3. Click hafiz name button to switch
    4. Verify redirect to home page (URL)
    5. Verify UI shows current hafiz name
    6. Verify session has correct hafiz_id (check via DB query)
    7. Cleanup: Delete test hafiz

    Coverage: Hafiz switching, session management, routing
    """
    pass

def test_delete_hafiz(page, db_connection):
    """
    Test: User can delete a non-current hafiz profile

    Steps:
    1. Seed two test hafizs via DB
    2. Login and switch to hafiz1 (makes it current)
    3. Navigate to hafiz selection
    4. Click delete button for hafiz2
    5. Accept confirmation dialog
    6. Verify hafiz2 not visible in UI
    7. Verify hafiz2 not in database (CASCADE deleted)
    8. Cleanup: Delete hafiz1

    Coverage: Hafiz deletion, confirmation dialogs, CASCADE DELETE
    """
    pass
```

#### 2. Review Flow (1 test)

```python
# tests/e2e/test_review_flow.py

def test_review_item_with_rating_dropdown(page, db_connection):
    """
    Test: User can review an item via rating dropdown with HTMX auto-submit

    Steps:
    1. Seed test hafiz and item in DR mode, due today
    2. Login and switch to test hafiz
    3. Select "Good" rating (value=1) from dropdown
    4. Wait for HTMX auto-submit (1s)
    5. Verify UI shows green row background (visual feedback)
    6. Verify DB has revision record with rating=1
    7. Cleanup: Delete test hafiz

    Coverage: Rating dropdown, HTMX auto-submit, revision creation, UI feedback
    Note: Tests dropdown once - same component used across all modes
    """
    pass
```

#### 3. Close Date Engine (3 tests)

```python
# tests/e2e/test_close_date.py

def test_close_date_advances_date(page, db_connection):
    """
    Test: Close Date button advances hafiz current_date by 1 day

    Steps:
    1. Seed test hafiz with current_date='2025-11-07'
    2. Login and switch to test hafiz
    3. Click "Close Date" button
    4. Accept confirmation dialog
    5. Wait for processing (1s)
    6. Verify UI shows "Current Date: 2025-11-08"
    7. Verify DB hafiz.current_date = '2025-11-08'
    8. Cleanup: Delete test hafiz

    Coverage: Close Date button, date advancement, dialog handling
    """
    pass

def test_close_date_graduates_multiple_items(page, db_connection):
    """
    Test: Close Date processes multiple mode graduations in one operation

    This is the "engine test" - verifies core workflow across all modes.

    Steps:
    1. Seed test hafiz with current_date='2025-11-07'
    2. Seed 3 items ready to graduate:
       - Item 1: NM mode, reviewed today → should become DR
       - Item 2: DR mode, 7 reviews → should become WR
       - Item 3: WR mode, 7 reviews → should become FC
    3. Login and switch to test hafiz
    4. Click "Close Date" button
    5. Accept confirmation
    6. Wait for processing (2s)
    7. Verify DB item states:
       - Item 1: mode_code='DR', memorized=True
       - Item 2: mode_code='WR', next_review set
       - Item 3: mode_code='FC', next_review=NULL
    8. Cleanup: Delete test hafiz

    Coverage: All mode transitions, Close Date processing logic, stat updates
    """
    pass

def test_bad_rating_demotes_to_srs_on_close_date(page, db_connection):
    """
    Test: Item with bad rating moves to SRS mode when date is closed

    Steps:
    1. Seed test hafiz, item in FC mode with bad_streak=0
    2. Login and switch
    3. Review item with Bad rating (-1)
    4. Wait for auto-submit (1s)
    5. Click "Close Date" button
    6. Accept confirmation
    7. Wait for processing (2s)
    8. Verify DB:
       - Item mode_code='SR'
       - Item bad_streak=1
       - Item next_interval=7 (SRS start interval)
    9. Cleanup: Delete test hafiz

    Coverage: SRS demotion logic, bad_streak tracking, interval initialization
    """
    pass
```

**Total Phase 1: 7 tests, ~20-25s runtime**

---

### Phase 2: Mode-Specific Workflows (Optional - Add if Coverage < 70%)

These tests target specific mode behaviors that may not be fully covered by Phase 1.

#### 4. New Memorization (NM) Mode (2-3 tests)

```python
# tests/e2e/test_new_memorization.py

def test_browse_and_select_unmemorized_page(page, db_connection):
    """
    Test: User can browse unmemorized pages and mark one as newly memorized

    Steps:
    1. Seed test hafiz with some pages not memorized
    2. Login and navigate to /new_memorization
    3. Select "By Page" view
    4. Click checkbox for page 5
    5. Verify page appears in "Recently Memorized" table
    6. Verify DB: hafizs_items record for page 5, mode_code='NM'
    7. Cleanup

    Coverage: New memorization UI, checkbox interactions, NM mode creation
    """
    pass

def test_bulk_select_pages_with_shift_click(page, db_connection):
    """
    Test: User can bulk select pages with shift-click

    Steps:
    1. Seed test hafiz
    2. Navigate to New Memorization
    3. Click page 1 checkbox
    4. Shift+click page 5 checkbox
    5. Verify pages 1-5 all checked
    6. Submit selection
    7. Verify DB: 5 items created in NM mode
    8. Cleanup

    Coverage: Bulk selection, JavaScript shift-click handler
    """
    pass

def test_nm_to_dr_transition_on_first_review(page, db_connection):
    """
    Test: Item transitions from NM to DR after first review + Close Date

    Steps:
    1. Seed item in NM mode (memorized=False)
    2. Review item (default rating=1)
    3. Close Date
    4. Verify DB:
       - mode_code='DR'
       - memorized=True
       - next_review = current_date + 1 (daily interval)
    5. Cleanup

    Coverage: NM → DR transition logic
    Note: May be redundant with test_close_date_graduates_multiple_items
    """
    pass
```

#### 5. Daily/Weekly Reps (DR/WR) Modes (2 tests)

```python
# tests/e2e/test_fixed_reps.py

def test_dr_review_counting_and_wr_graduation(page, db_connection):
    """
    Test: Item in DR mode graduates to WR after 7 reviews

    Steps:
    1. Seed item in DR with 6 historical reviews
    2. Review item (7th time)
    3. Close Date
    4. Verify DB:
       - mode_code='WR'
       - next_review = current_date + 7 (weekly interval)
    5. Cleanup

    Coverage: DR review counting, threshold logic, WR graduation
    Note: Partially covered by test_close_date_graduates_multiple_items
    """
    pass

def test_wr_review_counting_and_fc_graduation(page, db_connection):
    """
    Test: Item in WR mode graduates to FC after 7 reviews

    Steps:
    1. Seed item in WR with 6 historical reviews (7 days apart)
    2. Review item (7th time)
    3. Close Date
    4. Verify DB:
       - mode_code='FC'
       - next_review=NULL (FC doesn't use fixed intervals)
    5. Cleanup

    Coverage: WR review counting, FC graduation
    Note: Partially covered by test_close_date_graduates_multiple_items
    """
    pass
```

#### 6. SRS Mode (SR) Advanced (3 tests)

```python
# tests/e2e/test_srs_advanced.py

def test_srs_good_rating_advances_interval(page, db_connection):
    """
    Test: Good rating in SRS mode advances to next interval in sequence

    Steps:
    1. Seed item in SR mode with next_interval=7
    2. Review with Good rating (1)
    3. Close Date
    4. Verify DB:
       - next_interval > 7 (should be 11, next in sequence)
       - next_review = current_date + 11
    5. Cleanup

    Coverage: SRS algorithm, good rating progression
    """
    pass

def test_srs_bad_rating_decreases_interval(page, db_connection):
    """
    Test: Bad rating in SRS mode regresses to earlier interval

    Steps:
    1. Seed item in SR mode with next_interval=11
    2. Review with Bad rating (-1)
    3. Close Date
    4. Verify DB:
       - next_interval < 11 (should be 7, previous in sequence)
       - next_review = current_date + 7
    5. Cleanup

    Coverage: SRS algorithm, bad rating penalty
    """
    pass

def test_srs_graduation_to_fc(page, db_connection):
    """
    Test: Item graduates from SRS to FC when interval exceeds 99

    Steps:
    1. Seed item in SR mode with next_interval=97
    2. Review with Good rating (1)
    3. Close Date
    4. Verify DB:
       - mode_code='FC' (graduated)
       - bad_streak=0 (reset)
       - next_interval=NULL
       - next_review=NULL (FC managed differently)
    5. Cleanup

    Coverage: SRS graduation threshold, FC re-entry
    """
    pass
```

#### 7. Full Cycle (FC) Mode Edge Cases (2 tests)

```python
# tests/e2e/test_full_cycle_advanced.py

def test_fc_pagination_adds_extra_rows_when_limit_reached(page, db_connection):
    """
    Test: FC table auto-expands when daily capacity limit is reached

    Steps:
    1. Seed hafiz with daily_capacity=5
    2. Seed 10 FC items all due today
    3. Login
    4. Review 5 items (reach limit)
    5. Verify FC table still shows more items (limit auto-increased)
    6. Verify session["full_cycle_progress"]["limit"] increased
    7. Cleanup

    Coverage: FC pagination logic, session tracking, ADD_EXTRA_ROWS
    """
    pass

def test_srs_items_appear_in_fc_table(page, db_connection):
    """
    Test: Items in SRS mode appear in FC table (not separate SR table)

    Steps:
    1. Seed item in SR mode, due today
    2. Login
    3. Verify item appears in FC table (mode_code shown as FC in UI)
    4. Verify SR specific columns (Last Interval, Next Interval) displayed
    5. Cleanup

    Coverage: FC/SR display overlap, UI mode presentation
    """
    pass
```

**Total Phase 2: 12 additional tests, ~30-40s runtime**

---

### Phase 3: Integration Tests (Only if E2E Coverage < 70%)

Add these ONLY if Phase 1 E2E tests don't achieve 70%+ coverage in critical backend logic.

#### SRS Algorithm Edge Cases

```python
# tests/integration/test_srs_intervals.py

def test_get_interval_triplet_for_each_sequence_position():
    """Test triplet calculation for all 26 interval positions"""
    pass

def test_interval_graduation_at_boundary():
    """Test graduation when next_interval = 101 (first > 99)"""
    pass

def test_interval_regression_at_start_of_sequence():
    """Test bad rating when already at interval=2 (leftmost)"""
    pass
```

#### Mode Transition Logic

```python
# tests/integration/test_mode_transitions.py

def test_update_rep_item_with_various_review_counts():
    """Test threshold detection for counts 0-7 in DR mode"""
    pass

def test_update_rep_item_wr_to_fc_transition():
    """Test WR graduation logic directly"""
    pass

def test_update_hafiz_item_for_srs_graduation():
    """Test SRS graduation when interval > 99"""
    pass
```

#### Close Date Processing

```python
# tests/integration/test_close_date_engine.py

def test_close_date_processes_mixed_mode_revisions():
    """Test Close Date with revisions across all 5 modes"""
    pass

def test_start_srs_for_bad_streak_items():
    """Test SRS demotion trigger for items with bad_streak >= 1"""
    pass

def test_populate_hafizs_items_stat_columns():
    """Test stat recalculation (streaks, counts, last_review)"""
    pass
```

**Total Phase 3: 8-10 integration tests, ~3-5s runtime**

---

### Phase 4: Additional Features (Low Priority)

#### Revision Management

```python
# tests/e2e/test_revision_crud.py

def test_edit_revision_rating(page, db_connection):
    """Test editing a revision's rating through revision page"""
    pass

def test_delete_revision(page, db_connection):
    """Test deleting a revision and verify stats update"""
    pass

def test_bulk_edit_revisions(page, db_connection):
    """Test bulk edit UI for multiple revisions"""
    pass
```

#### Profile & Page Details

```python
# tests/e2e/test_profile.py

def test_browse_memorization_status_by_juz(page, db_connection):
    """Test profile view filtered by Juz"""
    pass

def test_filter_memorized_pages(page, db_connection):
    """Test memorized/not_memorized filter toggle"""
    pass
```

```python
# tests/e2e/test_page_details.py

def test_page_details_shows_all_mode_tables(page, db_connection):
    """Test page details view with items in multiple modes"""
    pass
```

---

## Test Implementation Priority

**Week 1: Phase 1 Only**
- Goal: Get 6-7 E2E tests passing
- Run coverage analysis
- Decision point: Is 70%+ coverage achieved?

**Week 2: Conditional Expansion**
- If coverage >= 70%: **STOP** - E2E tests alone are sufficient
- If coverage 60-70%: Add selective Phase 2 tests for gaps
- If coverage < 60%: Add Phase 3 integration tests + Phase 2

**Week 3+: Optional Enhancement**
- Phase 4 tests only if:
  - Refactoring specific features (e.g., revision management)
  - Adding new features that need test coverage first (TDD)
  - Coverage report shows untested critical paths

---

## Test Metrics & Success Criteria

| Metric | Target | Notes |
|--------|--------|-------|
| **E2E Tests (Phase 1)** | 6-7 tests | Core user flows |
| **E2E Runtime** | < 30s | Fast enough for frequent runs |
| **Coverage** | > 70% overall | Minimum for refactoring confidence |
| **Critical Path Coverage** | > 85% | Close Date, mode transitions, SRS |
| **Flakiness** | 0% | All tests pass consistently (10 runs) |
| **Integration Tests** | 0-10 tests | Only if E2E gaps exist |
| **Total Runtime** | < 40s | E2E + integration combined |

---

## Notes on Test Design

**Why These Tests Are "Minimal"**:
- Rating dropdown tested once (same component across modes)
- Mode graduation tested once with multiple items (efficient "engine test")
- No exhaustive edge case testing in E2E (save for integration if needed)
- No duplicate testing across layers (each feature tested once)

**Coverage vs Test Count Tradeoff**:
- 7 E2E tests should cover ~70-80% of codebase
- Adding 12 more E2E tests (Phase 2) → ~85-90% coverage
- Adding 10 integration tests (Phase 3) → ~95% coverage
- Diminishing returns after 70% - focus on critical paths instead

**When to Stop Testing**:
1. All Phase 1 tests pass
2. Coverage > 70% overall
3. Critical paths (Close Date, mode logic) > 85% coverage
4. Tests run fast enough for TDD (<30s)
5. No flaky tests

**If these criteria are met, do NOT add more tests. You're done.**
