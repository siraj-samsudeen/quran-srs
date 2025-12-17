# TDD Rebuild Plan

**Branch:** `phoenix-rebuild`

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
- [ ] User views and updates settings on hafiz settings page
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
- [ ] User can update hafiz settings (name, current date)
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
- [ ] FC table shows all unreviewed items with pagination (daily_capacity removed in migration 0022)
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

## Memorization Status Redesign

A unified dashboard with events tracking, status filtering, and integrated learning flow.
See `docs/profile-redesign-plan.md` for full architecture details.

### Status Model (derived from mode_code)
```
📚 NOT_MEMORIZED  → memorized = false
🌱 LEARNING       → mode_code = NM
🏋️ REPS           → mode_code = DR/WR/FR/MR
💪 SOLID          → mode_code = FC
😰 STRUGGLING     → mode_code = SR
```

### Event Types
`started_new`, `started_renew`, `completed`, `advanced`, `graduated`, `slipped`, `recovered`, `reset`

---

### Slice 1: Stats cards on profile page
Show counts per status at top of profile page.
- [ ] Add `get_status_counts()` query to `common_function.py`
- [ ] Create `render_stats_cards()` component in `profile.py`
- [ ] Add stats cards to profile page (above existing table)
- **Verify**: Profile page shows cards with counts for each status

---

### Slice 2: Status filter
Filter profile table by status (Not Memorized, Learning, Reps, Solid, Struggling).
- [ ] Add `get_status()` function to derive status from mode_code
- [ ] Add status filter dropdown to profile page
- [ ] Make stats cards clickable (clicking card sets filter)
- [ ] Update profile query to filter by derived status
- **Verify**: Click "Struggling" card → only SR pages shown

---

### Slice 3: Mode filter (within Reps)
Filter by specific mode when viewing Reps status.
- [ ] Add mode dropdown (DR/WR/FR/MR) shown when status=Reps or All
- [ ] Update profile query to filter by mode_code
- **Verify**: Filter status=Reps, then mode=Weekly → only WR pages shown

---

### Slice 3.5: Table sorting (DONE)
Add clickable column headers to sort the profile table.
- [x] Add sort parameter to profile route (`?sort=mode&dir=asc`)
- [x] Make Mode, Progress columns clickable to sort
- [x] Update SQL query with ORDER BY based on sort parameter
- [x] Show sort indicator (▲/▼) on active column
- **Verify**: Click "Mode" header → table sorts by mode (DR → WR → FR → MR → FC → SR)

---

### Slice 3.6: Tabulator table integration
Replace manual table with Tabulator for full sorting/filtering/search.
- [ ] Add Tabulator CSS/JS to base template
- [ ] Convert profile table to Tabulator format (JSON data endpoint)
- [ ] Enable sorting on all columns
- [ ] Add global search/filter box
- [ ] Add column filters (dropdown for Mode, text for others)
- [ ] Style Tabulator to match DaisyUI theme
- **Verify**: Table has search box, all columns sortable, Mode has dropdown filter

---

### Slice 4: Health column
Show streak-based health indicator for each page.
- [ ] Add `get_health_indicator()` function (returns icon based on streaks)
- [ ] Add "Health" column to profile table
- **Verify**: Pages with good_streak show 🔥, bad_streak show ⚠️

---

### Slice 5: Page journey on page details
Show timeline of events for a page. (Introduces events table)
- [ ] Create migration `0025-create-page-events.sql`
- [ ] Add `page_events` table to `database.py`
- [ ] Create `app/events_model.py` with `log_event()` and `get_page_history()`
- [ ] Add `render_page_journey()` component
- [ ] Add "Page Journey" section to `/page_details/{item_id}`
- **Verify**: View page details → see "Page Journey" section (empty for now)

---

### Slice 6: Log events for new memorization
When marking page as newly memorized, log events.
- [ ] Add `log_event()` calls in `update_status_as_newly_memorized()` → `started_new` + `completed`
- [ ] Add `log_event()` calls in `bulk_update_status_as_newly_memorized()`
- **Verify**: Mark page as newly memorized → page journey shows events

---

### Slice 7: Log events for rep mode graduation
When page graduates DR→WR→FR→MR→FC, log events.
- [ ] Add `log_event()` in `update_rep_item()` when graduating → `advanced` or `graduated`
- **Verify**: Close date with item at threshold → page journey shows `advanced` event

---

