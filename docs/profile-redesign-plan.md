# Profile Redesign & Events System - Implementation Plan

## Overview

A comprehensive redesign of the profile/memorization management system with:
1. **Events table** - Audit trail of all page transitions
2. **Unified status model** - Clear, derived statuses from mode_code
3. **Dashboard-first profile** - Stats, filters, bulk actions
4. **Integrated learning flow** - NEW and RENEW in same staging area

---

## Status Model (Derived from mode_code)

```
Status          Mode Code    Description
─────────────────────────────────────────────────────────────
📚 NOT_MEMORIZED  (any)      memorized = false
🌱 LEARNING       NM         Currently learning (NEW or RENEW)
🏋️ REPS           DR/WR/FR/MR Fixed interval training
💪 SOLID          FC         Confident, in rotation
😰 STRUGGLING     SR         Needs focused attention
```

No new column needed - status is computed from `memorized` + `mode_code`.

---

## Event Types

| Event | Description | From → To |
|-------|-------------|-----------|
| `started_new` | First time learning | NULL/FC → NM |
| `started_renew` | Re-learning | SR/FC → NM |
| `completed` | Finished learning | NM → DR |
| `advanced` | Moved up in reps | DR→WR, WR→FR, FR→MR |
| `graduated` | Completed all reps | MR → FC |
| `slipped` | Entered struggling | FC → SR |
| `recovered` | Exited struggling naturally | SR → FC |
| `reset` | User reset to reps | SR/FC → DR |

---

## Phase 1: Events Table Foundation

### 1.1 Create Migration

**File**: `migrations/0025-create-page-events.sql`

```sql
-- Page events table for tracking all status/mode transitions
CREATE TABLE page_events (
    id INTEGER PRIMARY KEY,
    hafiz_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    from_mode TEXT,
    to_mode TEXT,
    event_date TEXT NOT NULL,
    triggered_by TEXT DEFAULT 'user',
    FOREIGN KEY (hafiz_id) REFERENCES hafizs(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id)
);

-- Index for querying events by hafiz and item
CREATE INDEX idx_page_events_hafiz_item ON page_events(hafiz_id, item_id);
CREATE INDEX idx_page_events_date ON page_events(hafiz_id, event_date);
```

### 1.2 Create Events Model

**File**: `app/events_model.py`

```python
from database import db, page_events
from dataclasses import dataclass

@dataclass
class PageEvent:
    id: int | None = None
    hafiz_id: int | None = None
    item_id: int | None = None
    event_type: str | None = None
    from_mode: str | None = None
    to_mode: str | None = None
    event_date: str | None = None
    triggered_by: str | None = None

# Event type constants
EVENT_STARTED_NEW = "started_new"
EVENT_STARTED_RENEW = "started_renew"
EVENT_COMPLETED = "completed"
EVENT_ADVANCED = "advanced"
EVENT_GRADUATED = "graduated"
EVENT_SLIPPED = "slipped"
EVENT_RECOVERED = "recovered"
EVENT_RESET = "reset"

def log_event(
    hafiz_id: int,
    item_id: int,
    event_type: str,
    from_mode: str | None,
    to_mode: str,
    event_date: str,
    triggered_by: str = "user"
):
    """Log a page event to the events table."""
    return page_events.insert(
        hafiz_id=hafiz_id,
        item_id=item_id,
        event_type=event_type,
        from_mode=from_mode,
        to_mode=to_mode,
        event_date=event_date,
        triggered_by=triggered_by,
    )

def get_page_history(hafiz_id: int, item_id: int):
    """Get all events for a specific page, ordered by date."""
    return page_events(
        where=f"hafiz_id = {hafiz_id} AND item_id = {item_id}",
        order_by="event_date ASC, id ASC"
    )

def get_recent_events(hafiz_id: int, limit: int = 50):
    """Get recent events for a hafiz."""
    return page_events(
        where=f"hafiz_id = {hafiz_id}",
        order_by="event_date DESC, id DESC",
        limit=limit
    )
```

### 1.3 Integrate Event Logging

Add event logging to existing mode transition points:

| File | Function | Event to Log |
|------|----------|--------------|
| `app/new_memorization.py` | `update_status_as_newly_memorized()` | `started_new` + `completed` |
| `app/fixed_reps.py` | `update_rep_item()` | `advanced` or `graduated` |
| `app/srs_reps.py` | `start_srs_for_ok_and_bad_rating()` | `slipped` |
| `app/srs_reps.py` | `update_hafiz_item_for_srs()` | `recovered` (when interval > 99) |
| `app/profile.py` | `quick_change_mode()` | appropriate event based on transition |
| `app/profile.py` | `graduate_item()` | `advanced` or `graduated` |

### 1.4 Tasks

