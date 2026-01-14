# PRD: Bulk Selection with Juz/Surah Grouping on Profile Page

## Introduction

Enhance the Profile Table page (`/profile/table`) to support efficient bulk selection of pages organized by Juz and Surah. Users can filter by memorization status using tabs, then select entire Juz sections or Surah groups with a single click to mark pages as memorized or unmemorized.

## Goals

- Replace stats cards with simpler All/Memorized/Unmemorized tabs
- Reorganize table to group pages by Juz first, then Surah within each Juz
- Add checkbox to Juz headers to select all visible pages in that Juz
- Add checkbox to Surah headers to select all visible pages in that Surah (within current Juz)
- Maintain existing bulk action bar functionality

## User Stories

### US-001: Filter by Tab
**Description:** As a user, I want to filter pages by memorization status using tabs, so I can focus on specific pages when bulk selecting.

**Acceptance Criteria:**
- [ ] Three tabs appear at top: "All", "Memorized", "Unmemorized"
- [ ] Each tab shows count in parentheses, e.g., "All (604)"
- [ ] Clicking a tab filters the table to show only matching pages
- [ ] Active tab is visually highlighted
- [ ] Default tab is "All"
- [ ] Stats cards are removed (replaced by tabs)
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

### US-002: Juz Grouping with Headers
**Description:** As a user, I want to see pages organized by Juz, so I can easily navigate and find specific sections.

**Acceptance Criteria:**
- [ ] Table is grouped by Juz number (1-30)
- [ ] Each Juz has a header row showing "📖 Juz X"
- [ ] Juz header spans full table width with distinct styling
- [ ] Surahs are nested within their Juz sections
- [ ] Pages are ordered by page number within each section
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

### US-003: Juz Header Checkbox
**Description:** As a user, I want to select all pages in a Juz with one click, so I can quickly bulk-select an entire Juz.

**Acceptance Criteria:**
- [ ] Checkbox appears in Juz header row
- [ ] Clicking checkbox selects all visible page rows in that Juz
- [ ] Clicking again deselects all pages in that Juz
- [ ] Selected count updates in bulk action bar
- [ ] Only selects pages visible in current tab filter
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

### US-004: Surah Header with Checkbox
**Description:** As a user, I want to select all pages of a Surah within a Juz, so I can quickly select Surah portions.

**Acceptance Criteria:**
- [ ] Surah header row appears for each Surah within a Juz
- [ ] Header shows "📗 Surah Name"
- [ ] Checkbox appears in Surah header row
- [ ] Clicking checkbox selects all visible page rows for that Surah in current Juz only
- [ ] If a Surah spans multiple Juz, each Juz section has its own Surah header
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

### US-005: Checkbox State Synchronization
**Description:** As a user, I want header checkboxes to reflect selection state, so I can see what's selected at a glance.

**Acceptance Criteria:**
- [ ] Juz checkbox shows checked if ALL pages in that Juz are selected
- [ ] Juz checkbox shows indeterminate if SOME pages in that Juz are selected
- [ ] Juz checkbox shows unchecked if NO pages in that Juz are selected
- [ ] Same behavior applies to Surah header checkboxes
- [ ] Selecting/deselecting individual pages updates header checkbox states
- [ ] Typecheck passes

### US-006: Select All in Bulk Action Bar
**Description:** As a user, I want Select All to select all visible pages across all Juz/Surah sections.

**Acceptance Criteria:**
- [ ] "Select All" in bulk action bar selects all visible pages in current tab
- [ ] All Juz and Surah header checkboxes update to checked state
- [ ] "Clear All" deselects everything
- [ ] Selected count accurately reflects total selected
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

## Functional Requirements

- FR-1: Replace `StatsCards` component with `TabFilter` component showing All/Memorized/Unmemorized tabs
- FR-2: Tab counts derived from: All = total pages, Memorized = pages where memorized=true, Unmemorized = pages where memorized=false
- FR-3: Query `get_profile_data()` to return data ordered by juz_number, then page_number
- FR-4: Render Juz header row when juz_number changes, with checkbox having `data-juz="X"` attribute
- FR-5: Render Surah header row when surah_id changes within a Juz, with checkbox having `data-juz="X" data-surah="Y"` attributes
- FR-6: Page row checkboxes include `data-juz="X" data-surah="Y"` attributes for JavaScript selection logic
- FR-7: Alpine.js handles checkbox state synchronization between headers and page rows
- FR-8: Juz/Surah header checkbox click uses JavaScript to select/deselect child page checkboxes
- FR-9: Individual page checkbox changes trigger header checkbox state recalculation
- FR-10: Tab filter uses `?tab=all|memorized|unmemorized` query parameter (or reuse existing `status_filter`)

