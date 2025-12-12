# Quran SRS - Complete Technical Specification

> **Purpose**: This specification enables recreating the Quran SRS application in any tech stack (Phoenix LiveView, React + Convex, FastAPI, Supabase, etc.) with identical functionality and data compatibility.

## Table of Contents

1. [Overview](#1-overview)
2. [Database Schema](#2-database-schema)
3. [Authentication System](#3-authentication-system)
4. [The Five Memorization Modes](#4-the-five-memorization-modes)
5. [Mode Transitions & Business Logic](#5-mode-transitions--business-logic)
6. [SRS Algorithm](#6-srs-algorithm)
7. [Close Date Processing](#7-close-date-processing)
8. [API Routes & Endpoints](#8-api-routes--endpoints)
9. [UI/UX Requirements](#9-uiux-requirements)
10. [Data Import Format](#10-data-import-format)

---

## 1. Overview

### 1.1 Purpose

Quran SRS is a Spaced Repetition System for Quran memorization (Hifz) and revision. It tracks memorization progress across 5 distinct modes, each with different review intervals and algorithms.

### 1.2 Core Concepts

- **User**: Account owner (parent/teacher) who can manage multiple hafiz profiles
- **Hafiz**: A memorizer profile with its own progress, settings, and virtual date
- **Item**: A reviewable unit (typically a Quran page or page-part)
- **Revision**: A single review event with date, rating, and mode
- **Plan**: A Full Cycle rotation through all memorized pages
- **Virtual Date**: Each hafiz has an independent `current_date` allowing independent timelines

### 1.3 Rating System

All reviews use a 3-point rating scale:
- **Good (+1)**: Strong recall, no hesitation
- **Ok (0)**: Acceptable recall with minor issues
- **Bad (-1)**: Poor recall, significant mistakes

---

## 2. Database Schema

### 2.1 Entity Relationship Diagram

```
users (1) ──────< (N) hafizs (1) ──────< (N) hafizs_items
                       │                        │
                       │                        │
                       ├──────< (N) revisions ──┘
                       │            │
                       │            │
                       └──────< (N) plans

items (1) ──────< (N) hafizs_items
  │
  └── pages (via page_id)
  └── surahs (via surah_id)

modes (referenced by mode_code in hafizs_items and revisions)
```

### 2.2 Table Definitions

#### `users` - Account holders

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);
```

#### `hafizs` - Memorizer profiles (one-to-many with users)

```sql
CREATE TABLE hafizs (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    daily_capacity INTEGER DEFAULT 5,  -- Pages per day for Full Cycle
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_date TEXT  -- Virtual system date (YYYY-MM-DD), NULL = use real date
);
```

#### `modes` - Review mode definitions

```sql
CREATE TABLE modes (
    code CHAR(2) PRIMARY KEY,  -- 'FC', 'NM', 'DR', 'WR', 'SR'
    name TEXT NOT NULL,
    description TEXT
);

-- Seed data (REQUIRED):
INSERT INTO modes (code, name, description) VALUES
    ('FC', 'Full Cycle', 'Sequential maintenance of all memorized content'),
    ('NM', 'New Memorization', 'Learning completely new pages'),
    ('DR', 'Daily Reps', 'Daily repetition (1-day interval) after initial memorization'),
    ('WR', 'Weekly Reps', 'Weekly repetition (7-day interval) after daily graduation'),
    ('SR', 'SRS Mode', 'Adaptive spaced repetition for problematic pages');
```

#### `surahs` - Quran chapters (114 surahs)

```sql
CREATE TABLE surahs (
    id INTEGER PRIMARY KEY,  -- 1-114
    name TEXT NOT NULL       -- Arabic/transliterated name
);
```

#### `pages` - Quran pages (604 pages in standard Madani mushaf)

```sql
CREATE TABLE pages (
    id INTEGER PRIMARY KEY,
    mushaf_id INTEGER,        -- For future multi-mushaf support
    page_number INTEGER NOT NULL,  -- 1-604
    juz_number INTEGER NOT NULL    -- 1-30
);
```

#### `items` - Reviewable units (pages or page-parts)

```sql
CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    page_id INTEGER NOT NULL REFERENCES pages(id),
    surah_id INTEGER REFERENCES surahs(id),
    surah_name TEXT,           -- Denormalized for performance
    item_type TEXT,            -- 'page' or 'page-part'
    part_number INTEGER,       -- Which part (1, 2, 3...) if page-part
    start_text TEXT,           -- First few words of the page/part
    description TEXT,          -- Optional custom description
    active BOOLEAN DEFAULT 1   -- Whether item is currently in use
);
```

#### `hafizs_items` - Per-hafiz progress tracking for each item

```sql
CREATE TABLE hafizs_items (
    id INTEGER PRIMARY KEY,
    hafiz_id INTEGER NOT NULL REFERENCES hafizs(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES items(id),
    page_number INTEGER,       -- Denormalized from items.page_id for queries

    -- Mode tracking
    mode_code CHAR(2) NOT NULL REFERENCES modes(code) DEFAULT 'FC',
    memorized BOOLEAN DEFAULT FALSE,

    -- Review scheduling
    next_review TEXT,          -- Next scheduled review date (YYYY-MM-DD)
    last_review TEXT,          -- Most recent review date
    next_interval INTEGER,     -- Days until next scheduled review
    last_interval INTEGER,     -- Actual days since previous review

    -- Statistics
    good_streak INTEGER DEFAULT 0,
    bad_streak INTEGER DEFAULT 0,

    -- SRS-specific
    srs_start_date TEXT,       -- When item entered SRS mode

    UNIQUE(hafiz_id, item_id)
);
```

#### `revisions` - Individual review records

```sql
CREATE TABLE revisions (
    id INTEGER PRIMARY KEY,
    hafiz_id INTEGER NOT NULL REFERENCES hafizs(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES items(id),
    revision_date TEXT NOT NULL,  -- YYYY-MM-DD
    rating INTEGER,               -- -1 (Bad), 0 (Ok), 1 (Good)
    mode_code CHAR(2) NOT NULL REFERENCES modes(code),
    plan_id INTEGER REFERENCES plans(id),  -- For Full Cycle grouping
    next_interval INTEGER         -- Stored for SRS history
);
```

#### `plans` - Full Cycle plan tracking

```sql
CREATE TABLE plans (
    id INTEGER PRIMARY KEY,
    hafiz_id INTEGER NOT NULL REFERENCES hafizs(id) ON DELETE CASCADE,
    completed BOOLEAN DEFAULT 0   -- 0 = active, 1 = completed
);
```

### 2.3 Key Constraints

- **CASCADE DELETE on User**: Deleting a user cascades to all hafizs and their related data
- **CASCADE DELETE on Hafiz**: Deleting a hafiz cascades to hafizs_items, revisions, and plans
- **UNIQUE(hafiz_id, item_id)** on hafizs_items: One progress record per item per hafiz
- Foreign keys must be enforced: `PRAGMA foreign_keys = ON;`

---

## 3. Authentication System

### 3.1 Two-Tier Authentication

The app uses a two-level authentication system:

**Level 1: User Authentication**
- Session key: `user_auth` stores `user_id`
- Required for: All routes except login/signup/logout
- On failure: Redirect to `/users/login`

**Level 2: Hafiz Authentication**
- Session key: `auth` stores `hafiz_id`
- Required for: All routes that access hafiz-specific data
- On failure: Redirect to `/hafiz/selection`
- **Important**: All queries to `revisions`, `hafizs_items`, and `plans` must be filtered by the current `hafiz_id`

### 3.2 Authentication Flow

```
User opens app
    │
    ├── Not logged in? → /users/login
    │                         │
    │                    Login success
    │                         │
    │                         ▼
    └── Logged in? ──────> /hafiz/selection
                               │
                          Select hafiz
                               │
                               ▼
                           Home page (/)
```

### 3.3 Password Handling

- Passwords are stored as plain text in current implementation
- **Recommendation**: Use bcrypt or similar hashing in production
- Login uses constant-time comparison to prevent timing attacks

---

## 4. The Five Memorization Modes

### 4.1 Mode Codes (Constants)

```python
FULL_CYCLE_MODE_CODE = "FC"
NEW_MEMORIZATION_MODE_CODE = "NM"
DAILY_REPS_MODE_CODE = "DR"
WEEKLY_REPS_MODE_CODE = "WR"
SRS_MODE_CODE = "SR"
```

### 4.2 Mode Descriptions

| Mode | Code | Purpose | Interval | Entry Condition | Exit Condition |
|------|------|---------|----------|-----------------|----------------|
| New Memorization | NM | Learn new pages | N/A | Manual selection | Close Date (→ DR) |
| Daily Reps | DR | Daily reinforcement | 1 day | From NM | 7 reviews (→ WR) |
| Weekly Reps | WR | Weekly consolidation | 7 days | From DR | 7 reviews (→ FC) |
| Full Cycle | FC | Maintain all memorized | Sequential | From WR | Ok/Bad rating (→ SR) |
| SRS Mode | SR | Fix problem pages | Adaptive | From FC (Ok/Bad) | Interval > 99 days (→ FC) |

### 4.3 Mode Progression Diagram

```
New Memorization (NM)
        │
        │ (Close Date - always promotes)
        ▼
Daily Reps (DR) ←── review count < 7: stay, schedule +1 day
        │
        │ (7 reviews completed)
        ▼
Weekly Reps (WR) ←── review count < 7: stay, schedule +7 days
        │
        │ (7 reviews completed)
        ▼
Full Cycle (FC) ←── Good rating: stay in cycle
        │
        │ (Ok or Bad rating during Close Date)
        ▼
SRS Mode (SR) ←── interval ≤ 99: stay, adapt interval
        │
        │ (interval > 99 days)
        ▼
Full Cycle (FC) [returns to main rotation]
```

---

## 5. Mode Transitions & Business Logic

### 5.1 New Memorization (NM)

**Entry**: User manually marks pages as "newly memorized" via UI

**On Close Date**:
```python
def update_hafiz_item_for_new_memorization(revision):
    hafiz_item = get_hafiz_item(revision.item_id)
    hafiz_item.mode_code = "DR"  # Promote to Daily Reps
    hafiz_item.memorized = True
    save(hafiz_item)
```

**Rating**: Always recorded as Good (+1)

### 5.2 Daily Reps (DR)

**Configuration**:
```python
DAILY_REPS_CONFIG = {
    "interval": 1,      # Review every 1 day
    "threshold": 7,     # Graduate after 7 reviews
    "next_mode": "WR"   # Graduate to Weekly Reps
}
```

**On Close Date**:
```python
def update_rep_item(revision):
    hafiz_item = get_hafiz_item(revision.item_id)
    current_date = get_current_date(revision.hafiz_id)
    review_count = count_revisions(revision.item_id, mode_code="DR")

    hafiz_item.last_interval = hafiz_item.next_interval

    if review_count < 7:
        # Stay in Daily Reps
        hafiz_item.next_interval = 1
        hafiz_item.next_review = current_date + 1 day
    else:
        # Graduate to Weekly Reps
        hafiz_item.mode_code = "WR"
        hafiz_item.next_interval = 7
        hafiz_item.next_review = current_date + 7 days

    save(hafiz_item)
```

**Display**: Show items where `next_review <= current_date` OR items reviewed today in DR mode

### 5.3 Weekly Reps (WR)

**Configuration**:
```python
WEEKLY_REPS_CONFIG = {
    "interval": 7,      # Review every 7 days
    "threshold": 7,     # Graduate after 7 reviews
    "next_mode": "FC"   # Graduate to Full Cycle
}
```

**On Close Date**:
```python
def update_rep_item(revision):
    hafiz_item = get_hafiz_item(revision.item_id)
    current_date = get_current_date(revision.hafiz_id)
    review_count = count_revisions(revision.item_id, mode_code="WR")

    hafiz_item.last_interval = hafiz_item.next_interval

    if review_count < 7:
        # Stay in Weekly Reps
        hafiz_item.next_interval = 7
        hafiz_item.next_review = current_date + 7 days
    else:
        # Graduate to Full Cycle
        hafiz_item.mode_code = "FC"
        hafiz_item.memorized = True
        hafiz_item.next_interval = NULL
        hafiz_item.next_review = NULL

    save(hafiz_item)
```

### 5.4 Full Cycle (FC)

**Purpose**: Sequential rotation through all memorized pages

**Key Concepts**:
- **Plan**: Groups revisions in current cycle via `plan_id`
- **Daily Capacity**: `hafiz.daily_capacity` controls how many pages shown per day
- **Sequential Order**: Items shown in `item_id` order (which maps to page order)

**Determining Next Items**:
```python
def get_full_cycle_items(hafiz_id, daily_capacity):
    plan_id = get_current_plan_id(hafiz_id)
    current_date = get_current_date(hafiz_id)

    # Get all memorized items (FC or SRS mode, memorized=true)
    memorized_items = query(
        "SELECT item_id FROM hafizs_items
         WHERE hafiz_id = ?
         AND memorized = TRUE
         AND mode_code IN ('FC', 'SR')
         ORDER BY item_id"
    )

    # Get items already revised in this plan (excluding today)
    revised_in_plan = query(
        "SELECT item_id FROM revisions
         WHERE plan_id = ? AND revision_date < ?",
        plan_id, current_date
    )

    # Find next unrevised items
    eligible = [i for i in memorized_items if i not in revised_in_plan]

    # Find where we left off (last revised item_id)
    last_revised = max(revised_in_plan) if revised_in_plan else 0

    # Get next N items starting after last_revised
    next_items = []
    page_count = 0
    for item_id in eligible:
        if item_id > last_revised and page_count < daily_capacity:
            next_items.append(item_id)
            page_count += get_page_portion(item_id)

    # Also include any items already reviewed today
    today_items = query(
        "SELECT item_id FROM revisions
         WHERE revision_date = ? AND mode_code = 'FC'",
        current_date
    )

    return sorted(set(next_items + today_items))
```

**On Close Date**:
```python
def update_hafiz_item_for_full_cycle(revision):
    hafiz_item = get_hafiz_item(revision.item_id)
    current_date = get_current_date(revision.hafiz_id)

    # If item is also in SRS, update its next_review
    if hafiz_item.mode_code == "SR":
        hafiz_item.next_review = current_date + hafiz_item.next_interval

    # Update last_interval (actual days since last review)
    hafiz_item.last_interval = days_since_last_review(revision.item_id)
    save(hafiz_item)
```

**Plan Completion**:
```python
def cycle_full_cycle_plan_if_completed(hafiz_id):
    plan_id = get_current_plan_id(hafiz_id)

    memorized_count = count(
        "SELECT * FROM hafizs_items
         WHERE mode_code IN ('FC', 'SR') AND memorized = TRUE"
    )
    revised_count = count(
        "SELECT * FROM revisions
         WHERE mode_code = 'FC' AND plan_id = ?",
        plan_id
    )

    if memorized_count == revised_count:
        # Mark current plan complete
        update(plans, id=plan_id, completed=True)
        # Create new plan
        insert(plans, hafiz_id=hafiz_id, completed=False)
```

### 5.5 SRS Mode (SR)

See [Section 6: SRS Algorithm](#6-srs-algorithm) for complete details.

---

## 6. SRS Algorithm

### 6.1 Overview

SRS Mode uses an adaptive spaced repetition algorithm based on prime number intervals. Items enter SRS when they receive Ok or Bad ratings in Full Cycle, and graduate back when intervals exceed 99 days.

### 6.2 Constants

```python
# Starting intervals when entering SRS
SRS_START_INTERVAL = {
    -1: 3,   # Bad rating → 3-day starting interval
    0: 10,   # Ok rating → 10-day starting interval
}

# Graduate back to Full Cycle when exceeded
SRS_END_INTERVAL = 99

# Prime number sequence for interval progression
SRS_INTERVALS = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
    53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101
]

# Rating multipliers for actual interval
RATING_MULTIPLIERS = {
    1: 1.0,    # Good: 100% of actual interval
    0: 0.5,    # Ok: 50% of actual interval
    -1: 0.35   # Bad: 35% of actual interval
}
```

### 6.3 Entry to SRS Mode

**Triggered**: During Close Date, after processing Full Cycle revisions

```python
def start_srs_for_ok_and_bad_rating(hafiz_id):
    current_date = get_current_date(hafiz_id)

    # Find FC revisions with Ok/Bad ratings today
    items_to_move = query("""
        SELECT revisions.item_id, revisions.rating
        FROM revisions
        JOIN hafizs_items ON revisions.item_id = hafizs_items.item_id
                         AND hafizs_items.hafiz_id = revisions.hafiz_id
        WHERE revisions.revision_date = ?
          AND revisions.hafiz_id = ?
          AND revisions.rating IN (-1, 0)
          AND revisions.mode_code = 'FC'
          AND hafizs_items.mode_code = 'FC'
    """, current_date, hafiz_id)

    for item in items_to_move:
        start_srs(item.item_id, hafiz_id, item.rating)


def start_srs(item_id, hafiz_id, rating):
    current_date = get_current_date(hafiz_id)
    next_interval = SRS_START_INTERVAL[rating]  # 3 for Bad, 10 for Ok

    hafiz_item = get_hafiz_item(item_id)
    hafiz_item.mode_code = "SR"
    hafiz_item.next_interval = next_interval
    hafiz_item.next_review = current_date + next_interval
    hafiz_item.srs_start_date = current_date
    save(hafiz_item)
```

### 6.4 Interval Calculation Algorithm

```python
def get_next_interval(item_id, rating):
    """
    Calculate next SRS interval using:
    1. Actual interval (days since last review)
    2. Rating-based penalty
    3. Prime number sequence lookup
    """
    hafiz_item = get_hafiz_item(item_id)
    current_date = get_current_date(hafiz_item.hafiz_id)

    # Step 1: Get actual interval (days since last review)
    actual_interval = days_between(hafiz_item.last_review, current_date)
    if not actual_interval:
        return None

    # Step 2: Apply rating penalty
    multiplier = RATING_MULTIPLIERS[rating]
    adjusted_actual = round(actual_interval * multiplier)

    # Step 3: Use max of planned vs adjusted actual
    planned_interval = hafiz_item.next_interval
    current_interval = max(planned_interval, adjusted_actual)

    # Step 4: Look up next interval from prime sequence
    triplet = get_interval_triplet(current_interval, SRS_INTERVALS)
    # triplet = [left, current, right]
    # rating -1 → index 0 (left), rating 0 → index 1 (current), rating 1 → index 2 (right)
    return triplet[rating + 1]


def get_interval_triplet(target, intervals):
    """
    Find [left, current, right] from prime sequence.
    Uses binary search to find largest interval <= target.
    """
    # Binary search for largest value <= target
    left, right = 0, len(intervals) - 1
    result_index = 0

    while left <= right:
        mid = (left + right) // 2
        if intervals[mid] <= target:
            result_index = mid
            left = mid + 1
        else:
            right = mid - 1

    i = result_index

    # Build triplet with bounds checking
    left_val = intervals[i - 1] if i > 0 else intervals[i]
    right_val = intervals[i + 1] if i < len(intervals) - 1 else intervals[i]

    return [left_val, intervals[i], right_val]
```

### 6.5 SRS Review Processing

```python
def update_hafiz_item_for_srs(revision):
    hafiz_item = get_hafiz_item(revision.item_id)
    current_date = get_current_date(revision.hafiz_id)

    next_interval = get_next_interval(revision.item_id, revision.rating)

    # Save current interval as last_interval
    hafiz_item.last_interval = hafiz_item.next_interval

    if next_interval <= SRS_END_INTERVAL:  # 99
        # Stay in SRS
        hafiz_item.next_interval = next_interval
        hafiz_item.next_review = current_date + next_interval
    else:
        # Graduate to Full Cycle
        hafiz_item.mode_code = "FC"
        hafiz_item.memorized = True
        hafiz_item.last_interval = days_since_last_review(revision.item_id)
        hafiz_item.next_interval = NULL
        hafiz_item.next_review = NULL
        hafiz_item.srs_start_date = NULL

    save(hafiz_item)

    # Also store next_interval on revision for history
    revision.next_interval = next_interval
    save(revision)
```

### 6.6 SRS Display Logic

```python
def get_srs_items_for_today(hafiz_id):
    current_date = get_current_date(hafiz_id)
    daily_limit = ceil(hafiz.daily_capacity * 0.5)  # 50% of capacity

    # Get all due SRS items
    due_items = query("""
        SELECT * FROM hafizs_items
        WHERE hafiz_id = ? AND mode_code = 'SR'
        AND (next_review <= ? OR last_review = ?)
        ORDER BY item_id
    """, hafiz_id, current_date, current_date)

    # Exclude pages upcoming in Full Cycle (3 days worth)
    last_fc_page = get_last_full_cycle_page(hafiz_id)
    if last_fc_page:
        exclude_end = last_fc_page + (hafiz.daily_capacity * 3)
        due_items = [i for i in due_items
                     if i.page_number < last_fc_page or i.page_number > exclude_end]

    # Rotate display: even days show first N, odd days show last N
    day_of_month = current_date.day
    if day_of_month % 2 == 0:
        return due_items[:daily_limit]
    else:
        return due_items[-daily_limit:]
```

---

## 7. Close Date Processing

### 7.1 Overview

"Close Date" is the core operation that:
1. Processes all reviews for the current date
2. Updates mode-specific logic for each reviewed item
3. Triggers SRS entry for Ok/Bad Full Cycle items
4. Checks for plan completion
5. Advances the hafiz's virtual date

### 7.2 Complete Algorithm

```python
def close_date(hafiz_id):
    hafiz = get_hafiz(hafiz_id)
    current_date = hafiz.current_date
    today = get_real_date()

    # Handle multi-day gap (skip to today if > 1 day elapsed)
    if days_between(current_date, today) > 1:
        hafiz.current_date = today
        save(hafiz)
        return redirect("/")

    # Get all revisions for current date
    revisions = query(
        "SELECT * FROM revisions WHERE hafiz_id = ? AND revision_date = ?",
        hafiz_id, current_date
    )

    # Process each revision based on mode
    for rev in revisions:
        if rev.mode_code == "FC":
            update_hafiz_item_for_full_cycle(rev)
        elif rev.mode_code == "NM":
            update_hafiz_item_for_new_memorization(rev)
        elif rev.mode_code in ["DR", "WR"]:
            update_rep_item(rev)
        elif rev.mode_code == "SR":
            update_hafiz_item_for_srs(rev)

        # Update statistics (streaks, last_review)
        populate_hafiz_item_stats(rev.item_id)

    # Move Ok/Bad FC items to SRS
    start_srs_for_ok_and_bad_rating(hafiz_id)

    # Check and cycle plan if complete
    cycle_full_cycle_plan_if_completed(hafiz_id)

    # Advance date by 1 day
    hafiz.current_date = current_date + 1 day
    save(hafiz)

    return redirect("/")
```

### 7.3 Statistics Update

```python
def populate_hafiz_item_stats(item_id):
    """Calculate and update good_streak, bad_streak, last_review"""
    revisions = query(
        "SELECT * FROM revisions WHERE item_id = ? ORDER BY revision_date ASC",
        item_id
    )

    good_streak = 0
    bad_streak = 0
    last_review = None

    for rev in revisions:
        if rev.rating == -1:  # Bad
            bad_streak += 1
            good_streak = 0
        elif rev.rating == 1:  # Good
            good_streak += 1
            bad_streak = 0
        else:  # Ok
            good_streak = 0
            bad_streak = 0

        last_review = rev.revision_date

    hafiz_item = get_hafiz_item(item_id)
    hafiz_item.good_streak = good_streak
    hafiz_item.bad_streak = bad_streak
    hafiz_item.last_review = last_review
    save(hafiz_item)
```

---

## 8. API Routes & Endpoints

### 8.1 Authentication Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/login` | Display login form |
| POST | `/users/login` | Authenticate user (email, password) → set session `user_auth` |
| GET | `/users/signup` | Display signup form |
| POST | `/users/signup` | Create user (email, password, name, confirm_password) |
| GET | `/users/logout` | Clear session, redirect to login |
| GET | `/users/account` | Display user profile form |
| POST | `/users/account` | Update user (name, email, optional password) |
| DELETE | `/users/delete/{user_id}` | Delete user and all data (cascade) |

### 8.2 Hafiz Management Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hafiz/selection` | Display all hafizs for current user |
| POST | `/hafiz/selection` | Select hafiz (current_hafiz_id) → set session `auth` |
| POST | `/hafiz/add` | Create hafiz (name, daily_capacity) |
| DELETE | `/hafiz/delete/{hafiz_id}` | Delete hafiz and all data |
| GET | `/hafiz/settings` | Display hafiz settings form |
| POST | `/hafiz/settings` | Update hafiz (name, daily_capacity, current_date) |

### 8.3 Home / Review Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Home page with 4 mode tabs (FC, SR, DR, WR) |
| GET | `/close_date` | Confirmation page before closing date |
| POST | `/close_date` | Process Close Date operation |
| POST | `/add/{item_id}` | Add revision (date, item_id, mode_code, rating, plan_id?) |
| PUT | `/edit/{rev_id}` | Update revision rating |
| POST | `/bulk_rate` | Bulk rate multiple items (item_ids[], rating, mode_code, date) |
| GET | `/report` | Datewise summary table of all revisions |

### 8.4 New Memorization Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/new_memorization/{type}` | Display pages by juz/surah/page |
| GET | `/new_memorization/expand/{type}/{number}` | Expand category to show individual pages |
| POST | `/new_memorization/update_as_newly_memorized/{item_id}` | Mark single item as memorized |
| POST | `/new_memorization/bulk_update_as_newly_memorized` | Mark multiple items (item_ids[]) |
| DELETE | `/new_memorization/update_as_newly_memorized/{item_id}` | Unmark item |

### 8.5 Profile Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/profile/{type}` | Memorization status by juz/surah/page (type) |
| GET | `/profile/{type}?status=memorized` | Filter to memorized only |
| GET | `/profile/{type}?status=not_memorized` | Filter to not memorized |
| POST | `/profile/update_status/{type}/{number}` | Toggle memorized status for group |
| GET | `/profile/custom_status_update/{type}/{number}` | Get items for custom update |
| POST | `/profile/custom_status_update/{type}/{number}` | Update individual items |

### 8.6 Page Details Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/page_details` | List all pages with revision counts |
| GET | `/page_details/{item_id}` | Detailed view for single page |
| GET | `/page_details/edit/{item_id}` | Edit form for page description |

### 8.7 Revision Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/revision` | List recent revisions (paginated) |
| GET | `/revision/bulk_edit?ids=1,2,3` | Bulk edit form for multiple revisions |
| PUT | `/revision/{rev_id}` | Update single revision |
| DELETE | `/revision/{rev_id}` | Delete single revision |

### 8.8 Admin Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/tables` | Database table viewer |
| GET | `/admin/backup` | Trigger manual backup |
| GET | `/admin/backups` | List all backups |
| PUT | `/admin/tables/{table}/{id}` | Update any table record |

---

## 9. UI/UX Requirements

### 9.1 Home Page

**Layout**:
- Header: Current date display + "Close Date" button
- Tabs: 4 tabs for FC, SR, DR, WR modes
- Each tab: Summary table with items to review

**Summary Table Columns**:
- Checkbox (for bulk selection)
- Page (linked to page details)
- Start Text
- Rating dropdown (auto-submits on change)

**Rating Dropdown**:
- Options: "- Select -", "✅ Good", "😄 Ok", "❌ Bad"
- Auto-submit: Change triggers immediate POST to save
- Row color: Green (Good), Yellow (Ok), Red (Bad), White (unrated)

**Bulk Actions**:
- Select-all checkbox in header
- Bulk action bar appears when items selected
- Buttons: Good, Ok, Bad

### 9.2 Hafiz Selection Page

**Layout**:
- List of hafiz cards (one row per hafiz)
- Current hafiz: Green highlight, "← Go Back" button
- Other hafizs: Name button + delete icon
- Add hafiz form at bottom

### 9.3 New Memorization Page

**Layout**:
- Recently memorized table (last 10)
- Browse by: Juz / Surah / Page tabs
- Expandable rows with checkboxes
- Bulk "Set as Newly Memorized" button

### 9.4 Profile Page

**Layout**:
- Filter buttons: Memorized / Not Memorized
- Browse by: Juz / Surah / Page tabs
- Status checkbox per row
- "Customize" link for multi-item groups

### 9.5 Page Details

**Layout**:
- Navigation: Previous / Next page arrows
- Page info: Number, Surah, Juz
- Editable description and start text
- Summary stats table
- Full revision history table

---

## 10. Data Import Format

### 10.1 Database Compatibility

For drop-in data migration, ensure:
1. Same table names and column names
2. Same data types (INTEGER, TEXT, BOOLEAN)
3. Same foreign key relationships
4. Date format: `YYYY-MM-DD`

### 10.2 Required Seed Data

**Modes** (must exist before any other data):
```sql
INSERT INTO modes (code, name, description) VALUES
    ('FC', 'Full Cycle', 'Sequential maintenance of all memorized content'),
    ('NM', 'New Memorization', 'Learning completely new pages'),
    ('DR', 'Daily Reps', 'Daily repetition (1-day interval) after initial memorization'),
    ('WR', 'Weekly Reps', 'Weekly repetition (7-day interval) after daily graduation'),
    ('SR', 'SRS Mode', 'Adaptive spaced repetition for problematic pages');
```

**Surahs** (114 surahs with names)

**Pages** (604 pages with juz_number 1-30)

**Items** (one or more items per page)

### 10.3 New Hafiz Initialization

When creating a new hafiz:

```python
def initialize_hafiz(hafiz_id):
    # Create hafizs_items for all active items
    active_items = query("SELECT id, page_id FROM items WHERE active = 1")

    for item in active_items:
        page = get_page(item.page_id)
        insert(hafizs_items,
            hafiz_id=hafiz_id,
            item_id=item.id,
            page_number=page.page_number,
            mode_code="FC",
            memorized=False
        )

    # Create initial plan
    insert(plans, hafiz_id=hafiz_id, completed=False)
```

### 10.4 Export Format

To export existing data for migration:

```sql
-- Export in order of foreign key dependencies
.mode csv
.headers on

.output users.csv
SELECT * FROM users;

.output hafizs.csv
SELECT * FROM hafizs;

.output surahs.csv
SELECT * FROM surahs;

.output pages.csv
SELECT * FROM pages;

.output items.csv
SELECT * FROM items;

.output plans.csv
SELECT * FROM plans;

.output hafizs_items.csv
SELECT * FROM hafizs_items;

.output revisions.csv
SELECT * FROM revisions;
```

---

## Appendix A: Date Utility Functions

```python
def add_days(date_str, days):
    """Add days to YYYY-MM-DD date string"""
    date = parse(date_str, "%Y-%m-%d")
    return format(date + timedelta(days=days), "%Y-%m-%d")

def days_between(date1_str, date2_str):
    """Return days between two dates (positive if date2 > date1)"""
    if not date1_str or not date2_str:
        return 0
    date1 = parse(date1_str, "%Y-%m-%d")
    date2 = parse(date2_str, "%Y-%m-%d")
    return (date2 - date1).days

def current_date():
    """Return today as YYYY-MM-DD"""
    return format(datetime.now(), "%Y-%m-%d")

def date_to_human(date_str):
    """Convert YYYY-MM-DD to 'Jan 15 Mon' format"""
    date = parse(date_str, "%Y-%m-%d")
    return format(date, "%b %d %a")
```

---

## Appendix B: Page Portion Calculation

Some pages are split into multiple items (parts). Calculate page count correctly:

```python
def get_page_portion(item_id):
    """
    Returns fraction of page this item represents.
    If page has 4 parts, each part = 0.25
    If page has 1 item, it = 1.0
    """
    item = get_item(item_id)
    items_in_page = count("SELECT * FROM items WHERE page_id = ? AND active = 1", item.page_id)
    return 1.0 / items_in_page if items_in_page > 0 else 0

def get_page_count(item_ids):
    """Sum page portions for list of item_ids"""
    total = sum(get_page_portion(id) for id in item_ids)
    # Round to 1 decimal, return as int if whole number
    rounded = round(total, 1)
    return int(rounded) if rounded == int(rounded) else rounded
```

---

## Appendix C: Compact Range Formatting

Display page ranges compactly (e.g., "1-5, 7, 9-12"):

```python
def compact_format(numbers):
    """Convert [1,2,3,5,7,8,9] to '1-3, 5, 7-9'"""
    if not numbers:
        return ""

    unique = sorted(set(numbers))
    result = []
    start = end = unique[0]

    for num in unique[1:] + [None]:
        if num is not None and num == end + 1:
            end = num
        else:
            if start == end:
                result.append(str(start))
            else:
                result.append(f"{start}-{end}")
            if num is not None:
                start = end = num

    return ", ".join(result)
```

---

## Appendix D: Rating Display Map

```python
RATING_MAP = {
    "1": "✅ Good",
    "0": "😄 Ok",
    "-1": "❌ Bad"
}
```

---

*End of Specification*