- [ ] Create migration file `0025-create-page-events.sql`
- [ ] Add `page_events` table to `database.py`
- [ ] Create `app/events_model.py` with helper functions
- [ ] Add `log_event()` calls to `new_memorization.py`
- [ ] Add `log_event()` calls to `fixed_reps.py`
- [ ] Add `log_event()` calls to `srs_reps.py`
- [ ] Add `log_event()` calls to `profile.py` mode change routes
- [ ] Write tests for event logging

---

## Phase 2: Status Helper Functions

### 2.1 Add Status Derivation

**File**: `app/common_function.py` (additions)

```python
# Status constants
STATUS_NOT_MEMORIZED = "NOT_MEMORIZED"
STATUS_LEARNING = "LEARNING"
STATUS_REPS = "REPS"
STATUS_SOLID = "SOLID"
STATUS_STRUGGLING = "STRUGGLING"

STATUS_DISPLAY = {
    STATUS_NOT_MEMORIZED: ("📚", "Not Memorized"),
    STATUS_LEARNING: ("🌱", "Learning"),
    STATUS_REPS: ("🏋️", "Reps"),
    STATUS_SOLID: ("💪", "Solid"),
    STATUS_STRUGGLING: ("😰", "Struggling"),
}

def get_status(hafiz_item) -> str:
    """Derive status from memorized flag and mode_code."""
    if isinstance(hafiz_item, dict):
        memorized = hafiz_item.get("memorized")
        mode_code = hafiz_item.get("mode_code")
    else:
        memorized = hafiz_item.memorized
        mode_code = hafiz_item.mode_code

    if not memorized:
        return STATUS_NOT_MEMORIZED

    if mode_code == NEW_MEMORIZATION_MODE_CODE:
        return STATUS_LEARNING
    elif mode_code in (DAILY_REPS_MODE_CODE, WEEKLY_REPS_MODE_CODE,
                       FORTNIGHTLY_REPS_MODE_CODE, MONTHLY_REPS_MODE_CODE):
        return STATUS_REPS
    elif mode_code == FULL_CYCLE_MODE_CODE:
        return STATUS_SOLID
    elif mode_code == SRS_MODE_CODE:
        return STATUS_STRUGGLING

    return STATUS_NOT_MEMORIZED

def get_status_display(status: str) -> tuple[str, str]:
    """Get icon and label for a status."""
    return STATUS_DISPLAY.get(status, ("❓", "Unknown"))

def get_status_counts(hafiz_id: int) -> dict:
    """Get count of pages in each status for dashboard stats."""
    qry = f"""
        SELECT
            SUM(CASE WHEN memorized = 0 THEN 1 ELSE 0 END) as not_memorized,
            SUM(CASE WHEN memorized = 1 AND mode_code = 'NM' THEN 1 ELSE 0 END) as learning,
            SUM(CASE WHEN memorized = 1 AND mode_code IN ('DR', 'WR', 'FR', 'MR') THEN 1 ELSE 0 END) as reps,
            SUM(CASE WHEN memorized = 1 AND mode_code = 'FC' THEN 1 ELSE 0 END) as solid,
            SUM(CASE WHEN memorized = 1 AND mode_code = 'SR' THEN 1 ELSE 0 END) as struggling
        FROM hafizs_items
        WHERE hafiz_id = {hafiz_id}
    """
    result = db.q(qry)
    if result:
        return result[0]
    return {}

def get_mode_counts(hafiz_id: int) -> dict:
    """Get count of pages in each specific mode."""
    qry = f"""
        SELECT mode_code, COUNT(*) as count
        FROM hafizs_items
        WHERE hafiz_id = {hafiz_id} AND memorized = 1
        GROUP BY mode_code
    """
    results = db.q(qry)
    return {r["mode_code"]: r["count"] for r in results}
```

### 2.2 Tasks

- [ ] Add status constants to `common_function.py`
- [ ] Add `get_status()` function
- [ ] Add `get_status_display()` function
- [ ] Add `get_status_counts()` for dashboard stats
- [ ] Add `get_mode_counts()` for detailed breakdown
- [ ] Write tests for status derivation

---

## Phase 3: Profile Page Redesign

### 3.1 New Profile Structure

```
/profile                    → Redirects to /profile/dashboard
/profile/dashboard          → Main dashboard with stats + filters + table
/profile/page/{item_id}     → Individual page details (existing page_details)
```