### Slice 8: Log events for SRS transitions
When page enters or exits SRS, log events.
- [ ] Add `log_event()` in `start_srs_for_ok_and_bad_rating()` → `slipped`
- [ ] Add `log_event()` in `update_hafiz_item_for_srs()` when interval > 99 → `recovered`
- **Verify**: FC page with bad rating → page journey shows `slipped` event

---

### Slice 9: Log events for manual mode changes
When user changes mode via profile UI, log events.
- [ ] Add `log_event()` in `quick_change_mode()` → determine event type
- [ ] Add `log_event()` in `graduate_item()` → `advanced` or `graduated`
- [ ] Add `log_event()` in `configure_reps()` when mode changes
- **Verify**: Change mode via dropdown → page journey shows event

---

### Slice 10: "Start Learning" action
Button to start learning not-memorized pages.
- [ ] Create `/profile/bulk/start_learning` route
- [ ] Set mode_code = NM, memorized = false, log `started_new` event
- [ ] Add "🌱 Start Learning" button to bulk actions bar
- [ ] Show button only when not-memorized pages selected
- **Verify**: Select not-memorized pages → click Start Learning → status=Learning

---

### Slice 11: "Complete" action for learning pages
Button to complete learning and enter Reps.
- [ ] Create `/profile/complete_learning/{item_id}` route
- [ ] Set mode_code = DR, memorized = true, log `completed` event
- [ ] Show "✓ Complete" button in row for NM pages
- **Verify**: Page in Learning → click Complete → status=Reps (DR)

---

### Slice 12: "Renew" action
Button to re-learn struggling/solid pages.
- [ ] Create `/profile/bulk/renew` route
- [ ] Set mode_code = NM, log `started_renew` event
- [ ] Add "🔄 Renew" button to bulk actions bar
- [ ] Show button only when SR/FC pages selected
- **Verify**: Select struggling page → click Renew → status=Learning

---

### Slice 13: "Reset" action
Button to reset page directly to Daily Reps (skip learning).
- [ ] Create `/profile/bulk/reset` route
- [ ] Set mode_code = DR, log `reset` event
- [ ] Add "⚡ Reset" button to bulk actions bar
- [ ] Show button only when SR/FC pages selected
- **Verify**: Select struggling page → click Reset → status=Reps (DR)

---

### Slice 14: Learning section enhancements
Show NEW vs RENEW type in learning view.
- [ ] Add "Type" column showing NEW or RENEW (based on last event)
- [ ] Add "Started" column with event date
- [ ] Query last `started_*` event for each NM item
- **Verify**: Renew a page → filter Learning → shows "RENEW" type with date

---

### Slice 15: Quick filters
Predefined filters for common queries.
- [ ] Add "😰 Struggling" quick filter (mode=SR OR bad_streak > 2)
- [ ] Add "📈 Almost Done" quick filter (rep count >= 6)
- [ ] Add "⏰ Overdue" quick filter (next_review < current_date)
- [ ] Add "Clear" button to reset all filters
- **Verify**: Click "Struggling" → shows SR pages + pages with bad streaks

---

### Slice 16: Search box
Quick search by page number.
- [ ] Add search input to filter bar
- [ ] Filter table as user types (client-side or HTMX)
- **Verify**: Type "45" → only page 45 shown

---

### Slice 17: Unify views (remove juz/surah/page tabs)
Single table with filters instead of separate views.
- [ ] Remove tab navigation (by juz/surah/page)
- [ ] Add juz and surah filter dropdowns instead
- [ ] Default to showing all pages, sorted by page number
- **Verify**: Profile shows single filterable table, juz/surah as filters

---

### Slice 18: Navigation cleanup
Update nav links and deprecate old routes.
- [ ] Update "Profile" nav link to `/profile/page`
- [ ] Redirect `/new_memorization` to `/profile/page?status=not_memorized`
- [ ] Remove deprecated juz/surah view code
- **Verify**: All navigation works, old URLs redirect

---

## Future Improvements

### Testing Infrastructure
- [ ] Implement module-scoped database fixtures for integration tests (per `docs/testing-approach.md` lines 596-643)
  - Current: Simple session-scoped `test_user` with manual cleanup
  - Recommended: Module-scoped DB creation + function-scoped table truncation
  - Benefit: ~10ms per test (vs current approach), guaranteed test isolation
  - When: Add when integration test count exceeds 10+ tests per module
