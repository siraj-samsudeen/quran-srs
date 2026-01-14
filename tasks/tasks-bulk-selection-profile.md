## Relevant Files

- `app/profile_view.py` - Main profile table rendering, needs Juz/Surah grouping and tab filter
- `app/profile_controller.py` - Routes for profile page, bulk operations
- `app/profile_model.py` - Database queries, needs ordering by juz_number
- `app/components/tables.py` - SurahHeader component, add JuzHeader component
- `app/components/forms.py` - BulkSelectCheckbox, SelectAllCheckbox components
- `app/components/layout.py` - StatsCards to be replaced with TabFilter
- `tests/test_profile_bulk_selection.py` - Tests for bulk selection with Juz/Surah grouping

### Notes

- Unit tests should be placed in `tests/` directory
- Use `uv run pytest` to run tests
- Use `uv run main.py` to run the app for browser verification
- Use `mailsiraj@gmail.com` for testing in browser, select hafiz "Siraj"

## Instructions for Completing Tasks

**IMPORTANT:** As you complete each task, you must check it off in this markdown file by changing `- [ ]` to `- [x]`. This helps track progress and ensures you don't skip any steps.

Example:
- `- [ ] 1.1 Read file` → `- [x] 1.1 Read file` (after completing)

Update the file after completing each sub-task, not just after completing an entire parent task.

## Tasks

- [x] 0.0 Create feature branch
  - [x] 0.1 Create and checkout a new branch `git checkout -b feature/bulk-selection-juz-surah`

- [x] 1.0 Baseline - verify existing bulk action works and write tests
  - [x] 1.1 Read existing bulk select implementation in `profile_view.py` (render_bulk_action_bar, BulkSelectCheckbox, SelectAllCheckbox)
  - [x] 1.2 Read existing bulk action handler in `profile_controller.py` (bulk_set_status)
  - [x] 1.3 Manually test current flow in browser: select pages → Mark Memorized → verify toast and table update
  - [x] 1.4 Create `tests/test_profile_bulk_selection.py` with tests for:
    - [x] 1.4.1 Test bulk_set_status marks selected items as memorized
    - [x] 1.4.2 Test bulk_set_status marks selected items as not memorized
    - [x] 1.4.3 Test bulk_set_status with empty selection shows error
  - [x] 1.5 Run tests with `uv run pytest tests/test_profile_bulk_selection.py` - all should pass

- [ ] 2.0 Add tab filter (All/Memorized/Unmemorized)
  - [ ] 2.1 Read `app/components/layout.py` to understand StatsCards component
  - [ ] 2.2 Create `TabFilter` component in `app/components/layout.py` with:
    - [ ] 2.2.1 Three tabs: All, Memorized, Unmemorized
    - [ ] 2.2.2 Each tab shows page count in parentheses (e.g., "All (604)")
    - [ ] 2.2.3 Active tab visually highlighted
    - [ ] 2.2.4 Tabs link to `/profile/table?status_filter=all|memorized|unmemorized`
  - [ ] 2.3 Update `profile_model.py` to add helper for tab counts:
    - [ ] 2.3.1 Add `get_tab_counts(hafiz_id)` returning {all: X, memorized: Y, unmemorized: Z} as page counts
  - [ ] 2.4 Update `profile_view.py`:
    - [ ] 2.4.1 Replace `render_stats_cards()` call with `TabFilter` component
    - [ ] 2.4.2 Pass tab counts to TabFilter
  - [ ] 2.5 Update `profile_controller.py`:
    - [ ] 2.5.1 Map status_filter values: `all` → None, `memorized` → memorized=1, `unmemorized` → memorized=0
  - [ ] 2.6 Run typecheck (if available) to verify no type errors
  - [ ] 2.7 Verify in browser: tabs display, counts correct, clicking tab filters table
  - [ ] 2.8 Add tests to `tests/test_profile_bulk_selection.py`:
    - [ ] 2.8.1 Test tab counts calculation
    - [ ] 2.8.2 Test filtering by memorized status
  - [ ] 2.9 Run tests - all should pass