## Non-Goals

- Collapsible Juz/Surah sections (all sections always expanded)
- Keyboard navigation between sections
- Remembering tab selection across page reloads
- Drag-and-drop selection
- Inline editing of page status (use bulk action bar only)

## Design Considerations

### Visual Mockup

```
┌─────────────────────────────────────────────────────────────────────┐
│ [All (604)] [Memorized (120)] [Unmemorized (484)]                   │
├─────────────────────────────────────────────────────────────────────┤
│ [☐]  Page  Status      Mode    Progress  Config                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ [☐] 📖 Juz 1                                                        │
│                                                                     │
│ [☐] 📗 Al-Fatiha                                                    │
│ [☐]  1     ❌ Not Mem  -       -         -                          │
│                                                                     │
│ [☐] 📗 Al-Baqarah                                                   │
│ [☐]  2     ❌ Not Mem  -       -         -                          │
│ [☐]  3     ❌ Not Mem  -       -         -                          │
│ ... (pages 4-21)                                                    │
│                                                                     │
│ [☐] 📖 Juz 2                                                        │
│                                                                     │
│ [☐] 📗 Al-Baqarah                                                   │
│ [☐]  22    ❌ Not Mem  -       -         -                          │
│ ... (pages 22-41)                                                   │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ [Select All] │ 0 selected │ ✓ Mark Memorized │ ✗ Mark Not Mem  │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Styling

- Juz header: Bold text, light background (e.g., `bg-base-200`), full-width row
- Surah header: Slightly indented or lighter styling than Juz header
- Active tab: Primary color background or border-bottom indicator
- Header checkboxes: Same size as page checkboxes for alignment

## Technical Considerations

- Reuse existing `BulkSelectCheckbox` and `SelectAllCheckbox` components
- Add new `JuzHeader` and modify existing `SurahHeader` components to include checkboxes
- Alpine.js `x-data` scope needs to track selection state per Juz/Surah for efficient updates
- Consider using CSS classes like `.juz-1-checkbox`, `.surah-1-juz-1-checkbox` for JavaScript selection
- Tab filtering can reuse existing `status_filter` logic with simplified values: `all`, `memorized`, `unmemorized`
- Infinite scroll pagination should maintain Juz/Surah grouping across page loads

### Data Attributes Strategy

```html
<!-- Juz header -->
<tr class="juz-header" data-juz="1">
  <td><input type="checkbox" class="juz-checkbox" data-juz="1"></td>
  <td colspan="5">📖 Juz 1</td>
</tr>

<!-- Surah header within Juz -->
<tr class="surah-header" data-juz="1" data-surah="2">
  <td><input type="checkbox" class="surah-checkbox" data-juz="1" data-surah="2"></td>
  <td colspan="5">📗 Al-Baqarah</td>
</tr>

<!-- Page row -->
<tr data-juz="1" data-surah="2">
  <td><input type="checkbox" class="bulk-select-checkbox" data-juz="1" data-surah="2" name="hafiz_item_ids" value="123"></td>
  <td>2</td>
  ...
</tr>
```

## Success Metrics

- User can select all 20 pages in a Juz with 1 click
- User can select all Surah pages within a Juz with 1 click  
- Tab switching filters table in under 200ms
- Bulk marking 100+ pages completes in under 2 seconds
- No page reload required for any operation

## Design Decisions

1. **Hide empty sections when filtering:** Yes - if Juz 1 has no unmemorized pages, hide it in the Unmemorized tab
2. **Page counts in headers:** Skip for MVP - no "(20 pages)" suffix in headers
3. **Display in pages, not items:**
   - Tab counts show pages: "All (604)"
   - Table rows show page number with part indicator if split: "50" or "50 (1/4)"
   - Bulk action bar shows pages: "4.5 pages selected"
   - Success toast shows pages: "Marked 20 pages as memorized"
   - Internally, rows are items and selection works on hafiz_item_ids

## Open Questions

None - ready for implementation.
