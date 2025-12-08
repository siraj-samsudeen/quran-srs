# TDD Rebuild Plan

**Branch:** `phoenix-rebuild`

---
## MVC Refactoring

### Hafiz Module (Phoenix MVC Pattern) ✅
- [x] Create hafiz_model.py with Hafiz dataclass and table reference
- [x] Make hafiz_model.py self-contained (only imports db from globals)
- [x] Implement table linking pattern (hafizs.cls = Hafiz)
- [x] Create get_hafiz() and update_hafiz() model functions
- [x] Update hafiz_controller.py to import from hafiz_model
- [x] Remove Hafiz dataclass from globals.py
- [x] Update all imports across codebase (app_setup, common_model, common_view, users_model)
- [x] Add migration note in globals.py explaining Phoenix pattern
- [x] Create hafiz_test.py with unit tests (2 tests)
- [x] Create hafiz_test.py with integration tests (3 tests)
- [x] Load test credentials from .env file in tests
- [x] Verify all 5 hafiz tests passing
- [x] Create app/revision_model.py with missing CRUD functions
- [x] Implement cycle_full_cycle_plan_if_completed() for Close Date logic

### common_function.py Cleanup (Layer Separation) ✅
- [x] Move populate_hafizs_items_stat_columns() to common_model.py
- [x] Move get_actual_interval() to common_model.py
- [x] Move get_page_count() to common_model.py
- [x] Move get_full_review_item_ids() to common_model.py
- [x] Move get_srs_daily_limit() to common_model.py
- [x] Move get_full_cycle_daily_limit() to common_model.py
- [x] Move group_by_type() to utils.py
- [x] Add re-exports in common_function.py for backward compatibility
- [x] Update common_model.py imports (math, mode constants, utils)
- [x] Verify all 8 mode transition tests still passing
- [x] Reduce common_function.py to re-exports + 1 complex function

### Remove Re-exports from common_function.py (Per Reviewer Feedback)
**Issue:** common_function.py re-exports functions from app_setup, common_model, common_view, and utils for backward compatibility. This adds unnecessary indirection.

**Goal:** Remove re-exports and update all imports to use direct imports from source modules.

**Files to update (11 files):**
- [ ] main.py - Replace `from app.common_function import *` with direct imports
- [ ] app/users_model.py - Update to import from source modules
- [ ] app/srs_reps_service.py - Update to import from source modules
- [ ] app/revision_view.py - Update to import from source modules
- [ ] app/revision.py - Update to import from source modules
- [ ] app/profile.py - Update to import from source modules
- [ ] app/page_details.py - Update to import from source modules
- [ ] app/new_memorization.py - Update to import from source modules
- [ ] app/fixed_reps_service.py - Update to import from source modules
- [ ] app/admin.py - Update to import from source modules
- [ ] Remove all re-exports from common_function.py (keep only make_summary_table)
- [ ] Run all tests to verify nothing broke

**Source module mapping:**
- `create_app_with_auth`, `user_auth`, `*_bware`, `*_toast`, `*_header` → `app.app_setup`
- `get_current_date`, `get_page_count`, `add_revision_record`, etc. → `app.common_model`
- `main_area`, `render_*`, `rating_dropdown`, etc. → `app.common_view`
- `group_by_type` → `app.utils`

### Remaining Modules to Refactor
- [ ] Refactor profile.py to MVC (profile_controller, profile_model, profile_view)
- [ ] Refactor new_memorization.py to MVC
- [ ] Refactor admin.py to MVC
- [ ] Refactor page_details.py to MVC
- [ ] Refactor make_summary_table() (currently mixes service + view layers)

### Future: Database Migration (After MVC Complete)
- [ ] Switch from Fastlite to FastSQL (class-first with SQLAlchemy)
- [ ] Configure PostgreSQL connection for Neon
- [ ] Test with PostgreSQL locally
- [ ] Deploy to Neon for production

---

## User Journeys

### Journey 1: New User Day 1
The user registers, logs in, creates hafiz profile, marks previously memorized pages, sets daily capacity, starts the first Full Cycle, rates pages, closes the day, sees progress summary, and continues to tomorrow's review.

