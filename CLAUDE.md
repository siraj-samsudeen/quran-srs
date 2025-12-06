# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Quran SRS is a sophisticated Spaced Repetition System designed to help with Quran memorization and revision. It uses FastHTML as the web framework with SQLite database, focusing on tracking memorization progress across different modes (New Memorization, Daily, Weekly, Full Cycle, SRS). The application supports multi-user scenarios where a single account can manage multiple hafiz profiles (family/teaching contexts).

## Recent Changes & Cleanup (Nov 2025)

**Codebase Cleanup** (Commits: 08f2db7, 5a133f3, 2fc9263):
- Removed ~809 lines of dead code across 17 files
- Deleted 27 unused database columns (migration 0020)
- Removed orphaned routes: `/admin/backups`, `/admin/change_current_date`, `/admin/import_db`
- Cleaned up duplicate utility functions in `utils.py`
- Removed unused SRS recalculation logic from Close Date processing

**Testing**:
- **Strategy**: Test pyramid approach (Unit → Integration → E2E)
- **See**: `docs/testing-approach.md` for comprehensive testing guide
- **Test Types**:
  - Unit tests (`tests/backend/`) - Pure Python, business logic
  - Integration tests (`tests/integration/`) - TestClient for routes/HTMX
  - E2E tests (`tests/ui/`) - Playwright for critical journeys only

## Development Commands

### Python Environment
- **Run the application**: `uv run main.py` (uses uv, NOT `python main.py`)
- **Run in test mode**: `ENV=test uv run main.py` (uses test database)
- **Install dependencies**: `uv sync`
- **Add new dependency**: `uv add <package-name>`
- **Run all tests**: `uv run pytest -v`
- **Run unit tests**: `uv run pytest tests/backend -v` (fastest)
- **Run integration tests**: `uv run pytest tests/integration -v` (TestClient)
- **Run E2E tests**: `uv run pytest tests/ui -v` (Playwright)
- **Run with coverage**: `uv run pytest --cov --cov-report=html`
- **Base URL**: `http://localhost:5001` (configurable via BASE_URL env var)

### Environment Configuration

The application uses an `ENV` environment variable to determine which database to use:

| ENV Value | Database Path | Use Case |
|-----------|---------------|----------|
| `test` | `data/quran_test.db` | E2E tests (isolated from dev data) |
| `dev` (default) | `data/quran_v10.db` | Local development |
| `prod` | `data/quran_v10.db` | Production (future: separate path) |

**Setup test database (one-time)**:
```bash
cp data_backup/quran_v10.db data/quran_test.db
```

### Testing Strategy

**See `docs/testing-approach.md` for complete testing guide.**

Our testing follows a **test pyramid approach** optimized for FastHTML:

**1. Unit Tests** (`tests/backend/`) - **Most tests, fastest**
- Pure Python functions, business logic, algorithms
- No HTTP, no database dependencies
- Speed: ⚡⚡⚡ Instant (< 10ms per test)

**2. Integration Tests** (`tests/integration/`) - **Middle layer**
- FastHTML routes, HTMX fragments, form submissions
- Uses Starlette's `TestClient` (no browser needed)
- Speed: ⚡⚡ Fast (~50ms per test)
- **Key Pattern**: Set `HX-Request: 1` header for HTMX tests

**3. E2E Tests** (`tests/ui/`) - **Fewest tests, slowest**
- Critical user journeys, JavaScript interactions (Alpine.js)
- Uses Playwright (browser-based)
- Speed: 🐌 Slow (~2-3s per test)
- **Use only when**: Testing requires JavaScript or visual validation

**Running tests**:
```bash
# All tests
uv run pytest -v

# By speed (fastest first)
uv run pytest tests/backend -v       # Unit tests
uv run pytest tests/integration -v   # Integration tests
uv run pytest tests/ui -v            # E2E tests
```

#### Test Examples by Type

**Unit Test** (tests/backend/):
```python
def test_calculate_good_interval_phase1():
    """Pure function test - no DB, no HTTP."""
    from app.srs_interval_calc import calculate_good_interval

    result = calculate_good_interval(base=7, good_streak=2)
    assert result == 11  # 7 + (2 × 2)
```

