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

**Migration to Python Testing**:
- Existing E2E tests (Wallaby/Elixir) remain in phoenix_migration worktree
- **NEW**: Python Playwright tests being added to `tests/` directory for code coverage
- Goal: Minimal E2E test suite (6-8 tests) with pytest-cov integration
- Approach: E2E-first, add integration tests only if coverage gaps exist

## Development Commands

### Python Environment
- **Run the application**: `uv run main.py` (uses uv, NOT `python main.py`)
- **Install dependencies**: `uv sync`
- **Add new dependency**: `uv add <package-name>`
- **Run tests**: `uv run pytest` (pytest configured but no tests currently exist)
- **Base URL**: `http://localhost:5001` (configurable via BASE_URL env var)

### End-to-End Testing
- **Location**: E2E tests are maintained in a separate git worktree at `../quran-srs-phoenix_migration/test/e2e_test.exs`
- **Framework**: Uses Wallaby (Elixir's browser automation library) with ChromeDriver
- **Purpose**: Tests the FastHTML application UI flows (login, hafiz selection, CRUD operations, mode-specific workflows)
- **Running E2E tests**: From the phoenix_migration worktree, run `mix test --only e2e`
- **Note**: The phoenix_migration worktree is used for both Phoenix (future) and FastHTML (current) e2e tests

#### E2E Test Coverage Status

**Completed Tests (✅):**
1. User authentication and hafiz selection
2. Hafiz CRUD operations (create, switch, delete)
3. Full Cycle mode visibility verification
4. **Full Cycle - Review item due today** (rating dropdown auto-submit via HTMX)

**Pending Tests (⏳):**
- Full Cycle: Item not due doesn't appear (3 more FC tests)
- SRS: Rating affects interval progression (3 SRS tests)
- Mode Progression: NM→DR→WR→FC graduation (3 progression tests)

**Test Infrastructure:**
- Database seeding helpers (`seed_item_in_mode`, `seed_revision`)
- Hafiz management helpers (`create_test_hafiz_and_switch`, `cleanup_test_hafiz`)
- Assertion helpers (`assert_revision_exists`, `assert_item_in_mode`)
- Date manipulation helper (`set_hafiz_date`)
- All `data-testid` attributes added to core UI components

#### E2E Test Structure & Best Practices

**Test Organization:**
- Use `feature` blocks for each major user flow
- Create reusable helper functions for common actions (`login/2`, `create_hafiz/3`, `delete_hafiz/2`)
- Each feature should test a complete user journey from start to finish

**Selector Strategy:**
- **Primary**: Use `data-testid` attributes for reliable element targeting (e.g., `data-testid="switch-{name}-hafiz-button"`)
- **Fallback**: Use semantic selectors (e.g., `css("h3", text: "Name")`) for content verification
- **Why**: `data-testid` is stable across UI changes; text/class selectors are fragile

**Handling Dynamic Content:**
- Use timestamp-based unique identifiers for test data (e.g., `"E2E Test #{:os.system_time(:millisecond)}"`)
- Prevents test collisions when running concurrently or with leftover data
- Use `count: 1` assertions for unique identifiers, `minimum: 1` for "at least exists" checks

**Common Wallaby Patterns:**

1. **Browser Confirmation Dialogs** (`hx-confirm` in HTMX):
   ```elixir
   # WRONG: accept_dialogs() doesn't exist
   # CORRECT:
   accept_confirm session, fn session ->
     click(session, css("button[data-testid='delete-button']"))
   end
   session  # Must return session for pipe chain
   ```

2. **Waiting for HTMX Updates**:
   - `assert_has/2` polls automatically (default 3 seconds)
   - No need for explicit waits in most cases
   - Use `count: N` or `minimum: N` to verify exact/minimum element counts

3. **Newly Created Resources**:
   - Don't assume Full Cycle mode appears for new hafizs (requires memorized pages)
   - Check for always-visible elements instead (e.g., "System Date:", "Close Date" button)
   - Understand business logic: new hafizs have `hafizs_items` but with `memorized=false`

**Common Errors & Solutions:**

| Error | Cause | Solution |
|-------|-------|----------|
| `undefined function accept_dialogs/1` | Wrong Wallaby API | Use `accept_confirm/2` instead |
| `FunctionClauseError` with dialog text | `accept_confirm` returns text, not session | Explicitly return `session` after `accept_confirm` |
| `Expected 1 element, found 3` | Non-unique selector or leftover test data | Use timestamp-based unique names + `count: 1` |
| `ExpectationNotMetError` for mode tables | Business logic prevents display | Check for always-visible elements instead |
| Alert/confirm dialog errors | HTMX `hx-confirm` creates native browser dialogs | Use `accept_confirm/2` wrapper function |

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
- **Full Cycle** → **SRS Mode** (when bad_streak >= 1, triggered on date close)

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

The "Close Date" operation (`main.py:457-481`) is the core engine that:
1. Processes all reviews for the current date across all modes
2. Updates `hafizs_items` based on mode-specific logic
3. Triggers SRS mode for items with `bad_streak >= 1`
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
  - Uses prime number interval sequence: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101]
  - Finds current interval in sequence, calculates triplet: [left, current, right]
  - Bad rating (-1) → left, Ok rating (0) → current, Good rating (1) → right
  - Graduates to FC when `next_interval > 99`, resets `bad_streak=0`
  - Otherwise updates `next_review = current_date + next_interval`

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

## E2E Testing Roadmap

### Test Strategy
All E2E tests use **temporary test hafizs** that are:
- Created with timestamp-based unique names (e.g., "E2E FC Review 1762408089619")
- Seeded with specific data via direct database manipulation
- Deleted after each test (CASCADE DELETE cleans up related records)

