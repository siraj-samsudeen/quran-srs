# Component Library Implementation Plan

## Overview

This plan addresses Section 3B from code-review-feedback.md: **Create a Component Library**. The goal is to extract reusable UI components that are currently scattered or duplicated across multiple modules into a dedicated `components/` directory.

## Current State Analysis

### Identified Duplication Patterns

| Component Pattern | Locations | Lines Duplicated |
|-------------------|-----------|------------------|
| `all_mode_options` list | `common_function.py` (×2), `render_mode_dropdown`, `render_graduate_cell` | ~20 lines |
| Bulk action bar structure | `home_view.py`, `new_memorization.py`, `profile.py` | ~60 lines each |
| Select-all checkbox Alpine.js | `home_view.py`, `new_memorization.py`, `profile.py` | ~15 lines each |
| Rating dropdown | `common_function.py` (used by 5+ modules) | Single source, but tightly coupled |
| Tap-to-reveal pattern | `home_view.py` (render_start_text_cell) | ~8 lines |
| Surah header row | `home_view.py`, `new_memorization.py`, `profile.py` | ~10 lines each |
| Page number cell with part indicator | `home_view.py` | Single source, could be more generic |
| Stats cards | `profile.py` | Single source, could be reused elsewhere |

### Alpine.js Patterns

The codebase uses Alpine.js extensively for:
1. **Bulk selection counter**: `x_data="{ count: 0 }"` with checkbox tracking
2. **Select-all toggle**: Complex `@change` handlers
3. **Tap-to-reveal**: `x_data="{ revealed: false }"`
4. **Tab state**: `x_data="{ activeTab: '...' }"`

These patterns are repeated with slight variations.

---

## Proposed Directory Structure

```
app/
├── components/
│   ├── __init__.py          # Re-exports all components
│   ├── forms.py             # Form inputs: rating_dropdown, mode_select, etc.
│   ├── tables.py            # Table helpers: surah_header, page_cell, etc.
│   ├── bulk_actions.py      # Bulk action bars and select-all logic
│   └── alpine.py            # Alpine.js x-data pattern generators
```

---

## Component Specifications

### 1. `components/forms.py` - Form Components

#### A. `mode_select()` - Unified Mode Dropdown
**Current Problem**: `all_mode_options` duplicated 3× with same list.

```python
# Proposed API
def mode_select(
    current_mode: str = None,
    exclude_modes: list[str] = None,  # e.g., exclude current mode for "graduate to"
    name: str = "mode_code",
    size: str = "xs",  # xs, sm, md
    **kwargs,  # hx_post, hx_trigger, etc.
) -> Select
```

**Consolidates**:
- `render_mode_dropdown()` in `common_function.py`
- `graduate_select` in `render_graduate_cell()`
- Mode selector in `render_mode_config_form()`

#### B. `rating_dropdown()` - Keep but move
**Current Location**: `common_function.py` lines 293-316
**Action**: Move to `components/forms.py`, keep same API.

#### C. `rating_radio()` - Keep but move
**Current Location**: `common_function.py` lines 319-351
**Action**: Move to `components/forms.py`.

---

### 2. `components/tables.py` - Table Components

#### A. `surah_header()` - Section Header Row
**Current Problem**: Similar implementations in 3 files.

```python
# Proposed API
def surah_header(
    surah_id: int,
    juz_number: int,
    colspan: int = 4,
    extra_content: Any = None,  # Optional additional content
) -> Tr
```

**Consolidates**:
- `render_surah_header()` in `home_view.py`
- `_render_profile_surah_header()` in `profile.py`
- Inline surah header in `new_memorization.py`

#### B. `page_number_cell()` - Page Display Cell
**Current Location**: `render_page_number_cell()` in `home_view.py`
**Action**: Move to `components/tables.py`, generalize.

```python
def page_number_cell(
    item_id: int,
    show_part_indicator: bool = True,
    link_target: str = None,  # Override default link
) -> Td
```

#### C. `start_text_cell()` - Tap-to-Reveal Cell
**Current Location**: `render_start_text_cell()` in `home_view.py`

```python
def start_text_cell(
    text: str,
    hide_text: bool = False,  # Enable tap-to-reveal
    reveal_style: str = "dots",  # "dots" or "blur"
) -> Td
```

#### D. `bulk_checkbox()` - Selection Checkbox Cell
**Current Location**: `render_bulk_checkbox()` in `home_view.py`

```python
def bulk_checkbox(
    item_id: int,
    name: str = "item_ids",
    checked: bool = False,
    cls: str = "bulk-select-checkbox",  # For Alpine.js targeting
) -> Td
```

---

### 3. `components/bulk_actions.py` - Bulk Action Components

#### A. `select_all_controls()` - Select-All UI Block
**Current Problem**: Nearly identical 15-line Alpine.js patterns in 3 files.

```python
def select_all_controls(
    checkbox_class: str = "bulk-select-checkbox",
    show_count: bool = True,
) -> Div
```

Returns the standard:
- Select-all checkbox
- "Select All" / "Clear All" labels
- Count display (`Span(x_text="count")`)

#### B. `bulk_action_bar()` - Generic Bulk Bar Container
**Current Problem**: 3 similar implementations with different buttons.

```python
def bulk_action_bar(
    bar_id: str,
    actions: list[Any],  # List of action buttons
    checkbox_class: str = "bulk-select-checkbox",
) -> Div
```

**Consolidates**:
- `render_bulk_action_bar()` in `home_view.py` (Good/Ok/Bad buttons)
- `render_nm_bulk_action_bar()` in `new_memorization.py` (Mark Memorized)
- `_render_bulk_action_bar()` in `profile.py` (Set Status)