**Integration Test** (tests/integration/):
```python
def test_login_redirects_to_hafiz_selection(client):
    """Test HTTP endpoint with TestClient."""
    response = client.post("/users/login", data={
        "email": "test@example.com",
        "password": "password123"
    }, follow_redirects=False)

    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/users/hafiz_selection"
```

**E2E Test** (tests/ui/):
```python
def test_alpine_tab_switching(page):
    """Test JavaScript interaction - requires browser."""
    page.goto("/")

    # Click SRS tab (Alpine.js x-show)
    page.locator("a:has-text('SRS')").click()

    # Verify tab becomes active (CSS class change)
    expect(page.locator("a:has-text('SRS')")).to_have_class(re.compile(r"tab-active"))
```

#### TDD Workflow (Red-Green-Refactor)

**IMPORTANT**: All tests must be written following strict TDD discipline:

**🔴 RED: Write Failing Test First**
1. Write the test that describes the desired behavior
2. Run test - it MUST fail (proves test is actually testing something)
3. Commit with message: `RED: [test description]`
4. Example: `RED: test user can create hafiz via UI`

**✅ GREEN: Write Minimal Implementation**
1. Write the simplest code to make the test pass
2. Run test - it MUST pass
3. Commit with message: `GREEN: [test description]`
4. Example: `GREEN: test user can create hafiz via UI`
5. **No refactoring yet** - just make it work

**🔄 REFACTOR: Clean Up Code**
1. Improve code quality without changing behavior
2. Run test - it MUST still pass
3. Commit with message: `REFACTOR: [description of improvement]`
4. Example: `REFACTOR: extract hafiz creation helpers`
5. This is where test helpers are created (if needed)

**Test Helper Policy**:
- ❌ **DO NOT** write test helpers upfront
- ✅ **DO** write helpers during RED phase if test requires it
- ✅ **DO** extract helpers during REFACTOR phase when duplication emerges
- **Rule of Three**: Extract helper after copying code 3 times

**Commit Discipline**:
- Each RED-GREEN-REFACTOR cycle = 2-3 separate commits
- Never combine RED and GREEN in one commit
- REFACTOR is optional (only when needed)

**Branching Workflow**:
1. **Always push master first**: `git push origin master` before starting new work
2. **Create feature branch**: `git checkout -b feature-name` for each new test/feature
3. **Work in branch**: Do RED-GREEN-REFACTOR commits in the feature branch
4. **Review before merge**: User reviews all commits in branch
5. **Merge to master**: `git checkout master && git merge feature-name`
6. **Push master**: `git push origin master`
7. **Delete feature branch**: `git branch -d feature-name`

**Example workflow**:
```bash
# Starting work on a new test
git push origin master                        # Ensure master is synced
git checkout -b test-create-hafiz            # Create feature branch
# ... do RED commit ...
# ... do GREEN commit ...
# ... do REFACTOR commit (if needed) ...
# User reviews commits
git checkout master                           # Switch back to master
git merge test-create-hafiz                   # Merge feature branch
git push origin master                        # Push to remote
git branch -d test-create-hafiz              # Clean up feature branch
```

#### Test Structure & Best Practices

**Test Organization:**
- Use focused tests (one behavior per test, not journey tests)
- Create reusable helper functions for common actions (`login()`, `create_hafiz()`, `switch_hafiz()`)
- Each test should be independent and self-contained

**Selector Strategy:**
- **Primary**: Use `data-testid` attributes for reliable element targeting (e.g., `data-testid="switch-{name}-hafiz-button"`)
- **Fallback**: Use semantic selectors (e.g., `page.locator("h3:has-text('Name')")`) for content verification
- **Why**: `data-testid` is stable across UI changes; text/class selectors are fragile

**Handling Dynamic Content:**
- Use timestamp-based unique identifiers for test data (e.g., `f"E2E Test {int(time.time() * 1000)}"`)
- Prevents test collisions when running concurrently or with leftover data
- Use Playwright's auto-waiting (polls automatically until element appears)

**Common Playwright Patterns:**