### 3.2 Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 📊 MY MEMORIZATION                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│ STATS CARDS (clickable to filter)                                       │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│ │ 📚 120  │ │ 🌱 5    │ │ 🏋️ 35   │ │ 💪 428  │ │ 😰 16   │ │ 📖 604  ││
│ │ Not Mem │ │Learning │ │ Reps    │ │ Solid   │ │Struggling│ │ Total   ││
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│ FILTERS                                                                 │
│ [Status ▼] [Mode ▼] [Juz ▼] [Surah ▼] [🔍 Search...]                   │
│                                                                         │
│ Quick: [⚠️ Struggling] [📈 Almost Done] [⏰ Overdue] [Clear]            │
├─────────────────────────────────────────────────────────────────────────┤
│ BULK ACTIONS (shown when items selected)                                │
│ [☐ Select All] Selected: 5  [🌱 Start Learning] [🔄 Reset] [⚙️ Config] │
├─────────────────────────────────────────────────────────────────────────┤
│ TABLE                                                                   │
│ │ ☐ │ Page │ Surah       │ Juz │ Status     │ Mode    │ Progress │ Health│
│ ├───┼──────┼─────────────┼─────┼────────────┼─────────┼──────────┼───────┤
│ │ ☐ │ 13   │ Al-Baqarah  │ 1   │ 😰 Struggling│ 🧠 SRS │ -        │ ⚠️    │
│ │ ☐ │ 45   │ Al-Baqarah  │ 1   │ 🏋️ Reps     │ ☀️ Daily│ 5/7      │ 🔥    │
│ │ ☐ │ 89   │ An-Nisa     │ 5   │ 🌱 Learning │ 🆕 NM   │ -        │ -     │
├─────────────────────────────────────────────────────────────────────────┤
│ PAGINATION                                                              │
│ [← Prev] Page 1 of 25 (604 items) [Next →]                             │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Filter Options

**Status Filter:**
- All
- 📚 Not Memorized
- 🌱 Learning
- 🏋️ Reps
- 💪 Solid
- 😰 Struggling

**Mode Filter (when Status = Reps):**
- All Reps
- ☀️ Daily (DR)
- 📅 Weekly (WR)
- 📆 Fortnightly (FR)
- 🗓️ Monthly (MR)

**Quick Filters:**
- ⚠️ Struggling: `mode_code = 'SR' OR bad_streak > 2`
- 📈 Almost Done: `mode_code IN ('DR','WR','FR','MR') AND rep_count >= 6`
- ⏰ Overdue: `next_review < current_date`

### 3.4 Bulk Actions

| Action | Available When | Result |
|--------|----------------|--------|
| 🌱 Start Learning | Status = Not Memorized | Creates `started_new` event, mode → NM |
| ✅ Complete | Status = Learning | Creates `completed` event, mode → DR |
| 🔄 Renew | Status = Struggling/Solid | Creates `started_renew` event, mode → NM |
| ⚡ Reset | Status = Struggling/Solid | Creates `reset` event, mode → DR |
| ⚙️ Configure | Any memorized | Opens config modal (mode, thresholds) |

### 3.5 Health Column

Based on performance indicators:

```python
def get_health_indicator(hafiz_item) -> tuple[str, int]:
    """Returns (icon, score) for health display."""
    good_streak = hafiz_item.good_streak or 0
    bad_streak = hafiz_item.bad_streak or 0

    if bad_streak >= 3:
        return ("🆘", -2)  # Critical
    elif bad_streak >= 1:
        return ("⚠️", 0)   # Needs attention
    elif good_streak >= 5:
        return ("🔥", 3)   # On fire
    elif good_streak >= 2:
        return ("✅", 2)   # Good
    else:
        return ("➖", 1)   # Neutral
```

### 3.6 Tasks

- [ ] Create new route `/profile/dashboard`
- [ ] Create `render_stats_cards()` component
- [ ] Create `render_filters_bar()` component
- [ ] Create `render_bulk_actions_bar()` component
- [ ] Create `render_dashboard_table()` component
- [ ] Add `get_health_indicator()` function
- [ ] Implement status filter logic
- [ ] Implement mode filter logic
- [ ] Implement juz/surah filter logic
- [ ] Implement quick filters
- [ ] Implement pagination
- [ ] Add Alpine.js state for selections
- [ ] Update navigation to use new dashboard
- [ ] Write integration tests for filters

---

## Phase 4: Learning Flow Integration

### 4.1 Unified Learning Section

When status filter = "Learning", show special UI:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 🌱 LEARNING (5 pages)                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ Pages you're currently memorizing. Click "Complete" when ready.         │
├─────────────────────────────────────────────────────────────────────────┤
│ │ Page │ Surah       │ Type   │ Started    │ Action                    │
│ ├──────┼─────────────┼────────┼────────────┼───────────────────────────┤
│ │ 45   │ Al-Baqarah  │ NEW    │ Dec 15     │ [Complete ✓]              │
│ │ 46   │ Al-Baqarah  │ NEW    │ Dec 15     │ [Complete ✓]              │
│ │ 13   │ Al-Baqarah  │ RENEW  │ Dec 17     │ [Complete ✓]              │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 "Start Learning" Flow

