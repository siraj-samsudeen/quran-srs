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
- Python Playwright tests in `tests/` directory for E2E testing with code coverage
- Goal: Minimal E2E test suite (6-8 tests) with pytest-cov integration
- Approach: E2E-first, add integration tests only if coverage gaps exist

## Development Commands

### Python Environment
- **Run the application**: `uv run main.py` (uses uv, NOT `python main.py`)
- **Run in test mode**: `ENV=test uv run main.py` (uses test database)
- **Install dependencies**: `uv sync`
- **Add new dependency**: `uv add <package-name>`
- **Run tests**: `uv run pytest tests/e2e -v` (Playwright E2E tests)
- **Run with coverage**: `uv run pytest tests/e2e --cov --cov-report=html`
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

**Phoenix LiveView-Inspired Architecture**:
Our testing follows Phoenix's two-layer approach with strict separation of concerns:

**1. UI Tests** (`tests/ui/`) - Browser-based tests with Playwright
- **Purpose**: Test complete user workflows through the browser
- **Framework**: Playwright Python with pytest
- **Running tests**:
  ```bash
  # Terminal 1: Start app in test mode
  ENV=test uv run main.py

  # Terminal 2: Run UI tests
  uv run pytest tests/ui -v
  ```
- **Key Rules (Phoenix-style)**:
  - ✅ **Setup**: Can seed test data via DB (arrange phase)
  - ✅ **Action**: Interact through browser only
  - ✅ **Assert**: Verify UI elements ONLY (no DB assertions)
  - ❌ **Never**: Assert on database state directly

**2. Backend Tests** (`tests/backend/`) - Business logic tests
- **Purpose**: Test business logic, algorithms, and data transformations
- **Framework**: Pure Python with pytest (no browser)
- **Running tests**:
  ```bash
  uv run pytest tests/backend -v
  ```
- **Key Rules**:
  - ✅ **Setup**: Seed test data via DB
  - ✅ **Action**: Call functions/methods directly
  - ✅ **Assert**: Verify database state and return values
  - ⚡ **Fast**: No browser overhead

**Run all tests**: `uv run pytest -v`

#### UI Test Example (Phoenix-style)

```python
def test_user_can_login(page, db_connection):
    # Arrange: Seed data via DB (setup is allowed)
    seed_user(db_connection, "test@example.com", "password123")

    # Act: Interact through browser
    page.goto("/users/login")
    page.fill("input[name='email']", "test@example.com")
    page.fill("input[name='password']", "password123")
    page.click("button[type='submit']")

    # Assert: Verify UI ONLY (no DB assertions!)
    expect(page).to_have_url("/users/hafiz_selection")
    expect(page.locator("text=Hafiz Selection")).to_be_visible()
```

#### Backend Test Example

```python
def test_dr_to_wr_progression(db_connection):
    # Arrange: Seed data
    hafiz_id = create_test_hafiz(db_connection, "Test Hafiz")
    seed_item_in_mode(db_connection, hafiz_id, item_id=1, mode="DR")
    seed_revisions(db_connection, hafiz_id, item_id=1, count=6)

    # Act: Call business logic directly
    from app.fixed_reps import update_rep_item
    update_rep_item(hafiz_id, item_id=1, mode_code="DR")

    # Assert: Verify database state
    item = get_hafizs_item(db_connection, hafiz_id, item_id=1)
    assert item['mode_code'] == 'WR'
    assert item['next_interval'] == 7
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

**Test Data Cleanup:**
- Tests should be self-contained: create → use → delete
- Rely on database CASCADE DELETE for related records
- Unique naming prevents interference between test runs

### Database
- **Path**: SQLite database at `data/quran_v10.db`
- **Migrations**: Uses fastmigrate with numbered SQL files in `migrations/` directory (format: `0001-description.sql`)
- **Migration system**: Automatically runs on app startup via `globals.py`

### Frontend Stack
- **Framework**: FastHTML (server-side rendered HTML with HTMX)
- **UI Library**: MonsterUI (provides pre-built FastHTML components)
- **Interactivity**:
  - HTMX (hx-boost enabled globally for SPA-like navigation, auto-submit on rating dropdown change)
  - Hyperscript (dynamic button states)
- **Styles**: Custom CSS in `public/css/style.css`, MonsterUI theme (blue)
- **JavaScript**: `public/script.js` for custom interactions

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

### File Structure & MVC Pattern

The app follows an MVC-like pattern where applicable:
- **Controllers** (`*_controller.py`): Route handlers and request processing
- **Views** (`*_view.py`): UI components, forms, display logic
- **Models** (`*_model.py`): Data access layer, business logic

**Main Application:**
- `main.py`: Main app initialization, home page route with all summary tables, Close Date logic
- `globals.py`: Database setup, mode constants (FULL_CYCLE_MODE_CODE, DAILY_REPS_MODE_CODE, etc.), table references
- `utils.py`: Helper functions for dates, formatting, list operations

**App Modules (mounted as sub-apps via FastHTML's Mount):**
- `app/users_controller.py` + `app/users_view.py`: User authentication routes and UI
- `app/revision.py` + `app/revision_view.py` + `app/revision_model.py`: Full MVC for revision CRUD operations
- `app/new_memorization.py`: New memorization workflow
- `app/profile.py`: Hafiz profile management
- `app/hafiz.py`: Hafiz-specific settings (capacity, current_date override)
- `app/admin.py`: Admin utilities and database management
- `app/page_details.py`: Detailed item/page information views
- `app/common_function.py`: Shared utilities (authentication beforeware, rendering helpers, data fetching)
- `app/fixed_reps.py`: Daily/Weekly Reps logic with `REP_MODES_CONFIG` dict
- `app/srs_reps.py`: SRS mode logic including interval calculations

**Supporting Files:**
- `docs/design.md`: Comprehensive design vision through user conversations
- `docs/srs-mode-design.md`: SRS algorithm specifications
- `docs/user_personas.md`: User personas for design decisions

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