1. **Browser Confirmation Dialogs** (`hx-confirm` in HTMX):
   ```python
   # Handle browser confirmation dialog
   page.on("dialog", lambda dialog: dialog.accept())
   page.click("button[data-testid='delete-button']")
   ```

2. **Waiting for HTMX Updates**:
   ```python
   # Playwright auto-waits for elements
   expect(page.locator("text=Success")).to_be_visible()

   # Or explicit wait for HTMX processing
   page.wait_for_timeout(1000)  # 1 second
   ```

3. **Newly Created Resources**:
   - Don't assume Full Cycle mode appears for new hafizs (requires memorized pages)
   - Check for always-visible elements instead (e.g., "System Date:", "Close Date" button)
   - Understand business logic: new hafizs have `hafizs_items` but with `memorized=false`

4. **Testing Alpine.js x_show visibility**:
   - Don't compare content between tabs - content might be the same
   - Don't use CSS `:visible` selector - doesn't work reliably with Alpine's x_show
   - Test class changes instead (more reliable):
   ```python
   import re
   srs_tab = page.locator("a:has-text('SRS')")
   srs_tab.click()
   # Verify tab-active class was applied
   expect(srs_tab).to_have_class(re.compile(r"tab-active"))
   ```

**Test Data Cleanup:**
- Tests should be self-contained: create → use → delete
- Rely on database CASCADE DELETE for related records
- Unique naming prevents interference between test runs

#### Advanced Playwright Patterns

**Use pytest markers for authentication** (instead of passing fixtures):
```python
@pytest.mark.requires_hafiz(hafiz_id=1)
def test_settings_page(page):
    # Auto-logged in as hafiz 1
    page.goto("/hafiz/settings")
```

**Validate HTMX requests** (not just UI):
```python
with page.expect_response("**/revision/rate/*") as response_info:
    page.select_option("select.rating-dropdown", "1")

response = response_info.value
assert response.status == 200
```

**Interactive debugging**:
```python
page.pause()  # Opens Playwright inspector
```

See `docs/testing-approach.md` → "Advanced Playwright Patterns" for complete implementation.

### Database
- **Path**: SQLite database at `data/quran_v10.db`
- **Migrations**: Uses fastmigrate with numbered SQL files in `migrations/` directory (format: `0001-description.sql`)
- **Migration system**: Automatically runs on app startup via `globals.py`

### Frontend Stack
- **Framework**: FastHTML (server-side rendered HTML with HTMX)
- **UI Library**: MonsterUI (provides pre-built FastHTML components)
- **Interactivity**:
  - HTMX (hx-boost enabled globally for SPA-like navigation, auto-submit on rating dropdown change)
  - Alpine.js (client-side reactivity for tabs, toggles)
  - Hyperscript (dynamic button states)
- **Styles**: Custom CSS in `public/css/style.css`, MonsterUI theme (blue)
- **JavaScript**: `public/script.js` for custom interactions

**DaisyUI Tabs with Alpine.js** (see `main.py` home page):
```python
# Tab buttons with Alpine.js state management
def make_tab_button(mode_code):
    return A(
        f"{icon} {name}",
        cls="tab",
        **{
            "@click": f"activeTab = '{mode_code}'",
            ":class": f"activeTab === '{mode_code}' ? 'tab-active [--tab-bg:oklch(var(--p)/0.1)] [--tab-border-color:oklch(var(--p))]' : ''",
        },
    )

# Tab content panels with x_show
Div(content, x_show=f"activeTab === '{mode_code}'")

# Wrap in container with x_data
Div(
    Div(*tab_buttons, cls="tabs tabs-lifted", role="tablist"),
    *tab_contents,
    x_data=f"{{ activeTab: '{default_mode}' }}",
)
```

**MonsterUI LabelInput** - auto-derives `id` and `name` from label:
```python
# Verbose (unnecessary)
LabelInput(
    label="Email",
    name="email",
    type="email",
    required=True,
    placeholder="Email",
)

# Simplified (preferred)
LabelInput("Email", type="email", required=True)
```
- First positional arg is `label`
- `id` auto-derived from label (lowercased): `"Email"` → `id="email"`
- `name` follows `id`
- `placeholder` optional (omit unless needed)
- Keep `type=` for email/password (not auto-inferred)
- Keep `required=True` when needed

