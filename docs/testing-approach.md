# Testing Approach for FastHTML Applications

**Last Updated**: December 2025

## Overview

This document outlines our testing strategy for the Quran SRS FastHTML application, following **official FastHTML recommendations** from Jeremy Howard's team.

**Philosophy**: "We write source code _first_, and then tests come _after_. The tests serve as both a means to confirm that the code works and also serves as working examples." - [FastHTML Docs](https://www.fastht.ml/docs/api/core.html#fasthtml-tests)

---

## Test Pyramid

```
       /\
      /  \     E2E Tests (Playwright)
     /    \    10% - Critical user journeys only
    /------\
   /        \  Cross-Module Integration (TestClient)
  /          \ 20% - Multi-module workflows
 /------------\
/              \ Colocated Tests (app/*_test.py)
\______________/ 70% - Unit + single-module integration
```

**Test Distribution**:
- **70%**: Colocated in `app/*_test.py` (unit tests + single-module integration)
- **20%**: Cross-module integration in `tests/integration/` (TestClient)
- **10%**: E2E user journeys in `tests/e2e/` (Playwright)

**Key Principle**: Keep tests simple. Use string assertions for most tests. Add structural queries only when needed.

---

## 🚨 CRITICAL: When to Use Playwright vs TestClient

**Playwright is EXPENSIVE (2-3s per test) - Use ONLY for complete user journeys:**

| Scenario | Tool | Example |
|----------|------|---------|
| ❌ Testing signup form submission | ~~Playwright~~ | ~~`test_user_can_signup.py`~~ |
| ✅ Testing signup form submission | **TestClient** | `tests/integration/test_authentication.py` |
| ❌ Testing login redirect | ~~Playwright~~ | ~~`test_user_can_login.py`~~ |
| ✅ Testing login redirect | **TestClient** | `tests/integration/test_authentication.py` |
| ❌ Testing create hafiz endpoint | ~~Playwright~~ | ~~`test_create_hafiz.py`~~ |
| ✅ Testing create hafiz endpoint | **TestClient** | `tests/integration/test_hafiz.py` |
| ✅ Testing complete user journey | **Playwright** | `tests/e2e/test_journey_first_cycle.py` |

**Rule of Thumb:**
- **Feature testing** (individual endpoints/actions) → Use **TestClient** (40-60x faster)
- **Journey testing** (multi-step user workflows) → Use **Playwright** (only for critical paths)

**Why?**
- TestClient gives you **code coverage** for features WITHOUT browser overhead
- Playwright tests should tell a **user story**, not test individual features
- One journey test (signup → login → create hafiz) is better than three Playwright feature tests

**Examples:**

```python
# ❌ BAD: Playwright for individual feature
def test_user_can_signup(page):
    page.goto("/users/signup")
    page.fill("[name='email']", "test@example.com")
    page.click("button[type='submit']")
    expect(page).to_have_url("/users/login")

# ✅ GOOD: TestClient for individual feature
def test_user_can_signup(client):
    response = client.post("/users/signup", data={"email": "test@example.com"})
    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/users/login"

# ✅ GOOD: Playwright for complete journey
def test_journey_new_user_first_cycle(page):
    # Phase 1: Signup
    page.goto("/users/signup")
    # ... signup flow

    # Phase 2: Login
    page.goto("/users/login")
    # ... login flow

    # Phase 3: Create hafiz
    # ... create hafiz flow

    # Phase 4-6: Mark pages, complete cycle, verify plan
    # ... (complete user story)
```

---

---

## FastHTML Testing Tools

### **Option 1: FastHTML's `Client` (Recommended)**

FastHTML provides its own test client:

```python
from fasthtml.core import Client

cli = Client(app)
response = cli.get('/')
assert "Welcome" in response.text
```

### **Option 2: Starlette's `TestClient` (Interchangeable)**

```python
from starlette.testclient import TestClient

client = TestClient(app)
response = client.get('/')
assert "Welcome" in response.text
```

**Official note**: "You can use either `Client` or `TestClient`. They should be largely interchangeable."

---

## Three Testing Tiers

### **Tier 1: Simple String Assertions (90% of tests)**

**Official FastHTML pattern** - just check `response.text`:

```python
def test_home_displays_tabs(client, auth_session):
    response = client.get("/", cookies=auth_session)

    # Simple!
    assert response.status_code == 200
    assert "Full Cycle" in response.text
    assert "Daily Reps" in response.text
    assert "SRS" in response.text
```

**When to use**:
- Verifying content exists
- Checking text is displayed
- Quick smoke tests
- Most of your tests!

---

### **Tier 2: Structural Queries (10% of tests)**

**When string matching isn't enough**, use parsel for structural verification:

```python
from parsel import Selector

def test_tab_count(client, auth_session):
    response = client.get("/", cookies=auth_session)

    # Parse HTML only when structure matters
    sel = Selector(text=response.text)
    tabs = sel.css('a[role="tab"]').getall()

    assert len(tabs) == 5  # Need exact count
```

**When to use**:
- Need to count elements
- Verify DOM structure
- Check attributes or nesting
- XPath/CSS queries needed

**Why parsel**:
- Built on lxml (Jeremy Howard's recommendation)
- Supports both CSS and XPath
- Fast and battle-tested (powers Scrapy)

---

### **Tier 3: End-to-End (5% of tests)**

**Playwright for complete user journeys ONLY**:

```python
def test_journey_new_user_first_cycle(page):
    # Complete user story: signup → login → create hafiz → first cycle
    page.goto("/users/signup")
    # Phase 1: Signup
    # Phase 2: Login
    # Phase 3: Create hafiz
    # Phase 4-6: Mark pages, complete cycle, verify plan
```

**When to use (JOURNEYS ONLY)**:
- ✅ Complete user workflows (signup → login → create → use)
- ✅ JavaScript interactions (Alpine.js tabs, dynamic UI)
- ✅ Critical smoke tests (app loads, major features work)

**When NOT to use (use TestClient instead)**:
- ❌ Testing individual features (signup, login, create)
- ❌ Testing API endpoints
- ❌ Testing redirects or status codes
- ❌ Getting code coverage

---

## Official FastHTML Patterns

### **1. Basic Route Testing**

```python
def test_route(client):
    response = client.get('/')
    assert response.text == 'expected content'
```

### **2. HTMX Request Testing**

```python
def test_htmx_fragment(client, auth_session):
    # Simulate HTMX request
    response = client.get("/",
                          headers={'hx-request': '1'},
                          cookies=auth_session)

    # Verify it's a fragment, not full page
    assert not response.text.startswith("<!doctype")
    assert "content" in response.text
```

### **3. Form Submission Testing**

```python
def test_form_submission(client):
    data = dict(name="Test User", email="test@example.com")
    response = client.post("/submit", data=data)

    assert response.status_code == 200
```

### **4. JSON Payload Testing**

```python
import json

def test_json_endpoint(client):
    payload = json.dumps({"key": "value"})
    response = client.post("/api/endpoint",
                           headers={"Content-Type": "application/json"},
                           data=payload)

    assert response.status_code == 200
```

### **5. Authentication Testing**

```python
def test_login_redirects(client):
    response = client.post("/users/login", data={
        "email": "test@example.com",
        "password": "password123"
    }, follow_redirects=False)

    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/users/hafiz_selection"
```

---

## Performance Comparison

| Test Type | Tool | Per-Test Time | 10 Tests |
|-----------|------|---------------|----------|
| **Unit** | Pure Python | ~10ms | **~0.1s** |
| **Integration** | Client | ~50ms | **~0.5s** |
| **E2E** | Playwright | ~2-3s | **~20-30s** |

**Expected Speedup**: Migrating from Playwright to Client = **40-60x faster**

---

## Test Organization

**Colocated Testing**: Tests live alongside the code they test, with cross-module and E2E tests in separate folders.

```
app/
├── hafiz_controller.py
├── hafiz_model.py
├── hafiz_service.py
├── hafiz_view.py
├── hafiz_test.py              # Unit + single-module integration (70%)
│
├── srs_interval_calc.py
├── srs_interval_calc_test.py  # Pure unit tests
├── srs_reps.py
├── srs_reps_test.py
│
├── users_controller.py
├── users_model.py
├── users_view.py
├── users_test.py
│
tests/
├── integration/                # Cross-module integration (20%)
│   ├── conftest.py            # Client, htmx_headers, auth_session
│   ├── test_authentication.py # Login/signup features (TestClient)
│   ├── test_close_date.py     # Touches multiple modules
│   └── test_srs_entry.py      # FC → SRS transition
│
└── e2e/                        # E2E user journeys (10%)
    ├── conftest.py            # Playwright fixtures
    ├── test_journey_1a_first_cycle.py  # New user → first full cycle
    └── test_journey_1b_srs_entry.py    # Full cycle → SRS transition
```

**Key Points**:
- **`app/*_test.py`**: Colocated tests - unit tests and single-module integration tests
- **`tests/integration/`**: Cross-module integration tests using TestClient
- **`tests/e2e/`**: Full user journeys using Playwright
- **Naming convention**: `*_test.py` suffix (not `test_*` prefix) for alphabetical grouping
  - ✅ `hafiz_controller.py`, `hafiz_model.py`, `hafiz_test.py` - sorted together!
  - ❌ `test_hafiz.py` - sorted away from module files

### **pytest Configuration**

Add to `pyproject.toml` to enable test discovery in both `app/` and `tests/`:

```toml
[tool.pytest.ini_options]
testpaths = ["app", "tests"]
python_files = ["*_test.py", "test_*.py"]
```

This allows:
- `app/*_test.py` pattern (colocated tests)
- `tests/*/test_*.py` pattern (integration/e2e tests)

---

## Setup: Test Fixtures

### **Integration Tests**

```python
# tests/integration/conftest.py
import pytest
from fasthtml.core import Client

@pytest.fixture
def client():
    """FastHTML test client."""
    from main import app
    return Client(app)

@pytest.fixture
def htmx_headers():
    """Standard HTMX request headers."""
    return {'hx-request': '1'}

@pytest.fixture
def auth_session(client):
    """Login and return session cookies."""
    response = client.post("/users/login", data={
        "email": "test@example.com",
        "password": "password123"
    })
    return response.cookies
```

### **Optional: parsel Helper**

```python
# Only add if you use parsel in multiple tests
from parsel import Selector

@pytest.fixture
def parse_html():
    """Parse response HTML with parsel (use sparingly)."""
    def _parse(response):
        return Selector(text=response.text)
    return _parse
```

---

## Colocated Test Examples

### **Unit Test (Pure Python)**

```python
# app/srs_interval_calc_test.py
from app.srs_interval_calc import calculate_good_interval, get_phase_config

def test_phase1_good_interval():
    """Phase 1 (0-14 days): base + (streak × 2)"""
    result = calculate_good_interval(base=7, good_streak=2)
    assert result == 11  # 7 + (2 × 2)

def test_phase_config_lookup():
    """Verify phase configuration."""
    config = get_phase_config(interval=10)
    assert config["good_multiplier"] == 2.0
    assert config["ok_increment"] == 2
```

### **Single-Module Integration Test**

```python
# app/hafiz_test.py
import pytest
from fasthtml.core import Client

@pytest.fixture
def client():
    from main import app
    return Client(app)

def test_hafiz_creation(client, auth_session):
    """Test creating a new hafiz."""
    response = client.post("/hafiz/create", data={
        "name": "Test Hafiz",
    }, cookies=auth_session)

    assert response.status_code == 200
    assert "Test Hafiz" in response.text

def test_hafiz_deletion(client, auth_session):
    """Test deleting a hafiz."""
    # Create hafiz first
    client.post("/hafiz/create", data={
        "name": "To Delete",
    }, cookies=auth_session)

    # Then delete
    response = client.delete("/hafiz/1", cookies=auth_session)

    assert response.status_code == 200
```

### **Cross-Module Integration Test**

```python
# tests/integration/test_close_date.py
"""
Cross-module integration test - Close Date touches:
- revisions (reading today's reviews)
- hafizs_items (updating intervals)
- srs_reps (triggering SRS entry)
- fixed_reps (mode transitions)
"""
import pytest
from fasthtml.core import Client

@pytest.fixture
def client():
    from main import app
    return Client(app)

def test_close_date_triggers_srs_entry(client, auth_session):
    """When FC item gets Ok/Bad rating, close date should move it to SRS."""
    # 1. Create revision with Bad rating in Full Cycle
    client.post("/revisions/create", data={
        "item_id": 1,
        "mode_code": "FC",
        "rating": -1  # Bad
    }, cookies=auth_session)

    # 2. Close the date
    response = client.post("/close_date", cookies=auth_session)
    assert response.status_code == 200

    # 3. Verify item moved to SRS
    item_response = client.get("/hafiz_items/1", cookies=auth_session)
    assert "SR" in item_response.text  # Now in SRS mode
    assert "3" in item_response.text   # 3-day starting interval
```

---

## FastHTML/HTMX Testing Patterns

*Patterns from [Testing FastHTML Dashboards](https://krokotsch.eu/posts/testing-fasthtml/)*

### 1. HTMX Request Headers ⚠️ CRITICAL

**Problem**: FastHTML/HTMX returns different responses based on the `HX-Request` header:
- With header: Returns HTML fragment (what HTMX expects)
- Without header: Returns full page with wrapper/layout

**Solution**: Always set the header when testing HTMX endpoints:

```python
def test_htmx_fragment(client, hafiz_session):
    """Test HTMX fragment response (not full page)."""
    response = client.get(
        "/hafiz/settings",
        cookies=hafiz_session,
        headers={"HX-Request": "true"}  # ← Critical for HTMX testing
    )

    assert response.status_code == 200
    # Response is now just the fragment, not full page
```

**Alternative: Use fixture** (from line 287-289):
```python
def test_htmx_fragment(client, hafiz_session, htmx_headers):
    """Use htmx_headers fixture for cleaner code."""
    response = client.get(
        "/hafiz/settings",
        cookies=hafiz_session,
        headers=htmx_headers  # {'hx-request': '1'}
    )
```

**When to use**:
- ✅ Testing routes that return HTMX fragments (forms, tables, partials)
- ✅ Testing auto-submit dropdowns, inline edits
- ❌ Testing full page loads (login, initial page render)

---

### 2. XPath for HTML Assertions

**Problem**: String matching (`"text" in response.text`) is fragile and imprecise:
- Matches text in comments, scripts, hidden elements
- Can't verify HTML structure or attributes
- Hard to debug when tests fail

**Solution**: Use `lxml` with XPath for precise HTML assertions:

**Before (fragile)**:
```python
assert "Hafiz Preferences" in response.text
assert "Name" in response.text
assert "Daily Capacity" in response.text
```

**After (precise)**:
```python
import lxml.html

html = lxml.html.fromstring(response.text)

# Verify heading exists
assert html.xpath("//h1[text()='Hafiz Preferences']")

# Verify form fields
assert html.xpath("//label[text()='Name']")
assert html.xpath("//input[@name='name']")

# Verify attributes
assert html.xpath("//input[@name='name' and @type='text']")

# Verify disabled state
assert html.xpath("//input[@name='current_date' and @disabled]")
```

**Common XPath patterns**:
```python
# Element with specific text
html.xpath("//h1[text()='Title']")

# Element with attribute
html.xpath("//input[@name='email']")

# Element with multiple attributes
html.xpath("//input[@type='email' and @required]")

# Element containing text (partial match)
html.xpath("//p[contains(text(), 'Success')]")

# Get attribute value
html.xpath("//input[@name='capacity']/@value")[0]  # → "5"

# Count elements
len(html.xpath("//tr[@class='revision-row']"))  # → 3
```

**Installation**:
```bash
uv add lxml
```

**Benefits**:
- ✅ More precise (won't match text in wrong places)
- ✅ Can verify structure, not just content
- ✅ Can check attributes, classes, states
- ✅ Better error messages (shows actual HTML when fails)

---

### 3. Playwright Semantic Selectors

**Problem**: CSS selectors (`input[id='email']`) are brittle:
- Break when implementation changes (ID/class refactoring)
- Don't reflect user intent (users don't see IDs)
- Poor accessibility alignment

**Solution**: Use Playwright's semantic selectors:

**Before (brittle)**:
```python
page.click("a:has-text('Settings')")
page.fill("input[id='name']", "Test Hafiz")
page.click("button:has-text('Update')")
```

**After (robust)**:
```python
# By role and name (most semantic)
page.get_by_role("link", name="Settings").click()

# By label (best for form fields)
page.get_by_label("Daily Capacity").fill("5")

# By role for buttons
page.get_by_role("button", name="Update").click()

# By text (for non-interactive elements)
page.get_by_text("Hafiz Preferences")
```

**Common semantic selectors**:
```python
# Links
page.get_by_role("link", name="Home")
page.get_by_role("link", name="Settings")

# Buttons
page.get_by_role("button", name="Submit")
page.get_by_role("button", name="Delete")

# Form fields
page.get_by_label("Email")
page.get_by_label("Password")
page.get_by_placeholder("Enter your name")

# Headings
page.get_by_role("heading", name="Dashboard")

# Text content
page.get_by_text("Welcome back")
page.get_by_text("Success", exact=True)  # Exact match

# Test IDs (fallback for dynamic content)
page.get_by_test_id("switch-hafiz-1")
```

**Migration strategy**:
1. Start with new tests (use semantic selectors from day 1)
2. Refactor existing tests when they break (opportunistic)
3. Don't rewrite working tests just for style (YAGNI)

**Benefits**:
- ✅ More resilient to DOM changes
- ✅ Better accessibility (reflects user perspective)
- ✅ More readable ("get by label Email" vs "input[id='email']")
- ✅ Playwright auto-waits for elements

---

### 4. Module-Scoped Database Fixtures (Performance)

**Problem**: Creating/destroying database for every test is slow:
- SQLite file creation overhead
- Schema migration overhead
- Adds ~50-100ms per test

**Solution**: Create DB once per module, clean data between tests:

**Before (slow - 100ms per test)**:
```python
@pytest.fixture
def test_db():
    """Create fresh DB for every test."""
    db = create_database()  # 50ms
    run_migrations(db)      # 30ms
    yield db
    delete_database(db)     # 20ms
    # Total: 100ms overhead per test
```

**After (fast - 10ms per test)**:
```python
@pytest.fixture(scope="module")
def test_db_module():
    """Create DB once per test module."""
    db = create_database()  # 50ms once
    run_migrations(db)      # 30ms once
    yield db
    delete_database(db)     # 20ms once

@pytest.fixture
def clean_db(test_db_module):
    """Clean data between tests (fast)."""
    yield test_db_module
    # Just truncate tables (~5ms)
    truncate_all_tables(test_db_module)
```

**When to use**:
- ✅ When you have many tests in one module (10+ tests)
- ✅ When database setup is expensive (migrations, seed data)
- ✅ When tests are independent (no shared state dependencies)
- ❌ When tests modify schema (use function-scoped)
- ❌ For E2E tests with real server (use dev database with cleanup)

**Trade-off**: Faster tests vs. risk of test pollution if cleanup fails.

---

## Migration Examples

### **Authentication Test**

**Before (Playwright - ~3s)**:
```python
def test_user_can_login(page):
    page.goto("http://localhost:5001/users/login")
    page.get_by_label("Email").fill("test@example.com")
    page.get_by_label("Password").fill("password123")
    page.get_by_role("button", name="Login").click()

    expect(page).to_have_url("http://localhost:5001/users/hafiz_selection")
```

**After (Client - ~50ms)**:
```python
def test_user_can_login(client):
    response = client.post("/users/login", data={
        "email": "test@example.com",
        "password": "password123"
    }, follow_redirects=False)

    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/users/hafiz_selection"
```

**Result**: **60x faster!**

---

### **Content Verification Test**

**Before (Playwright)**:
```python
def test_home_displays_tabs(page, authenticated):
    page.goto("/")
    expect(page.locator("a:has-text('Full Cycle')")).to_be_visible()
    expect(page.locator("a:has-text('SRS')")).to_be_visible()
```

**After (Client - Simple)**:
```python
def test_home_displays_tabs(client, auth_session):
    response = client.get("/", cookies=auth_session)

    assert "Full Cycle" in response.text
    assert "SRS" in response.text
```

**After (Client + parsel - When structure matters)**:
```python
from parsel import Selector

def test_home_tab_structure(client, auth_session):
    response = client.get("/", cookies=auth_session)
    sel = Selector(text=response.text)

    # Verify exact count
    tabs = sel.css('a[role="tab"]').getall()
    assert len(tabs) == 5

    # Verify active tab
    active_tab = sel.css('a.tab-active::text').get()
    assert active_tab in ['Full Cycle', 'Daily Reps', 'Weekly Reps', 'SRS']
```

---

## Decision Tree

```
What are you testing?
├─ Pure function/calculation?
│  └─ Colocated Unit Test: app/module_test.py
│
├─ Single module (controller → service → model)?
│  └─ Colocated Integration Test: app/module_test.py (TestClient)
│
├─ Multiple modules working together?
│  └─ Cross-Module Integration: tests/integration/ (TestClient)
│
├─ Content exists on page?
│  └─ Integration Test: assert "text" in response.text
│
├─ HTML structure/count/attributes?
│  └─ Integration Test: Client + parsel
│
├─ HTMX fragment response?
│  └─ Integration Test: Client with hx-request header
│
├─ JavaScript (Alpine.js)?
│  └─ E2E Test: tests/e2e/ (Playwright)
│
└─ Multi-step user journey?
   └─ E2E Test: tests/e2e/ (Playwright)
```

---

## Running Tests

### **All Tests**
```bash
uv run pytest -v
```

### **By Type (Speed Order)**
```bash
# Fastest - Colocated unit/integration tests
uv run pytest app/ -v                 # ~0.1-0.5s

# Fast - Cross-module integration
uv run pytest tests/integration -v    # ~0.5-1s

# Slowest - E2E user journeys
uv run pytest tests/e2e -v            # ~10-20s
```

### **By Module**
```bash
# Test specific module
uv run pytest app/hafiz_test.py -v
uv run pytest app/srs_interval_calc_test.py -v
```

### **With Coverage**
```bash
uv run pytest --cov --cov-report=html
```

### **Watch Mode (TDD)**
```bash
uv run pytest-watch app/           # Watch colocated tests
uv run pytest-watch tests/         # Watch integration/e2e tests
```

---

## Common Patterns

### **Testing Multiple Items**

```python
def test_all_modes_display(client, auth_session):
    response = client.get("/", cookies=auth_session)

    for mode in ["Full Cycle", "Daily Reps", "Weekly Reps", "SRS"]:
        assert mode in response.text, f"Mode '{mode}' not found"
```

### **Testing HTMX Fragments**

```python
def test_htmx_returns_fragment_not_full_page(client, auth_session, htmx_headers):
    response = client.get("/",
                          headers=htmx_headers,
                          cookies=auth_session)

    # Fragment should not have doctype
    assert not response.text.strip().startswith("<!doctype")

    # But should have content
    assert len(response.text) > 0
```

### **Testing Redirects**

```python
def test_redirect_after_action(client, auth_session):
    response = client.post("/action",
                           data={"key": "value"},
                           cookies=auth_session,
                           follow_redirects=False)

    assert response.status_code in (302, 303, 307, 308)
    assert response.headers["location"] == "/expected/path"
```

### **Testing Status Codes**

```python
def test_unauthorized_access(client):
    response = client.get("/protected")
    assert response.status_code == 401
```

---

## Using parsel (When Needed)

### **CSS Selectors (Familiar)**

```python
from parsel import Selector

sel = Selector(text=response.text)

# Simple selection
tabs = sel.css('a[role="tab"]').getall()

# Get text content
tab_names = sel.css('a[role="tab"]::text').getall()

# Get attributes
hrefs = sel.css('a[role="tab"]::attr(href)').getall()

# Find one element
active_tab = sel.css('a.tab-active::text').get()
```

### **XPath (Powerful)**

```python
# Text matching
fc_tab = sel.xpath('//a[contains(text(), "Full Cycle")]').get()

# Complex conditions
active_tabs = sel.xpath('//a[@role="tab" and contains(@class, "active")]').getall()

# Parent/child navigation
tab_container = sel.xpath('//div[@class="tabs"]//a').getall()
```

### **Mix Both**

```python
# CSS for structure, XPath for text
tabs = sel.css('div.tabs').xpath('.//a[contains(text(), "SRS")]').get()
```

---

## Best Practices

### **1. Start Simple**

```python
# ✅ Good - Start with string assertions
def test_content_exists(client):
    response = client.get("/")
    assert "Expected content" in response.text

# ❌ Don't start with complex parsing
def test_content_exists(client):
    from parsel import Selector
    sel = Selector(text=response.text)
    # ... only if structure actually matters
```

### **2. Import parsel Locally**

```python
# ✅ Good - Import in function (signals "special case")
def test_structure(client):
    response = client.get("/")

    from parsel import Selector
    sel = Selector(text=response.text)
    # ...

# ❌ Avoid - Importing at module level suggests overuse
from parsel import Selector  # At top of file
```

### **3. Test What Matters**

```python
# ✅ Good - Test user-facing content
assert "Full Cycle" in response.text

# ❌ Don't test implementation details
assert '<div class="tabs">' in response.text
```

### **4. Use Helpers for Common Patterns**

```python
# tests/integration/helpers.py
def assert_redirects_to(response, path):
    """Helper for redirect assertions."""
    assert response.status_code in (302, 303)
    assert response.headers["location"] == path

# In tests
assert_redirects_to(response, "/users/hafiz_selection")
```

---

## Expected Migration Results

| Metric | Before (All Playwright) | After (Hybrid) | Improvement |
|--------|-------------------------|----------------|-------------|
| **Test suite time** | ~30-40s | ~5-8s | **5-6x faster** |
| **Per-test speed** | ~2-3s | ~50ms (integration) | **40-60x faster** |
| **Coverage** | Same | Same or better | - |
| **Flakiness** | High (timing issues) | Low (deterministic) | Much more stable |
| **Maintenance** | Medium (selectors break) | Low (stable text) | Easier to maintain |

---

## Summary

### **The Official FastHTML Way + Colocated Testing**

1. **Colocate tests** with code in `app/*_test.py` (70% of tests)
2. **Use `Client`** for integration tests (fast, no browser needed)
3. **Simple `.text` assertions** for 90% of tests
4. **Add parsel** only when structure verification is needed
5. **Cross-module tests** in `tests/integration/` (20% of tests)
6. **Keep Playwright** for critical E2E journeys in `tests/e2e/` (10% of tests)

### **Installation**

```bash
# Always needed
uv add pytest

# For integration tests (optional - already included with FastHTML)
# Client comes with fasthtml.core

# Only if you need structural queries
uv add parsel

# Only for E2E tests
uv add pytest-playwright
```

### **Philosophy**

Keep it simple. Tests are documentation. String assertions are fast, readable, and sufficient for most cases. Add complexity only when actually needed.

---

## Advanced Playwright Patterns

*Inspired by [Playwright & pytest that brings me joy](https://www.better-simple.com/django/2025/09/17/playwright-pytest-that-brings-me-joy/)*

### Pytest Markers for Test Context

**Problem:** Passing authentication fixtures explicitly clutters test signatures and hides test intent.

**Solution:** Use pytest markers to declare test requirements, let fixtures auto-configure.

**Before:**
```python
def test_settings_page(client, hafiz_session):
    # Must pass hafiz_session fixture
    response = client.get("/hafiz/settings", cookies=hafiz_session)
    assert response.status_code == 200
```

**After:**
```python
@pytest.mark.requires_hafiz(hafiz_id=1)
def test_settings_page(page):
    # Marker declares intent, fixture handles setup
    page.goto("/hafiz/settings")
    expect(page.locator("h1")).to_have_text("Hafiz Preferences")
```

**Benefits:**
- ✅ Test intent is **explicit** (marker shows requirements at a glance)
- ✅ Test signatures are **cleaner** (no fixture parameter clutter)
- ✅ Easy to **scan** test files and see which tests need authentication
- ✅ **Centralized** auth logic (fixture reads marker, configures once)

**Implementation:**

```python
# tests/e2e/conftest.py
import pytest
import os

@pytest.fixture
def page(page, request):
    """Auto-configure page based on test markers."""

    # Check for authentication markers
    hafiz_marker = request.node.get_closest_marker("requires_hafiz")

    if hafiz_marker:
        hafiz_id = hafiz_marker.kwargs.get("hafiz_id", 1)

        # Login as user
        page.goto("/users/login")
        page.fill("input[name='email']", os.getenv("TEST_EMAIL"))
        page.fill("input[name='password']", os.getenv("TEST_PASSWORD"))
        page.click("button[type='submit']")

        # Select hafiz
        page.click(f"button[data-testid='switch-hafiz-{hafiz_id}']")

    yield page
```

**Register the marker** in `pyproject.toml` to avoid warnings:

```toml
[tool.pytest.ini_options]
markers = [
    "requires_hafiz: mark test to auto-login and select a specific hafiz",
]
```

**Usage:**

```python
# No authentication needed
def test_smoke(page):
    page.goto("/")
    expect(page).to_have_title("Quran SRS")

# Requires hafiz 1
@pytest.mark.requires_hafiz(hafiz_id=1)
def test_hafiz_settings(page):
    page.goto("/hafiz/settings")
    expect(page.locator("h1")).to_have_text("Hafiz Preferences")

# Requires different hafiz
@pytest.mark.requires_hafiz(hafiz_id=2)
def test_hafiz_2_settings(page):
    page.goto("/hafiz/settings")
    # Tests run with hafiz 2 context
```

### HTMX Request Validation

**Problem:** Testing only UI changes misses HTMX request failures that don't show visually.

**Solution:** Use `page.expect_response()` to validate background requests.

**Why it matters:**
- Our app heavily uses HTMX for auto-submit rating dropdowns
- HTMX swaps HTML fragments without page reloads
- Backend errors might not show in UI but break functionality

**Pattern:**

```python
def test_rating_dropdown_triggers_htmx(page):
    page.goto("/")

    # Validate HTMX request completes successfully
    with page.expect_response("**/revision/rate/*") as response_info:
        page.select_option("select.rating-dropdown", "1")

    response = response_info.value
    assert response.status == 200
    assert response.ok
```

**Advanced: Check HTMX response headers:**

```python
def test_htmx_swap_response(page):
    with page.expect_response("**/endpoint") as response_info:
        page.click("button[hx-post]")

    response = response_info.value

    # Verify HTMX-specific headers
    assert "hx-trigger" in response.headers or "hx-reswap" in response.headers

    # Check response content
    body = response.text()
    assert "<tr" in body  # Expects table row HTML
```

**Where to apply:**
- Rating dropdown auto-submit (tests/e2e/rating_test.py)
- Bulk action bar HTMX swaps
- Close Date processing with redirects
- Any `hx-post`, `hx-get`, `hx-swap` interactions

### Accessibility Testing (Optional)

**Problem:** Accessibility issues only caught in manual review or production.

**Solution:** Automated accessibility checks with axe-playwright.

**Installation:**

```bash
uv add axe-playwright-python
```

**Implementation:**

```python
# tests/e2e/conftest.py
import pytest
from axe_playwright_python.sync_playwright import Axe

@pytest.fixture
def axe_check(page):
    """Run accessibility checks on current page."""
    def _check():
        axe = Axe()
        results = axe.run(page)

        violations = results.get("violations", [])
        if violations:
            print(f"\n{len(violations)} accessibility violations:")
            for v in violations:
                print(f"  [{v['impact']}] {v['id']}: {v['description']}")

        return violations

    return _check
```

**Usage:**

```python
def test_login_page_accessibility(page, axe_check):
    page.goto("/users/login")

    violations = axe_check()
    assert len(violations) == 0, "Accessibility violations found"

def test_dashboard_accessibility(page, axe_check):
    page.goto("/")

    violations = axe_check()

    # Allow known violations (document in issue tracker)
    critical = [v for v in violations if v['impact'] == 'critical']
    assert len(critical) == 0, "Critical accessibility issues found"
```

**When to use:**
- Login/signup flows (must be accessible)
- Main dashboard (complex tables)
- Forms (hafiz settings, revision entry)
- Any public-facing pages

### Interactive Debugging

**Pattern:** Use `page.pause()` for live debugging.

```python
def test_complex_interaction(page):
    page.goto("/")

    # Pause execution, open browser inspector
    page.pause()

    # Continue with test
    page.click("button")
```

**Run with headed mode:**

```bash
# Shows browser window
uv run pytest tests/e2e/test_file.py --headed

# Alternative: PWDEBUG=1 (Playwright inspector)
PWDEBUG=1 uv run pytest tests/e2e/test_file.py
```

**Benefits:**
- ✅ Craft correct selectors by inspecting live elements
- ✅ Verify page state at any point in test
- ✅ Debug flaky tests interactively

---

## References

- [FastHTML Testing Guide](https://www.fastht.ml/docs/ref/concise_guide.html#testing) - Official docs
- [FastHTML API: Tests](https://www.fastht.ml/docs/api/core.html#fasthtml-tests) - Test utilities
- [parsel Documentation](https://parsel.readthedocs.io/) - When you need structural queries
- [Scrapy Selectors](https://docs.scrapy.org/en/latest/topics/selectors.html) - parsel usage examples
- [Playwright & pytest that brings me joy](https://www.better-simple.com/django/2025/09/17/playwright-pytest-that-brings-me-joy/) - Advanced patterns