Each caller provides their specific action buttons; the bar handles:
- Fixed positioning
- Select-all controls
- x-show/x-transition
- Cancel button

#### C. `rating_buttons()` - Rating Action Buttons
**For home page bulk actions**:

```python
def rating_buttons(
    mode_code: str,
    current_date: str,
    plan_id: int = None,
) -> list[Button]
```

---

### 4. `components/alpine.py` - Alpine.js Helpers

#### A. `bulk_select_x_data()` - Bulk Selection State
**Current Problem**: `x_data="{ count: 0 }"` repeated, plus complex `@change` handlers duplicated.

```python
def bulk_select_x_data() -> str:
    """Returns Alpine.js x-data for bulk selection with count tracking."""
    return "{ count: 0 }"

def select_all_checkbox_handler(checkbox_class: str = "bulk-select-checkbox") -> dict:
    """Returns Alpine.js attributes for a select-all checkbox."""
    return {
        "@change": f"""
            $root.querySelectorAll('.{checkbox_class}').forEach(cb => cb.checked = $el.checked);
            count = $el.checked ? $root.querySelectorAll('.{checkbox_class}').length : 0
        """,
        ":checked": f"count > 0 && count === $root.querySelectorAll('.{checkbox_class}').length",
    }
```

#### B. `tap_to_reveal_x_data()` - Tap-to-Reveal State
```python
def tap_to_reveal_x_data() -> str:
    return "{ revealed: false }"
```

#### C. Migrate `select_all_checkbox_x_data()` from `utils.py`
The existing complex function in `utils.py` should move here.

---

## Constants Additions

Add to `constants.py`:

```python
# Mode display configuration (icon, short label, full label)
MODE_DISPLAY = {
    NEW_MEMORIZATION_MODE_CODE: ("🆕", "NM", "New Memorization"),
    DAILY_REPS_MODE_CODE: ("☀️", "Daily", "Daily Reps"),
    WEEKLY_REPS_MODE_CODE: ("📅", "Weekly", "Weekly Reps"),
    FORTNIGHTLY_REPS_MODE_CODE: ("📆", "Fortnightly", "Fortnightly Reps"),
    MONTHLY_REPS_MODE_CODE: ("🗓️", "Monthly", "Monthly Reps"),
    FULL_CYCLE_MODE_CODE: ("🔄", "Full Cycle", "Full Cycle"),
    SRS_MODE_CODE: ("🧠", "SRS", "Spaced Repetition"),
}

# Standard mode selection options (for dropdowns)
ALL_MODE_OPTIONS = [
    (DAILY_REPS_MODE_CODE, "☀️ Daily"),
    (WEEKLY_REPS_MODE_CODE, "📅 Weekly"),
    (FORTNIGHTLY_REPS_MODE_CODE, "📆 Fortnightly"),
    (MONTHLY_REPS_MODE_CODE, "🗓️ Monthly"),
    (FULL_CYCLE_MODE_CODE, "🔄 Full Cycle"),
    (SRS_MODE_CODE, "🧠 SRS"),
]
```

---

## Implementation Order

### Phase 1: Foundation (Low Risk)
1. Create `components/` directory structure
2. Add `ALL_MODE_OPTIONS` and `MODE_DISPLAY` to `constants.py`
3. Create `components/alpine.py` with Alpine helpers
4. Create `components/forms.py`:
   - Move `rating_dropdown()` from `common_function.py`
   - Move `rating_radio()` from `common_function.py`
   - Create `mode_select()` consolidating duplicated code

### Phase 2: Table Components (Medium Risk)
5. Create `components/tables.py`:
   - Move `render_page_number_cell()` → `page_number_cell()`
   - Move `render_start_text_cell()` → `start_text_cell()`
   - Move `render_bulk_checkbox()` → `bulk_checkbox()`
   - Create unified `surah_header()`
6. Update `home_view.py` to import from components
7. Update `new_memorization.py` to import from components
8. Update `profile.py` to import from components

### Phase 3: Bulk Actions (Higher Risk)
9. Create `components/bulk_actions.py`:
   - Create `select_all_controls()`
   - Create `bulk_action_bar()` generic container
   - Create `rating_buttons()` for home page
10. Refactor `render_bulk_action_bar()` in `home_view.py`
11. Refactor `render_nm_bulk_action_bar()` in `new_memorization.py`
12. Refactor `_render_bulk_action_bar()` in `profile.py`

### Phase 4: Cleanup
13. Update `common_function.py` to re-export from components for backward compatibility
14. Remove duplicated code
15. Move `select_all_checkbox_x_data()` from `utils.py` to `components/alpine.py`
16. Update imports across the codebase

---

## Expected Benefits

| Metric | Before | After |
|--------|--------|-------|
| `all_mode_options` definitions | 3 | 1 |
| Bulk action bar implementations | 3 | 1 (+ 3 thin wrappers) |
| Select-all Alpine patterns | 3 | 1 |
| Lines in `common_function.py` | ~775 | ~650 |
| Component discoverability | Poor (scattered) | Good (centralized) |

---

## Testing Strategy

1. **Visual regression**: Run E2E tests after each phase
2. **Component isolation**: Each component can be tested independently
3. **No new unit tests required**: Existing E2E tests cover functionality

---

## Rollback Plan

If issues arise:
1. `common_function.py` maintains re-exports for backward compatibility
2. Each phase is independently revertible
3. Git commits per phase allow easy rollback

---

## Next Steps

1. Review this plan
2. Approve or suggest modifications
3. Begin Phase 1 implementation