## Architecture Overview

### Core Modes System
The application is built around 5 distinct memorization modes, each with different revision algorithms:

1. **New Memorization (mode_code='NM')**: For learning completely new pages
2. **Daily Reps (mode_code='DR')**: Daily repetition (1-day interval) after initial memorization
3. **Weekly Reps (mode_code='WR')**: Weekly repetition (7-day interval) after daily graduation
4. **Full Cycle (mode_code='FC')**: Sequential maintenance of all memorized content
5. **SRS Mode (mode_code='SR')**: Adaptive spaced repetition for problematic pages

Mode codes are defined as constants in `globals.py`: `NEW_MEMORIZATION_MODE_CODE`, `DAILY_REPS_MODE_CODE`, `WEEKLY_REPS_MODE_CODE`, `FULL_CYCLE_MODE_CODE`, `SRS_MODE_CODE`.

**Important:** The codebase recently migrated from numeric `mode_id` (1-5) to 2-character `mode_code` ('FC', 'NM', 'DR', 'WR', 'SR'). The `code` column is now the PRIMARY KEY in the `modes` table. All Python code uses `mode_code` exclusively.

### Mode Progression Flow
- **New Memorization** → **Daily Reps** (after first review)
- **Daily Reps** → **Weekly Reps** (after 7 reviews at 1-day intervals)
- **Weekly Reps** → **Full Cycle** (after 7 reviews at 7-day intervals)
- **Full Cycle** → **SRS Mode** (when revision receives Ok or Bad rating, triggered on date close)

### Authentication & Multi-User Architecture
The app uses a two-tier authentication system implemented via beforeware in `app/common_function.py`:

1. **User Level** (`user_auth`): Account owner authentication
   - Session key: `user_auth` (user_id)
   - Redirects to `/users/login` if not authenticated

2. **Hafiz Level** (`hafiz_auth`): Profile selection within account
   - Session key: `auth` (hafiz_id)
   - Redirects to `/users/hafiz_selection` if not selected
   - Automatically adds `hafiz_id` to database queries via `xtra()` for `revisions`, `hafizs_items`, and `plans` tables

This allows one account (parent/teacher) to manage multiple hafiz profiles (children/students). Each hafiz profile belongs to exactly one user via the `user_id` foreign key in the `hafizs` table.

### UI/UX Design Patterns

**Hafiz Selection Page** (`/users/hafiz_selection`):
- **Mobile-First Design**: Compact single-row layout per hafiz to minimize scrolling on mobile devices
- **Visual Hierarchy**:
  - Current hafiz: Green background (`bg-green-50`) with green border (`border-green-400`), shows "← Go Back to [Name]"
  - Other hafizs: White background with hafiz name button + delete icon (🗑️)
- **Button Layout**:
  - Non-current hafiz: `[Name Button (flex-1)] [🗑️ Delete Icon (minimal)]`
  - Current hafiz: `[← Go Back to Name (full-width)]` with green highlight
- **Delete Safety**: Current hafiz cannot delete themselves (delete button hidden when active)
- **HTMX Integration**:
  - `hx-post` for hafiz switching
  - `hx-delete` for deletion with `hx-confirm` for confirmation dialogs
- **Test Selectors**: All buttons use `data-testid` attributes for E2E test stability

**Key UI Components** (`app/users_view.py`):
- `render_hafiz_card(hafiz, auth)`: Conditional rendering based on `is_current_hafiz`
- `render_add_hafiz_form()`: Minimalist form (name + daily_capacity only)
- `render_hafiz_selection_page(cards, hafiz_form)`: Grid layout with flexbox wrapping

### Database Schema Key Points

**Core Tables:**
- `users`: User accounts (parents/teachers)
  - `email`, `password`, `name`

- `hafizs`: Hafiz profiles (one-to-many with users)
  - `name`: Hafiz name
  - `user_id`: Foreign key to users (ON DELETE CASCADE)
  - `daily_capacity`: Number of pages for daily revision
  - `current_date`: Virtual date for this hafiz (allows independent timelines)