From dashboard:
1. Filter by "Not Memorized"
2. Select pages
3. Click "🌱 Start Learning"
4. Modal: Configure starting mode + rep counts (optional)
5. Confirm → Creates events, pages move to LEARNING status

### 4.3 "Renew" Flow

From dashboard:
1. Filter by "Struggling" (or select from any view)
2. Select pages
3. Click "🔄 Renew"
4. Confirm → Creates `started_renew` event, pages move to LEARNING

### 4.4 "Complete" Flow

From Learning section:
1. Click "Complete" on a page (or bulk select + complete)
2. Creates `completed` event
3. Page moves to REPS (DR) with configured settings

### 4.5 Tasks

- [ ] Add `start_learning` bulk action route
- [ ] Add `renew` bulk action route
- [ ] Add `complete_learning` route
- [ ] Create learning section UI
- [ ] Add "Type" column (NEW vs RENEW) based on event history
- [ ] Deprecate separate `/new_memorization` page (redirect to dashboard)
- [ ] Write tests for learning flows

---

## Phase 5: Page History & Details

### 5.1 Page History on Details Page

Add to `/page_details/{item_id}`:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 📜 PAGE JOURNEY                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ Dec 15  🌱 Started learning (NEW)                                       │
│ Dec 16  ✅ Completed → Daily Reps                                       │
│ Dec 23  📈 Advanced → Weekly Reps (7/7)                                 │
│ Jan 15  🎓 Graduated → Solid                                            │
│ Jan 20  😰 Slipped → Struggling (bad rating)                            │
│ Feb 10  💪 Recovered → Solid                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Tasks

- [ ] Add `render_page_journey()` component
- [ ] Update page_details to include journey section
- [ ] Add event icons and formatting

---

## Phase 6: Cleanup & Polish

### 6.1 Navigation Updates

- Update navbar: "Profile" → links to `/profile/dashboard`
- Remove or redirect `/profile/juz`, `/profile/surah`, `/profile/page` (all unified)
- Redirect `/new_memorization` → `/profile/dashboard?status=not_memorized`
- Keep `/profile/mode_management` for now (can deprecate later)

### 6.2 Mobile Optimization

- Stats cards: horizontal scroll on mobile
- Filters: collapsible on mobile
- Table: responsive with priority columns

### 6.3 Tasks

- [ ] Update navigation links
- [ ] Add redirects for old routes
- [ ] Mobile-responsive stats cards
- [ ] Collapsible filters on mobile
- [ ] Responsive table design
- [ ] Final UI polish

---

## Database Schema Summary

### New Table: `page_events`

```sql
CREATE TABLE page_events (
    id INTEGER PRIMARY KEY,
    hafiz_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    from_mode TEXT,
    to_mode TEXT,
    event_date TEXT NOT NULL,
    triggered_by TEXT DEFAULT 'user',
    FOREIGN KEY (hafiz_id) REFERENCES hafizs(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id)
);
```

### No Changes to Existing Tables

Status is derived from existing `hafizs_items.memorized` + `hafizs_items.mode_code`.

---

## File Changes Summary

| File | Changes |
|------|---------|
| `migrations/0025-create-page-events.sql` | NEW - Events table |
| `database.py` | Add `page_events` table reference |
| `app/events_model.py` | NEW - Event logging helpers |
| `app/common_function.py` | Add status derivation, stats helpers |
| `app/profile.py` | Major rewrite - dashboard, filters, bulk actions |
| `app/new_memorization.py` | Add event logging, simplify |
| `app/fixed_reps.py` | Add event logging |
| `app/srs_reps.py` | Add event logging |
| `app/page_details.py` | Add page journey section |
| `main.py` | Update navigation |

---

## Testing Strategy

### Unit Tests
- Status derivation from mode_code
- Event type determination
- Health indicator calculation

### Integration Tests
- Event logging on mode transitions
- Filter query correctness
- Bulk action state changes

### E2E Tests
- Complete learning flow (start → complete)
- Renew flow (struggling → learning → complete)
- Reset flow (struggling → reps)
- Filter interactions
- Bulk selections

---

## Implementation Order

1. **Phase 1**: Events table + logging (foundation)
2. **Phase 2**: Status helpers (enable new UI)
3. **Phase 3**: Profile dashboard (main UX improvement)
4. **Phase 4**: Learning flow integration (unify workflows)
5. **Phase 5**: Page history (polish)
6. **Phase 6**: Cleanup (finalize)

Estimated: 4-6 focused sessions

---

## Success Metrics

- [ ] User can see all pages in unified dashboard
- [ ] User can filter by status, mode, juz, surah
- [ ] User can bulk select and perform actions
- [ ] User can start learning from dashboard (no separate page)
- [ ] User can renew struggling pages
- [ ] User can see complete page journey history
- [ ] All mode transitions are logged as events