- [ ] 3.0 Add Juz grouping with header checkbox
  - [ ] 3.1 Update `profile_model.py` `get_profile_data()`:
    - [ ] 3.1.1 Change ORDER BY to `juz_number ASC, page_number ASC`
  - [ ] 3.2 Create `JuzHeader` component in `app/components/tables.py`:
    - [ ] 3.2.1 Display "📖 Juz X" with bold text, light background
    - [ ] 3.2.2 Include checkbox with `data-juz="X"` attribute
    - [ ] 3.2.3 Checkbox has class `juz-checkbox` for JS targeting
  - [ ] 3.3 Update `render_profile_table()` in `profile_view.py`:
    - [ ] 3.3.1 Track current_juz_number, insert JuzHeader when juz changes
    - [ ] 3.3.2 Add `data-juz="X"` attribute to each page row
    - [ ] 3.3.3 Hide empty Juz sections (skip JuzHeader if no rows for that Juz in current filter)
  - [ ] 3.4 Add Alpine.js handler for Juz checkbox click:
    - [ ] 3.4.1 On click, select/deselect all `.bulk-select-checkbox[data-juz="X"]` checkboxes
    - [ ] 3.4.2 Update count in bulk action bar
  - [ ] 3.5 Run typecheck to verify no errors
  - [ ] 3.6 Verify in browser:
    - [ ] 3.6.1 Juz headers appear in order
    - [ ] 3.6.2 Clicking Juz checkbox selects all pages in that Juz
    - [ ] 3.6.3 Filtered view only shows Juz with matching pages
  - [ ] 3.7 Add tests to `tests/test_profile_bulk_selection.py`:
    - [ ] 3.7.1 Test data ordering by juz_number
    - [ ] 3.7.2 Test JuzHeader component renders correctly
  - [ ] 3.8 Run tests - all should pass

- [ ] 4.0 Add Surah grouping within Juz with header checkbox
  - [ ] 4.1 Update `SurahHeader` component in `app/components/tables.py`:
    - [ ] 4.1.1 Add checkbox with `data-juz="X" data-surah="Y"` attributes
    - [ ] 4.1.2 Checkbox has class `surah-checkbox` for JS targeting
    - [ ] 4.1.3 Change icon to "📗" to differentiate from Juz header
  - [ ] 4.2 Update `render_profile_table()` in `profile_view.py`:
    - [ ] 4.2.1 Track both current_juz_number and current_surah_id
    - [ ] 4.2.2 Insert SurahHeader when surah changes within a Juz
    - [ ] 4.2.3 If Surah spans multiple Juz, show separate SurahHeader in each Juz
    - [ ] 4.2.4 Add `data-juz="X" data-surah="Y"` attributes to each page row
    - [ ] 4.2.5 Hide empty Surah sections in filtered view
  - [ ] 4.3 Add Alpine.js handler for Surah checkbox click:
    - [ ] 4.3.1 On click, select/deselect all `.bulk-select-checkbox[data-juz="X"][data-surah="Y"]` checkboxes
    - [ ] 4.3.2 Update count in bulk action bar
  - [ ] 4.4 Run typecheck to verify no errors
  - [ ] 4.5 Verify in browser:
    - [ ] 4.5.1 Surah headers appear within each Juz section
    - [ ] 4.5.2 Clicking Surah checkbox selects only pages in that Surah within current Juz
    - [ ] 4.5.3 Al-Baqarah shows separate headers in Juz 1, 2, and 3
  - [ ] 4.6 Add tests to `tests/test_profile_bulk_selection.py`:
    - [ ] 4.6.1 Test SurahHeader with checkbox renders correctly
    - [ ] 4.6.2 Test Surah spanning multiple Juz shows multiple headers
  - [ ] 4.7 Run tests - all should pass

- [ ] 5.0 Implement checkbox state synchronization and update Select All
  - [ ] 5.1 Add Alpine.js logic for Juz checkbox state:
    - [ ] 5.1.1 Checked: all pages in Juz are selected
    - [ ] 5.1.2 Indeterminate: some pages in Juz are selected
    - [ ] 5.1.3 Unchecked: no pages in Juz are selected
  - [ ] 5.2 Add Alpine.js logic for Surah checkbox state:
    - [ ] 5.2.1 Same checked/indeterminate/unchecked logic as Juz
  - [ ] 5.3 Update individual page checkbox `@change` handler:
    - [ ] 5.3.1 Trigger recalculation of parent Surah checkbox state
    - [ ] 5.3.2 Trigger recalculation of parent Juz checkbox state
  - [ ] 5.4 Update SelectAllCheckbox in bulk action bar:
    - [ ] 5.4.1 Select All selects all visible pages across all Juz/Surah
    - [ ] 5.4.2 All Juz and Surah checkboxes update to checked
    - [ ] 5.4.3 Clear All deselects everything and updates all header checkboxes
  - [ ] 5.5 Run typecheck to verify no errors
  - [ ] 5.6 Verify in browser:
    - [ ] 5.6.1 Select one page → Surah and Juz checkboxes show indeterminate
    - [ ] 5.6.2 Select all pages in Surah → Surah checkbox checked, Juz may be indeterminate
    - [ ] 5.6.3 Select all pages in Juz → Juz checkbox checked
    - [ ] 5.6.4 Select All → all checkboxes checked
    - [ ] 5.6.5 Clear All → all checkboxes unchecked
  - [ ] 5.7 Add tests to `tests/test_profile_bulk_selection.py`:
    - [ ] 5.7.1 Test checkbox state calculation logic
  - [ ] 5.8 Run all tests - all should pass
  - [ ] 5.9 Final browser verification of complete flow