This approach ensures:
- Test isolation (no shared state between tests)
- No corruption of production data (Siraj hafiz)
- Repeatable tests (clean slate each time)

### Completed Tests ✅

#### Test Infrastructure (File: `../quran-srs-phoenix_migration/test/e2e_test.exs`)

**Database Helpers:**
```elixir
seed_item_in_mode(hafiz_id, item_id, mode_code, opts)  # Creates/updates hafizs_items
seed_revision(hafiz_id, item_id, mode_code, date, rating)  # Inserts revision record
set_hafiz_date(hafiz_id, date_string)  # Updates hafiz's current_date
get_hafiz_id_by_name(name)  # Retrieves hafiz_id from database
```

**Test Management:**
```elixir
create_test_hafiz_and_switch(session, name_suffix)  # Creates hafiz, logs in, switches to it
cleanup_test_hafiz(session, hafiz_name)  # Switches away and deletes test hafiz
```

**Assertions:**
```elixir
assert_revision_exists(hafiz_id, item_id, mode_code, date, rating)
assert_item_in_mode(hafiz_id, item_id, expected_mode)
get_hafizs_items_from_db(hafiz_id, item_id)  # Returns item details map
```

#### Passing Tests:
1. **User authentication** - Login flow with email/password
2. **Hafiz CRUD** - Create, switch, delete hafiz profiles
3. **Full Cycle visibility** - FC mode always visible on home page
4. **FC - Review item due today** - Rating dropdown auto-submit via HTMX

### Pending Tests ⏳

#### Phase 1: Full Cycle Tests (3 remaining)

**Test 2: FC - Item not due doesn't appear**
```elixir
# Seed item with next_review = "2025-11-10" (future)
# Set current_date = "2025-11-07"
# Verify item does NOT appear in FC table
```

**Test 3: FC - Already reviewed item shows correct state**
```elixir
# Seed item with next_review = current_date
# Seed revision for that item (rating = 1)
# Verify dropdown shows selected value
# Verify row has green background (reviewed as good)
```

**Test 4: FC - Bad rating moves to SRS after Close Date**
```elixir
# Seed item in FC mode (bad_streak = 0)
# Review with Bad rating (-1)
# Click Close Date → Confirm
# Verify item.mode_code changed to 'SR'
# Verify bad_streak incremented
```

#### Phase 2: SRS Tests (3 tests)

**Test 5: SR - Good rating increases interval**
```elixir
# Seed item in SR mode (next_interval = 7)
# Review with Good rating (1)
# Close Date
# Verify next_interval > 7 (SRS algorithm progression)
```

**Test 6: SR - Bad rating resets/decreases interval**
```elixir
# Seed item in SR mode (next_interval = 14)
# Review with Bad rating (-1)
# Close Date
# Verify next_interval < 14 (penalty for bad performance)
```

**Test 7: SR - Graduation back to Full Cycle**
```elixir
# Seed item in SR mode (next_interval = 28, near 30-day threshold)
# Review with Good rating
# Close Date
# Verify item.mode_code changed to 'FC'
# Verify bad_streak reset to 0
```

#### Phase 3: Mode Progression Tests (3 tests)

**Test 8: NM → DR Progression**
```elixir
# Seed item in NM mode (memorized = false)
# Review with Good rating
# Close Date
# Verify item.mode_code changed to 'DR'
# Verify memorized = true
```

**Test 9: DR → WR Progression (7 reviews)**
```elixir
# Seed item in DR mode with 6 historical reviews
# Perform 7th review
# Close Date
# Verify item.mode_code changed to 'WR'
# Verify next_interval = 7 (weekly interval)
```

**Test 10: WR → FC Progression (7 reviews)**
```elixir
# Seed item in WR mode with 6 historical reviews (7 days apart)
# Perform 7th review
# Close Date
# Verify item.mode_code changed to 'FC'
# Verify next_interval = NULL (FC doesn't use fixed intervals)
# Verify next_review = NULL
```

### Implementation Notes

**HTMX Testing Pattern:**
Rating dropdowns auto-submit on change, so use JavaScript to trigger:
```elixir
session
|> execute_script("document.querySelector('select[data-testid=\"rating-#{item_id}\"]').value = '1'")
|> execute_script("document.querySelector('select[data-testid=\"rating-#{item_id}\"]').dispatchEvent(new Event('change'))")
Process.sleep(2000)  # Give HTMX time to process
```

**Historical Revisions for Progression Tests:**
Use loops to seed multiple revisions:
```elixir
for day <- 0..5 do
  date = Date.add(~D[2025-11-01], day) |> Date.to_string()
  seed_revision(hafiz_id, item_id, "DR", date, 1)
end
```

**Data Sources:**
- Use Siraj hafiz (hafiz_id=1) historical data to understand behavior
- Implement tests with temporary test hafizs for isolation

### Running Tests

**Start FastHTML server first:**
```bash
uv run main.py  # From quran-srs directory
```

**Run all E2E tests:**
```bash
cd ../quran-srs-phoenix_migration
mix test --only e2e
```

**Run specific test:**
```bash
mix test test/e2e_test.exs:236  # Line number of feature block
```

### Key Business Logic to Test

**Mode Transition Thresholds:**
- DR → WR: 7 reviews (configurable in `REP_MODES_CONFIG`)
- WR → FC: 7 reviews
- FC → SR: bad_streak >= 1 (triggered on Close Date)
- SR → FC: next_interval > SRS_END_INTERVAL (30 days)

**Close Date Processing:**
The Close Date operation is critical and must:
1. Process all revisions for current_date
2. Update hafizs_items based on mode-specific logic
3. Trigger SRS demotion for bad streaks
4. Advance current_date by 1 day

All mode progression tests must verify Close Date works correctly.