- `items`: Quran content broken into items (full pages or page parts)
  - `page_id`: Page number (1-604)
  - `item_type`: "page" or "page-part"
  - `part`: Which part of page (e.g., "1", "2", "3" for multi-part pages)
  - `active`: Whether item is currently in use

- `hafizs_items`: Tracks each hafiz's progress per item
  - `mode_code`: Current mode ('FC', 'NM', 'DR', 'WR', 'SR')
  - `memorized`: Boolean flag indicating if item has been memorized
  - `next_review`, `next_interval`: For scheduled reviews (used by DR, WR, SR modes)
  - `last_interval`: Actual days since last review
  - `bad_streak`, `good_streak`: Performance tracking
  - `page_number`: Reference to the page in the Quran

- `revisions`: Individual review records
  - `item_id`, `hafiz_id`, `mode_code`, `revision_date`
  - `rating`: -1 (Bad), 0 (Ok), 1 (Good)
  - `next_interval`: Calculated interval for SRS reviews
  - `plan_id`: Groups revisions into cycles (for Full Cycle mode)

- `plans`: Defines Full Cycle revision plans
  - `hafiz_id`, `start_page`, `completed`
  - Used to track progress through complete Quran cycles

**Critical Relationships:**
- One user has many `hafizs` (one-to-many relationship via `hafizs.user_id`)
- One hafiz has many `hafizs_items` (one per Quran item)
- One item can have many `revisions` across different modes and dates
- Revisions in Full Cycle mode link to `plans` via `plan_id`

### Key Business Logic

**Date Management:**
Each hafiz has a `current_date` field that acts as the "system date" for that profile. This allows:
- Independent timelines for different hafiz profiles
- Testing and demo scenarios
- Review of past data without affecting current progress

The "Close Date" operation (`main.py:372-399`) is the core engine that:
1. Processes all reviews for the current date across all modes
2. Updates `hafizs_items` based on mode-specific logic
3. Triggers SRS mode for Full Cycle items that received Ok or Bad ratings today
4. Recalculates statistics (streaks, counts, intervals)
5. Advances the hafiz's `current_date` by one day

**Mode-Specific Update Logic:**
- **Full Cycle (FC)**: Updates `last_interval` based on actual days since last review; if item is in SRS, moves `next_review` forward using `next_interval`
- **New Memorization (NM)**: Promotes to Daily Reps mode on close, sets `memorized=True`
- **Daily Reps (DR) & Weekly Reps (WR)**: Handled by `update_rep_item()` in `app/fixed_reps.py`
  - Counts reviews in current mode (threshold: 7 for both)
  - DR → WR after 7 reviews at 1-day intervals
  - WR → FC after 7 reviews at 7-day intervals
  - Updates `next_review = current_date + interval` if staying in mode
- **SRS Mode (SR)**: Handled by `update_hafiz_item_for_srs()` in `app/srs_reps.py`
  - **Entry**: Items move from Full Cycle to SRS when they receive Ok or Bad ratings (triggered by `start_srs_for_ok_and_bad_rating()` during Close Date)
    - Bad rating (-1) → 3-day starting interval
    - Ok rating (0) → 10-day starting interval
    - Good rating (1) → Stays in Full Cycle (no SRS entry)
  - **Progression**: Uses prime number interval sequence: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101]
    - Finds current interval in sequence, calculates triplet: [left, current, right]
    - Bad rating (-1) → left, Ok rating (0) → current, Good rating (1) → right
  - **Graduation**: Returns to Full Cycle when `next_interval > 99`
  - Updates `next_review = current_date + next_interval` after each review

### File Structure & MVC+S Pattern

The app follows an **MVC + Service** pattern (inspired by Java Spring / Phoenix contexts):

| Layer | File Suffix | Purpose | Example Functions |
|-------|-------------|---------|-------------------|
| **Controller** | `*_controller.py` | HTTP routes, request/response | Route handlers only |
| **Service** | `*_service.py` | Business logic, workflows, algorithms | `update_rep_item()`, `start_srs()` |
| **Model** | `*_model.py` | Data access, queries, CRUD | `get_items_by_type()`, `update_hafiz_item()` |
| **View** | `*_view.py` | UI rendering, HTML components | `render_table()`, `render_form()` |

