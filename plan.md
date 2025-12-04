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
