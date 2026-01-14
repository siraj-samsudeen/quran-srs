# PRD: Mark Page as Memorized/Not Memorized

## Introduction

This feature allows users to mark Quran pages as memorized or not memorized from the Profile Table page (`/profile/table`). When a page is marked as memorized, it enters the revision system with status "Solid" and mode "Full Cycle" (FC). This is the primary way users initially set up their memorization profile.

**Status**: ✅ Fixed (was broken due to form not wrapping table checkboxes)

## Status ↔ Mode Relationship

Status is a *derived* label based on `memorized` boolean + `mode_code`:

| Status | Memorized | Mode Code | Description |
|--------|-----------|-----------|-------------|
| Not Memorized | `false` | `null` | Page not yet memorized |
| Learning | `true` | `NM` | Actively memorizing new pages |
| Reps | `true` | `DR/WR/FR/MR` | Fixed repetition modes |
| Solid | `true` | `FC` | Full Cycle - strong memorization |
| Struggling | `true` | `SR` | SRS mode - needs recovery |

## Current Implementation

### UI Flow
1. User navigates to `/profile/table`
2. Stats cards show page counts by status (clickable filters)
3. Table shows all pages with Status, Mode, and Progress columns
4. User selects pages via checkboxes
5. Bulk Action Bar appears at bottom with:
   - "✓ Mark Memorized" button → sets to SOLID (FC mode)
   - "✗ Mark Not Memorized" button → clears memorized status

### Key Files
- Controller: `app/profile_controller.py` - `bulk_set_status()` route
- View: `app/profile_view.py` - `render_bulk_action_bar()`, `render_profile_table()`
- Model: `app/profile_model.py` - `apply_status_to_item()`, `get_status()`
- Constants: `constants.py` - Status and mode constants

### Current Behavior
When "Mark Memorized" is clicked:
- `memorized = True`
- `mode_code = "FC"` (Full Cycle)
- `next_review = None` (FC doesn't use scheduled reviews)
- `next_interval = None`

## Goals

- [x] Allow users to mark pages as memorized (status = Solid, mode = FC)
- [x] Allow users to unmark pages (status = Not Memorized)
- [x] Support bulk operations for multiple pages
- [x] Filter pages by status using stats cards
- [x] Show current status and mode in table view

## User Stories

### US-001: Bulk Mark Pages as Memorized ✅
**Description:** As a hafiz, I want to select multiple pages and mark them as memorized so I can quickly set up my profile.

**Acceptance Criteria:**
- [x] Checkboxes appear in each row for selection
- [x] Bulk action bar appears when pages are selected
- [x] "Mark Memorized" button sets selected pages to Solid/FC status
- [x] Success toast shows count of updated pages
- [x] Table refreshes to show updated status

### US-002: Bulk Mark Pages as Not Memorized ✅
**Description:** As a hafiz, I want to unmark pages I incorrectly marked as memorized.

**Acceptance Criteria:**
- [x] "Mark Not Memorized" button clears memorized status
- [x] Mode and status reset to null/Not Memorized
- [x] Pages removed from revision system

### US-003: Filter Pages by Status ✅
**Description:** As a hafiz, I want to filter the table by status to find specific pages.

**Acceptance Criteria:**
- [x] Stats cards are clickable and filter table
- [x] "Not Memorized" filter shows only unmarked pages
- [x] Active filter is visually indicated
- [x] Bulk actions work within filtered view

### US-004: Select All/Clear All ✅
**Description:** As a hafiz, I want to quickly select or clear all visible pages.

**Acceptance Criteria:**
- [x] Select All checkbox in header and bulk bar
- [x] Toggle behavior between Select All / Clear All
- [x] Counter shows number of selected items

## Functional Requirements

- FR-1: ✅ `POST /profile/bulk/set_status` accepts status and list of hafiz_item_ids
- FR-2: ✅ `apply_status_to_item()` maps status to memorized flag + mode_code
- FR-3: ✅ Stats cards show page counts by status
- FR-4: ✅ Table supports infinite scroll pagination
- FR-5: ✅ Bulk action bar is sticky at bottom of screen

## Non-Goals

- Inline single-click toggle per row (use checkbox + bulk action instead)
- Setting status to Learning/Reps/Struggling directly (only Memorized/Not Memorized)
- Setting mode directly from bulk actions (use config modal for that)

## Technical Considerations

- Uses HTMX for table refresh after bulk operations
- Alpine.js for checkbox state management and counter
- `hafizs_items` table stores `memorized` boolean and `mode_code`
- Status is derived at query time, not stored

## Success Metrics

- Users can mark 100+ pages in under 10 seconds using Select All
- No page reload required after bulk operations
- Clear visual feedback on success/failure

## Open Questions

None - feature is complete and working.