**Flow:** Controller → Service (business logic) → Model (data) → View (rendering)

**Naming Convention:**
```
app/
├── hafiz_controller.py    # Routes: GET/POST /hafiz/*
├── hafiz_service.py       # Business logic (if complex enough)
├── hafiz_model.py         # Data queries
├── hafiz_view.py          # UI components
```

**Main Application:**
- `main.py`: App initialization, home page routes, Close Date logic
- `app/globals.py`: Database setup, mode constants, table references
- `app/utils.py`: Pure utility functions (dates, formatting)
- `app/app_setup.py`: App configuration, authentication beforeware

**Feature Modules:**
- `app/users_*`: User authentication (controller, model, view)
- `app/revision_*`: Revision CRUD (controller, model, view)
- `app/hafiz_*`: Hafiz settings
- `app/profile_*`: Memorization profile/status
- `app/new_memorization_*`: New memorization workflow
- `app/page_details_*`: Page/item detail views
- `app/admin_*`: Admin utilities

**Service Modules (business logic):**
- `app/fixed_reps_service.py`: Daily/Weekly Reps mode transitions
- `app/srs_reps_service.py`: SRS interval calculations and mode logic

**Shared Modules:**
- `app/common_function.py`: Shared utilities, re-exports from model/view
- `app/common_model.py`: Shared data access functions
- `app/common_view.py`: Shared UI components

**Supporting Files:**
- `docs/design.md`: Comprehensive design vision
- `docs/srs-mode-design.md`: SRS algorithm specifications

### Common Development Patterns

**Adding/Removing Revisions:**
Use `add_revision_record()` and `remove_revision_record()` from `app/common_function.py`. These handle both database operations and hafizs_items stat updates.

**Rendering Summary Tables:**
The `make_summary_table()` function (app/common_function.py) generates mode-specific review tables with rating dropdowns. It handles:
- Item filtering by mode and date
- Rating dropdowns with auto-submit (HTMX `hx_trigger="change"`)
- Row background color based on rating (green=good, yellow=ok, red=bad)
- Displays: Page number, Start text, Rating dropdown

**Database Queries:**
- Use table objects from `globals.py` (e.g., `revisions()`, `hafizs_items()`)
- Each table has a dataclass (e.g., `Revision`, `Hafiz_Items`) for type safety
- For complex queries, use `db.q()` with raw SQL
- Always include `hafiz_id` filters (automatically added by `xtra()` when using beforeware)
- FastHTML's database layer provides CRUD operations: `table.insert()`, `table.update()`, `table[id]`, `table.delete()`

**Page References:**
Items can represent full pages or page parts (e.g., page 5 might have items for "5.1", "5.2", "5.3"). Use `get_page_description()` to render human-readable descriptions.

**Creating New Routes:**
When adding new sub-apps, mount them in `main.py` using FastHTML's `Mount()` and add beforeware for authentication:
```python
app, rt = create_app_with_auth(
    routes=[
        Mount("/users", users_app, name="users"),
        Mount("/new_module", new_module_app, name="new_module"),
    ]
)
```

---

## Key Business Logic to Test

**Mode Transition Thresholds:**
- DR → WR: 7 reviews (configurable in `REP_MODES_CONFIG`)
- WR → FC: 7 reviews
- FC → SR: When Full Cycle revision receives Ok (0) or Bad (-1) rating (triggered on Close Date)
  - Bad rating → 3-day starting interval
  - Ok rating → 10-day starting interval
- SR → FC: next_interval > SRS_END_INTERVAL (99 days)

**Close Date Processing:**
The Close Date operation is critical and must:
1. Process all revisions for current_date
2. Update hafizs_items based on mode-specific logic
3. Trigger SRS entry for Full Cycle items with Ok or Bad ratings (via `start_srs_for_ok_and_bad_rating()`)
4. Advance current_date by 1 day

All mode progression tests must verify Close Date works correctly.