- [ ] Home page displays signup option
- [ ] User signs up successfully 
- [ ] User logs in
- [ ] User is asked to create a hafiz profile and creates one
- [ ] User marks memorized pages in his profile
- [ ] User is taken to hafiz settings page
- [ ] User views and updates "daily capacity" (number of pages to review per day)
- [ ] User is taken to page with explanation of different revision modes
- [ ] User is asked to start a full cycle for the pages he has memorized
- [ ] User is taken to the home page where full cycle pages for current day is displayed
- [ ] User selects rating from dropdown for each item
- [ ] User clicks "Close Date" button
- [ ] System advances current_date by one day and shows a Confirmation page with today's summary
- [ ] Confirmation page displays two buttons: "Continue to Tomorrow's Review" (primary) and "Done for Today" (secondary)
- [ ] Page auto-redirects to Tomorrow's Review after 10 seconds if user takes no action
- [ ] User clicks "Continue to Tomorrow's Review" OR auto-redirect happens
- [ ] Home page displays next day's items

---

## Detailed Feature Breakdown

### Smoke Test
- [ ] Default home page is displayed

### User Authentication
- [ ] Home page displays options to signup or login
- [ ] Signup page displays form
- [ ] User can submit signup form successfully
- [ ] Login page loads and displays form
- [ ] User can login with valid credentials
- [ ] User can logout and session clears

### Hafiz Profile Management
- [ ] Hafiz selection page displays after login
- [ ] User can create hafiz profile via form
- [ ] User can switch between hafiz profiles
- [ ] User can delete non-current hafiz with confirmation
- [ ] Hafiz settings page displays current preferences
- [ ] User can update hafiz settings (name, daily capacity, current date)
- [ ] User can access theme picker from settings

### Profile View (Mark Memorized Pages)
- [ ] Profile page displays with Juz/Surah/Page navigation tabs
- [ ] Each row shows Juz/Surah/Page with memorized checkbox
- [ ] Checkbox shows checked/unchecked/indeterminate (partial memorization)
- [ ] User can filter view by memorized or not_memorized status
- [ ] User can toggle memorized status for entire group (all child pages)
- [ ] Each row displays Juz, Surah, and Page range details
- [ ] Clicking row opens modal showing all child pages
- [ ] Modal allows selecting/deselecting individual child pages

### Full Cycle Mode
- [ ] FC items appear in Full Cycle table
- [ ] FC table respects daily_capacity limit
- [ ] FC table auto-expands when limit reached
- [ ] FC calculates last_interval on Close Date
- [ ] FC tracks plan_id for each revision
- [ ] FC completes plan when cycle finishes
- [ ] FC creates new plan automatically
- [ ] SRS items in FC show Last/Next Interval columns

### Main Dashboard
- [ ] Dashboard displays current date header
- [ ] Dashboard shows Full Cycle mode table with due items
- [ ] Dashboard shows SRS mode table with due items (when items exist)
- [ ] Empty mode tables don't display
- [ ] Close Date button appears on dashboard

### Rating System
- [ ] User can select rating from dropdown for any item
- [ ] Rating dropdown auto-submits
- [ ] Rating creates revision record in database
- [ ] User can change rating after initial selection
- [ ] User can unrate item by selecting "None" (deletes revision)
- [ ] Row changes background color based on rating
- [ ] Full Cycle table auto-expands when daily limit reached

### Close Date Processing
- [ ] Close Date button redirects to confirmation page
- [ ] Confirmation page shows today/yesterday stats summary
- [ ] Confirmation page has Confirm and Cancel buttons
- [ ] Close Date advances current_date by 1 day
- [ ] Close Date processes all revisions for the day
- [ ] Close Date updates hafizs_items for each reviewed item
- [ ] Close Date triggers SRS demotion for bad_streak items
- [ ] Close Date checks and completes Full Cycle plans
- [ ] Close Date creates new plan when previous completes
- [ ] Close Date redirects to home after processing

### SRS Mode
- [ ] SRS items appear in Full Cycle table
- [ ] Good rating advances to next interval
- [ ] Bad rating regresses to previous interval
- [ ] SRS interval follows predefined sequence
- [ ] SRS graduates to FC when interval > 99
- [ ] FC items demote to SRS when bad_streak >= 1
- [ ] SRS demotion triggered on Close Date
- [ ] SRS resets bad_streak on graduation

### New Memorization Mode
- [ ] New Memorization page displays unmemorized items
- [ ] Items grouped by Juz/Surah/Page (navigation tabs)
- [ ] User can mark single item as newly memorized
- [ ] User can bulk mark items as newly memorized
- [ ] User can unmark newly memorized item
- [ ] Recently memorized section shows last 10 items
- [ ] Modal displays descendant items for selection
- [ ] NM items transition to DR on Close Date
- [ ] NM mode sets memorized=True on item

### Daily Reps Mode
- [ ] DR items appear in Daily Reps table when due
- [ ] DR counts review history correctly
- [ ] DR items graduate to WR after 7 reviews
- [ ] DR items schedule next_review = current_date + 1
- [ ] DR items update last_interval on Close Date
- [ ] Dashboard shows Daily Reps table when items exist
- [ ] Close Date triggers DR → WR graduation

### Weekly Reps Mode
- [ ] WR items appear in Weekly Reps table when due
- [ ] WR counts review history correctly
- [ ] WR items graduate to FC after 7 reviews
- [ ] WR items schedule next_review = current_date + 7
- [ ] WR items update last_interval on Close Date
- [ ] Dashboard shows Weekly Reps table when items exist
- [ ] Close Date triggers WR → FC graduation

### Revision Management
- [ ] Revision list page displays all revisions with pagination
- [ ] Revisions filterable and grouped by page
- [ ] User can edit single revision (rating, date, mode, plan)
- [ ] Edit revision form pre-fills current values
- [ ] Update revision recalculates item stats
- [ ] User can delete single revision
- [ ] User can select multiple revisions (checkboxes)
- [ ] Bulk delete removes selected revisions
- [ ] Bulk edit view displays selected revisions
- [ ] Bulk edit allows changing rating/date/mode for all
- [ ] Bulk edit supports sequential page selection
- [ ] Single add view for adding revision to specific page
- [ ] Bulk add view for adding revision to page range
- [ ] Bulk add supports parsing page ranges (e.g., "1-5")

### Page Details View
- [ ] Page Details page lists all pages with counts
- [ ] Table shows columns for each mode
- [ ] Table shows rating summary column
- [ ] Each row clickable to view specific page
- [ ] Specific page details shows all revisions
- [ ] Page details grouped by mode (separate tables)
- [ ] Each mode table shows revision history
- [ ] User can edit page description (inline form)
- [ ] Page description saves and updates display
- [ ] User can refresh stats for specific page (Refresh stats button)

### Datewise Report
- [ ] Report page displays revisions grouped by date
- [ ] Dates sorted descending (most recent first)
- [ ] Each date shows mode breakdown
- [ ] Page ranges displayed compactly (e.g., "1-5, 7")
- [ ] Page ranges are clickable links to bulk edit
- [ ] Report can filter by specific hafiz
- [ ] Report shows earliest_date to current_date range

### Admin Panel
- [ ] Admin page lists all database tables
- [ ] Admin page shows database backup list
- [ ] User can download existing backup file
- [ ] User can create new database backup
- [ ] User can view any table's records
- [ ] Table view shows all columns and records
- [ ] User can edit any record (inline form)
- [ ] User can delete any record with confirmation
- [ ] User can create new record via form
- [ ] User can export table to CSV/JSON
- [ ] User can import table from CSV (with preview)
- [ ] Import preview shows data before committing
- [ ] Import validates and displays errors

---

## Technical Debt & Refactoring

### MVC Refactoring
- [x] Document naming convention in CLAUDE.md
- [x] Rename service files (fixed_reps → fixed_reps_service, srs_reps → srs_reps_service)
- [x] Refactor hafiz.py to MVC (hafiz_controller.py + hafiz_view.py) - pilot
- [x] Rename test folders (tests/ui → tests/e2e, tests/backend → tests/integration)
- [x] Rename test files to {module}_test.py pattern
- [ ] Refactor profile.py to MVC
- [ ] Refactor new_memorization.py to MVC
- [ ] Refactor admin.py to MVC
- [ ] Refactor page_details.py to MVC

### Hafiz Module Improvements
- [ ] Move `create_new_plan()` from hafiz creation to first hafiz switch (lazy initialization)
  - Current: `setup_new_hafiz()` calls both `populate_hafiz_items()` and `create_new_plan()` immediately
  - Future: Only call `populate_hafiz_items()` on creation; defer `create_new_plan()` to first switch
  - Benefit: Faster hafiz creation, plan only created when hafiz is actually used

### Dataclass Migration (Phase 2 - after MVC complete)
- [x] Phase 1: Add explicit dataclass definitions in globals.py (for IDE support)
- [ ] Phase 2: Switch to class-first pattern using db.create(Class)
- [ ] Phase 3: Remove SQL migrations, let FastHTML/FastSQL manage schema

### Database Migration (Phase 3 - after dataclass migration)
- [ ] Switch from Fastlite to FastSQL (SQLAlchemy-based)
- [ ] Configure PostgreSQL connection for Neon
- [ ] Test with PostgreSQL locally
- [ ] Deploy to Neon for production
