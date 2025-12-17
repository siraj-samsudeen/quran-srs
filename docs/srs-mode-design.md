# SRS (Spaced Repetition System) Mode Design

## Complete Algorithm Implementation

Based on comprehensive code analysis and database examination with real examples:

## SRS Feature Implementation Context

SRS was implemented on July 9, 2025 (earliest SRS revision date in database)
- First 4 pages entered SRS: 359, 361, 362, 378
- Total 46 pages have used SRS since implementation
- Pages enter SRS via: (1) 2 consecutive bad ratings in full-cycle, OR (2) manual user action

## Database Tables and Columns

### 1. srs_booster_pack TABLE:
- id: Pack identifier (1=Standard, 2=Relaxed, 3=Extended, 4=Long-term)
- start_interval: Starting interval in days (Standard SRS: 7 days)
- end_interval: Graduation threshold (Standard SRS: 30 days)
- interval_days: Comma-separated progression "2,3,5,7,11,13,17,19,23,29,31,37,41,43..."

### 2. hafizs_items TABLE (current state):
- mode_code: 'SR' = SRS mode, 'FC' = Full Cycle mode
- status_id: 5 = SRS active, 6 = Not started
- srs_start_date: When item entered SRS (e.g., '2025-07-09')
- srs_booster_pack_id: Which pack to use (typically 1 = Standard)
- last_review: Date of most recent SRS review
- next_review: When item is due for next SRS review
- last_interval: Previous interval used
- current_interval: Days since last review based on the current_date in the hafiz table
- next_interval: Days to add for next review (NULL = graduated)

### 3. revisions TABLE (review history):
- mode_code: 'SR' = SRS review, 'FC' = Full Cycle review
- rating: -1=bad, 0=ok, 1=good
- last_interval: The interval position used to calculate this review (from algorithm state)
- current_interval: Actual days between previous review and this review date
- next_interval: Calculated interval for next review based on this rating

## SRS Lifecycle Events

### EVENT 1: PAGE ENTERS SRS MODE
**What triggers:** EITHER 2 consecutive bad ratings in full-cycle mode, OR user manually adds to SRS

**Note:** SRS feature was implemented starting July 9, 2025 (earliest SRS revision date)

**Database changes in hafizs_items:**
- mode_code = 'SR' (SRS mode)
- status_id = 5 (SRS active)
- srs_start_date = current_date (when SRS began)
- srs_booster_pack_id = 1 (Standard SRS pack)
- next_interval = 7 (start_interval from booster pack)
- next_review = srs_start_date + next_interval (7 days)
- last_interval, current_interval = NULL (no reviews yet)

### EVENT 2: SRS REVISION RECORDED
**What triggers:** Page comes up in SRS daily plan (when current_date >= next_review), user reviews it and selects rating (-1, 0, or 1)

**Algorithm steps:**
1. Find current algorithm position (last_interval from previous review, or start_interval)
2. Calculate actual days since last review (current_interval)
3. Get [bad, ok, good] interval options based on current position
4. Select next_interval based on rating: [-1]=bad option, [0]=ok option, [1]=good option
5. Check if next_interval > end_interval (30 for Standard SRS)

**SCENARIO A: Rating = -1 (Bad) - Move Backward**
- next_interval = previous prime number (shorter interval)
- Example: at position 11 → rating=-1 → next_interval=7 (regression)
- Prime sequence: ...5, 7, 11, 13, 17... (moves from 11 back to 7)

**SCENARIO B: Rating = 0 (Ok) - Stay Same**
- next_interval = current position (repeat same interval)
- Example: at position 11 → rating=0 → next_interval=11 (maintain)
- Prime sequence: ...5, 7, 11, 13, 17... (stays at 11)

**SCENARIO C: Rating = 1 (Good) - Move Forward**
- next_interval = next prime number (longer interval)
- Example: at position 11 → rating=1 → next_interval=13 (advance)
- Prime sequence: ...5, 7, 11, 13, 17... (moves from 11 forward to 13)

**Database updates:**
- revisions table: new record with rating and all three intervals
- hafizs_items: updated with new next_interval and next_review date

### EVENT 3: PAGE GRADUATES FROM SRS
**What triggers:** next_interval exceeds end_interval (30 for Standard SRS)

**Database changes in hafizs_items:**
- next_interval = NULL (graduation marker)
- next_review = NULL (no longer scheduled)
- current_interval, last_interval = NULL (no more reviews)
- srs_booster_pack_id, srs_start_date = NULL (no longer in SRS mode)
- mode_code = 'FC' (returns to Full Cycle mode)
- status_id = 1 (returns to normal memorized status)

**Result:** Page successfully completed SRS and returns to regular sequential revision

## Special Cases in SRS Revision Logic

### FIRST SRS REVISION FOR EACH PAGE:
Special handling when page has no previous SRS reviews:
- current_interval: Days since last_review (often much larger than expected)
- last_interval: Set to start_interval (7 for Standard SRS) from algorithm state
- Algorithm position: Uses start_interval as baseline for rating calculations

**Real Example - Page 64 First SRS Review (2025-07-25):**
- srs_start_date: 2025-07-18
- last_interval=7: Algorithm starts at start_interval position
- current_interval=62: Actual 62 days since last_review (major delay)
- rating=0 (ok): Stay at same algorithm position
- next_interval=7: Algorithm kept at position 7 despite 62-day delay

**Key insight:** Algorithm position is independent of actual timing delays

### DELAYED REVIEWS (current_interval > last_interval):
What happens when user reviews late (after scheduled next_review date):
- Algorithm ignores the delay for progression decisions
- current_interval reflects actual calendar delay
- last_interval still represents algorithm position
- Rating determines progression based on algorithm position, not actual timing

**Real Example - Page 100 (user manually added to SRS on 2025-07-18):**
- Full cycle history: May 26 (bad rating) - only 1 bad, not 2 consecutive
- Review 1 (2025-07-25): last_interval=7, current_interval=7, next_interval=11 (rating=1 good)  
- Review 2 (2025-08-05): last_interval=11, current_interval=11, next_interval=7 (rating=-1 bad)
- User manually triggered SRS entry (not automatic via 2 consecutive bad ratings)
- Both SRS reviews happened exactly on schedule
- Shows normal timing with rating progression: 7→11→7 (good then bad)

**Real Example - Page 163 Sequential Delays:**
- Review 1: last_interval=7, current_interval=61, next_interval=5 (rating=-1 bad)
- Review 2: last_interval=5, current_interval=7, next_interval=5 (rating=0 ok)  
- Review 3: last_interval=5, current_interval=6, next_interval=5 (rating=0 ok)
- Each review was delayed but algorithm regression/maintenance was based on ratings
- Shows algorithm's independence from actual review timing

## Revisions Table Interval Columns Explained

Each revision record stores three interval values that capture different aspects:

### 1. last_interval: The SRS Algorithm Position
- Where the page was positioned in the SRS interval progression
- Used as input to determine rating options [bad, ok, good]
- Carried forward from previous review's next_interval

### 2. current_interval: Actual Days Between Reviews
- Real calendar days between previous review date and this review date
- For first revision: days since last_review (on other mode)
- For subsequent reviews: days since previous revision
- Shows whether review happened early, on-time, or late

### 3. next_interval: Calculated Next Interval Based on Rating
- Determined by SRS algorithm based on user's rating for this review
- How many days to wait before next SRS review
- Becomes the last_interval for subsequent review

## Real Examples: SRS Algorithm in Action

Available prime intervals: [2,3,5,7,11,13,17,19,23,29,31...] (graduation at >30)

### EXAMPLE 1: PAGE 359 (Started with interval 2)
SRS Start: 2025-07-09, start_interval=2 (Before changing the start_interval=7 on standard pack)

**Review 1 (2025-07-09): rating=1 (good)**
- last_interval=2: Algorithm started at position 2
- current_interval=5: Days since SRS start  
- next_interval=3: Prime sequence [2,2,3] → rating=1 → advance to 3

**Review 2 (2025-07-13): rating=1 (good)**
- last_interval=3: Algorithm position from previous
- current_interval=4: Actual 4 days between reviews
- next_interval=5: Prime sequence [2,3,5] → rating=1 → advance to 5

**Review 3 (2025-07-18): rating=1 (good)**
- last_interval=5: Algorithm position 5
- current_interval=5: Exactly 5 days (on time)
- next_interval=7: Prime sequence [3,5,7] → rating=1 → advance to 7

**Review 4 (2025-07-25): rating=1 (good) → advance to 11**
**Review 5 (2025-08-05): rating=0 (ok) → stays at 11**

**Progression:** 2→3→5→7→11→11 (good ratings advance, ok rating maintains)

**Key insight:** If the current position is 2 the rating bad and ok stays at the position 2.

### EXAMPLE 2: PAGE 89 (Started with interval 7)  
SRS Start: ~2025-07-22, start_interval=7 (Standard SRS pack)

**Review 1 (2025-07-29): rating=0 (ok)**
- last_interval=7: Algorithm started at Standard position 7
- current_interval=7: Exactly on time
- next_interval=7: Prime sequence [5,7,11] → rating=0 → stay at 7

**Review 2 (2025-08-05): rating=-1 (bad)**
- last_interval=7: Algorithm position unchanged from previous
- current_interval=7: Exactly 7 days (on time)
- next_interval=5: Prime sequence [5,7,11] → rating=-1 → regress to 5

**Review 3 (2025-08-10): rating=1 (good)**
- last_interval=5: Algorithm regressed to position 5
- current_interval=5: Exactly 5 days (on time) 
- next_interval=7: Prime sequence [3,5,7] → rating=1 → advance to 7

**Progression:** 7→7→5→7 (ok maintains, bad regresses, good advances)

**GRADUATION:** When next_interval > end_interval (30), set next_interval=NULL

## Special Scenario (Pages 64 & 73)

**Cross-Mode Review Functionality:** Pages in SRS mode can still be reviewed in Full Cycle mode without disrupting SRS progression.

### Page 64 Example:
**SRS History:**
- 2025-07-25: First SRS review (rating=0, ok) → next_interval=7, next_review=2025-08-01
- 2025-08-01: Second SRS review (rating=1, good) → next_interval=11, next_review=2025-08-12

**Cross-Mode Event (2025-08-11):**
- Page 64 reviewed in Full Cycle mode (mode_code='FC') while still in SRS
- SRS schedule: Due 2025-08-12 (next day)
- Full Cycle review recorded normally without affecting SRS state

**Key Behaviors:**
1. **SRS State Preserved:** Page remains in SRS mode with next_review=2025-08-12
2. **No SRS Progression:** Full Cycle review doesn't advance SRS intervals
3. **Dual Mode Operation:** Same page can be active in both systems simultaneously
4. **Independent Tracking:** Each mode maintains separate revision history

**Technical Implementation:** The system differentiates reviews by mode_code ('FC'=Full Cycle, 'SR'=SRS) allowing parallel operation without interference. This flexibility lets users review SRS pages in regular sequential order when desired while maintaining their SRS schedule.

## Key Algorithm Functions

- get_srs_interval_list(): Creates filtered interval progression
- get_interval_triplet(): Maps current position to [prev,curr,next]
- recalculate_intervals_on_srs_records(): Recalculate intervals if the page gets edited or deleted (Bug: Shouldn't update the first record's last_interval as it is a historical decision)
- get_interval_based_on_rating(): Determines next interval from rating

## Revision Types and Algorithm Behavior

### Two REVISION SCENARIOS:

#### 1. ON-TIME REVISION  
**What happens:** SRS page reviewed exactly when current_date >= next_review.

**Current behavior:** Algorithm handles this correctly with normal SRS progression.

#### 2. DELAYED REVISION (Future Enhancement)
**What happens:** SRS page reviewed after its scheduled next_review date.

**Current behavior:** Algorithm ignores the delay - progression based purely on rating.

**Planned enhancement:** If rating=good AND current_interval > expected_interval, use actual delay as bonus:
- Find next interval higher than current_interval in prime sequence
- Use that as next_interval instead of normal progression  
- Reward learner for maintaining quality despite longer interval

**Note:** This delayed revision bonus feature is NOT YET IMPLEMENTED.

## Data Redundancy Analysis

### STRATEGIC DESIGN PRINCIPLE:
"Whenever we change any implementation, all past revision data should NOT be affected"

This drives the dual-storage approach:
- **revisions table** = Immutable historical record of algorithm decisions
- **hafizs_items table** = Current state cache that can be recalculated from revisions

### REDUNDANCY ANALYSIS:

#### TRULY REDUNDANT COLUMNS:

1. **hafizs_items.current_interval** - REDUNDANT
   - Can always be calculated as: current_date - last_review  
   - No need to store since both current_date and last_review are available
   - **Recommendation:** Remove this column, calculate dynamically

#### PERFORMANCE OPTIMIZATIONS (Technically redundant but justified):

2. **hafizs_items.last_interval** - Derivable but kept for performance
   - Can be derived from: most recent revision's next_interval
   - Kept to avoid querying revisions table constantly

3. **hafizs_items.next_interval** - Derivable but kept for performance  
   - Can be derived from: most recent revision's next_interval
   - Kept to avoid querying revisions table constantly

4. **hafizs_items.last_review** - Derivable but kept for performance
   - Can be derived from: most recent revision's revision_date
   - Kept to avoid querying revisions table constantly

5. **hafizs_items.next_review** - Derivable but kept for performance
   - Can be calculated as: last_review + next_interval
   - Kept because it's queried frequently for daily planning

#### ESSENTIAL NON-REDUNDANT COLUMNS:

6. **revisions.current_interval** - ESSENTIAL
   - Historical fact about actual timing between reviews
   - Cannot be recalculated - represents real user behavior
   - Critical for future delayed revision bonus feature
   - Must be preserved exactly as it occurred

7. **revisions.last_interval** - ESSENTIAL for algorithm evolution
   - Records what algorithm position was used for historical decision
   - Needed if algorithm changes and you want to understand past decisions
   - Cannot be recalculated without re-running entire algorithm

8. **revisions.next_interval** - ESSENTIAL for algorithm evolution  
   - Records what algorithm decided at that point in time
   - Preserves historical algorithm behavior even if logic changes
   - Cannot be recalculated without re-running entire algorithm

### CONCLUSION:
Only **hafizs_items.current_interval** is truly redundant and could be removed. All other apparent redundancy serves either:
- **Performance optimization** (avoid expensive revisions table queries)
- **Algorithm evolution** (preserve historical decisions when logic changes)
- **Historical accuracy** (preserve actual timing facts that cannot be recalculated)

The storage cost is minimal compared to the architectural benefits of having both an immutable audit trail (revisions) and a fast-access current state cache (hafizs_items).

## SRS Algorithm v2 - Unified Interval System

A unified spaced repetition system that treats all review modes as **interval bands** on a continuous spectrum. The system adapts to user behavior, tracks peak performance, and uses rating-based progression throughout.

## Core Philosophy

1. **Trust Success**: Good/Perfect at long intervals = proven strength
2. **Hedge on Failure**: Bad after long gap = unclear cause, don't punish harshly
3. **Accelerate Recovery**: Help items return to their proven peak
4. **Two Speeds**: Fast growth early (multiplicative), careful maintenance later (additive)
5. **Gradual Demotion**: Struggling items drop one level, not all the way back

---

## Rating Scale

| Value | Name     | Meaning                        | Effect                   |
| ----- | -------- | ------------------------------ | ------------------------ |
| 2     | Perfect  | Instant, effortless recall     | Strongest progression    |
| 1     | Good     | Solid recall with minor effort | Normal progression       |
| 0     | Ok       | Got it but struggled           | Hold/minimal progression |
| -1    | Bad      | Significant struggle           | Regression               |
| -2    | Very Bad | Complete failure               | Strong regression        |

---

## Interval Bands (Unified Model)

Instead of separate modes (DR/WR/SRS), we have **bands** on an interval spectrum:

| Band        | Code | Interval Range | Target  | Reviews to Graduate | Display Name |
| ----------- | ---- | -------------- | ------- | ------------------- | ------------ |
| Daily       | D1   | 1-6 days       | 1 day   | 7 reviews + 3 good  | Daily        |
| Weekly      | W1   | 7-13 days      | 7 days  | 5 reviews + 3 good  | Weekly       |
| Fortnightly | W2   | 14-29 days     | 14 days | 4 reviews + 3 good  | Fortnightly  |
| Monthly     | M1   | 30-59 days     | 30 days | 3 reviews + 3 good  | Monthly      |
| Full Cycle  | FC   | 60+ days       | N/A     | N/A                 | Maintenance  |

```
┌─────────────────────────────────────────────────────────────────┐
│                     INTERVAL SPECTRUM                           │
├─────────┬─────────┬──────────┬─────────┬───────────────────────┤
│   D1    │   W1    │    W2    │   M1    │         FC            │
│  1-6d   │  7-13d  │  14-29d  │ 30-59d  │        60+d           │
│  Daily  │ Weekly  │Fortnght  │ Monthly │    Full Cycle         │
└─────────┴─────────┴──────────┴─────────┴───────────────────────┘
     ↑                                                ↑
     │      Items flow along spectrum based on       │
     │      performance (graduation/demotion)        │
     └────────────────────────────────────────────────┘
```

---

## Graduation Criteria

An item graduates to the next band when ANY of these conditions are met:

1. **Performance-based**: 3 consecutive Good/Perfect ratings
2. **Count-based**: Completed required reviews for current band
3. **Manual**: User explicitly graduates the item

```python
def should_graduate(item, band_config) -> bool:
    return (
        item.good_streak >= 3 or
        item.band_review_count >= band_config["reviews_to_graduate"] or
        item.manual_graduation_requested
    )
```

---

## Two-Phase Algorithm

### Phase 1: Growth (interval < 30 days)

Multiplicative - quickly find the right level:

```python
GROWTH_MULTIPLIERS = {
    2: 2.0,    # Perfect → double
    1: 1.5,    # Good → 50% increase
    0: 1.1,    # Ok → slight increase
   -1: 0.5,    # Bad → halve
   -2: 0.3,    # Very Bad → aggressive cut
}

def apply_growth_phase(base: int, rating: int) -> float:
    return base * GROWTH_MULTIPLIERS[rating]
```

### Phase 2: Maintenance (interval ≥ 30 days)

Additive for positive ratings, midpoint regression for negative:

```python
MAINTENANCE_ADDITIONS = {
    2: 5,      # Perfect → +5 days
    1: 3,      # Good → +3 days
    0: 1,      # Ok → +1 day
}

def apply_maintenance_phase(base: int, rating: int, peak_good: int | None) -> int:
    if rating >= 0:
        return base + MAINTENANCE_ADDITIONS[rating]

    # Bad: midpoint toward half of peak (or half of base)
    if rating == -1:
        lower = (peak_good // 2) if peak_good else (base // 2)
        return (base + lower) // 2

    # Very Bad: midpoint toward third of peak (or third of base)
    lower = (peak_good // 3) if peak_good else (base // 3)
    return (base + lower) // 2
```

---

## Core Algorithm

### Main Calculation

```python
MIN_INTERVAL = 1
PHASE_THRESHOLD = 30
RECOVERY_BOOST = 0.3  # Cover 30% of gap to peak

def calculate_next_interval(
    scheduled_interval: int,    # What was scheduled for this review
    actual_interval: int,       # Days since last review
    rating: int,                # -2 to 2
    peak_good: int | None,      # Best proven interval
) -> int:
    # Step 1: Determine base interval
    base = determine_base(scheduled_interval, actual_interval, rating)

    # Step 2: Apply phase-appropriate transformation
    if base < PHASE_THRESHOLD:
        result = apply_growth_phase(base, rating)
    else:
        result = apply_maintenance_phase(base, rating, peak_good)

    # Step 3: Recovery boost when below proven peak
    if rating >= 1 and peak_good and result < peak_good:
        gap = peak_good - result
        result += gap * RECOVERY_BOOST

    return max(MIN_INTERVAL, round(result))
```

### Base Interval Determination

Who do we trust - the schedule or actual performance?

```python
def determine_base(scheduled: int, actual: int, rating: int) -> int:
    # Good/Perfect after long wait: trust actual (they proved it)
    if rating >= 1 and actual > scheduled:
        return actual

    # Ok/Bad after VERY long wait: hedge with midpoint
    if rating in (0, -1) and actual > scheduled * 2:
        return (scheduled + actual) // 2

    # Very Bad: always use scheduled (serious failure)
    # Default: use scheduled
    return scheduled
```

| Scheduled | Actual | Rating  | Base | Why                     |
| --------- | ------ | ------- | ---- | ----------------------- |
| 15        | 15     | Good    | 15   | On-time                 |
| 15        | 45     | Good    | 45   | Late success, earned it |
| 15        | 60     | Bad     | 37   | Late failure, hedge     |
| 15        | 60     | VeryBad | 15   | Serious failure         |

---

## Band Entry & Demotion

### Entry from New Memorization

```python
def get_entry_interval(rating: int, actual_interval: int | None) -> int:
    """Starting interval when entering from New Memorization."""
    # New memorization always starts at D1 with interval=1
    return 1
```

### Demotion (Bad Streak)

Demote gradually based on current interval:

```python
def get_demotion_band(current_interval: int) -> str:
    """Determine which band to demote to after bad streak (2 consecutive)."""
    if current_interval <= 6:
        return "D1"  # Already in daily, stay there
    elif current_interval <= 13:
        return "D1"  # Weekly → Daily
    elif current_interval <= 29:
        return "W1"  # Fortnightly → Weekly
    elif current_interval <= 59:
        return "W2"  # Monthly → Fortnightly
    else:
        return "M1"  # FC → Monthly

def get_demotion_interval(current_interval: int, rating: int) -> int:
    """Calculate new interval after demotion."""
    if rating == -2:  # Very Bad
        return max(1, current_interval // 4)
    else:  # Bad
        return max(1, current_interval // 2)
```

---

## Peak Tracking

Updated on **every review** (all bands, including FC):

```python
def update_peaks(item_id: int, actual_interval: int, rating: int):
    """Update peak intervals after any review."""
    item = get_hafizs_items(item_id)

    # peak_interval_any: Always update if longest seen
    if actual_interval > (item.peak_interval_any or 0):
        item.peak_interval_any = actual_interval

    # peak_interval_good: Only on Good (1) or Perfect (2)
    if rating >= 1:
        if actual_interval > (item.peak_interval_good or 0):
            item.peak_interval_good = actual_interval

    hafizs_items.update(item)
```

---

## Streak Tracking

Bad streak counts **across all bands**:

```python
def update_streaks(item_id: int, rating: int) -> tuple[int, int]:
    """Update streaks, returns (good_streak, bad_streak)."""
    item = get_hafizs_items(item_id)

    if rating >= 1:  # Good or Perfect
        item.good_streak = (item.good_streak or 0) + 1
        item.bad_streak = 0
    elif rating <= -1:  # Bad or Very Bad
        item.bad_streak = (item.bad_streak or 0) + 1
        item.good_streak = 0
    else:  # Ok
        item.good_streak = 0
        item.bad_streak = 0

    hafizs_items.update(item)
    return (item.good_streak, item.bad_streak)
```

---

## Database Schema

### hafizs_items (current state)

```sql
id INTEGER PRIMARY KEY,
hafiz_id INTEGER REFERENCES hafizs(id) ON DELETE CASCADE,
item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
page_number INTEGER,
mode_code TEXT,              -- 'D1', 'W1', 'W2', 'M1', 'FC', 'NM'
memorized BOOLEAN DEFAULT FALSE,

-- Scheduling
interval INTEGER,            -- Current interval (days between reviews)
next_review TEXT,            -- When due (YYYY-MM-DD)
last_review TEXT,            -- Date of last review

-- Streaks & Counts
good_streak INTEGER DEFAULT 0,
bad_streak INTEGER DEFAULT 0,
band_review_count INTEGER DEFAULT 0,   -- Reviews in current band

-- Peak Tracking
peak_interval_good INTEGER,  -- Best proven interval (Good/Perfect)
peak_interval_any INTEGER    -- Longest actual interval ever
```

### revisions (historical record)

```sql
id INTEGER PRIMARY KEY,
hafiz_id INTEGER REFERENCES hafizs(id) ON DELETE CASCADE,
item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
review_date TEXT,            -- YYYY-MM-DD
rating INTEGER,              -- -2 to 2
mode_code TEXT,              -- Band at time of review
plan_id INTEGER,             -- For FC sequential tracking

-- Interval data
interval INTEGER,            -- Interval assigned after this review
actual_interval INTEGER      -- Days since previous review
```

### transitions (event log)

```sql
id INTEGER PRIMARY KEY,
hafiz_id INTEGER REFERENCES hafizs(id) ON DELETE CASCADE,
item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
transition_date TEXT,        -- YYYY-MM-DD
from_mode TEXT,              -- NULL for initial memorization
to_mode TEXT,
trigger TEXT,                -- 'memorized', 'graduated', 'demoted', 'manual'
context TEXT                 -- JSON: {"rating": -1, "interval": 30}
```

---

## Close Date (Simplified)

Close Date is retained but streamlined. Most processing happens **immediately** when a review is recorded.

```python
def close_date(auth):
    """End-of-day processing (lightweight)."""
    # 1. Check if FC plan is complete
    cycle_full_cycle_plan_if_completed()

    # 2. Advance the virtual date
    advance_current_date(auth)
```

### What Happens Immediately (on review)

- Interval calculation
- next_review update
- Streak updates
- Peak updates
- Band graduation/demotion
- Transition logging

### What Happens at Close Date

- FC plan completion check
- Virtual date advancement

---

## Example Scenarios

### Scenario A: Normal Progression (New Memorization → FC)

```
Day 0:  Page memorized → D1, interval=1
        Transition: NULL → NM (memorized)
        Transition: NM → D1 (graduated)

Day 1:  Review Good → interval=1, count=1, good_streak=1
Day 2:  Review Good → interval=1, count=2, good_streak=2
Day 3:  Review Good → interval=1, count=3, good_streak=3 ✓
        → Graduate to W1! interval=7
        Transition: D1 → W1 (graduated)

Day 10: Review Good → interval=7, count=1, good_streak=1
Day 17: Review Good → interval=7, count=2, good_streak=2
Day 24: Review Good → interval=7, count=3, good_streak=3 ✓
        → Graduate to W2! interval=14
        Transition: W1 → W2 (graduated)

Day 38: Review Good → interval=14, count=1
Day 52: Review Good → interval=14, count=2
Day 66: Review Good → interval=14, count=3, good_streak=3 ✓
        → Graduate to M1! interval=30
        Transition: W2 → M1 (graduated)

Day 96:  Review Good → interval=30+3=33, count=1
Day 129: Review Good → interval=33+3=36, count=2
Day 165: Review Good → interval=36+3=39, count=3, good_streak=3 ✓
         → Graduate to FC! interval=60+
         Transition: M1 → FC (graduated)
```

### Scenario B: Struggle and Recovery

```
Day 0:   Item in FC, interval=45, peak_good=45

Day 50:  Review Bad (actual=50)
         base = (45+50)//2 = 47 (hedged, actual > scheduled*2)
         maintenance regression: lower=45//2=22
         result = (47+22)//2 = 34
         bad_streak=1

Day 84:  Review Bad (actual=34)
         base = 34
         maintenance regression: lower=45//2=22
         result = (34+22)//2 = 28
         bad_streak=2 → Demote to M1!
         demotion_interval = 34//2 = 17
         Transition: FC → M1 (demoted, {"bad_streak": 2})

Day 101: Review Good (actual=17)
         base = 17
         growth phase: 17*1.5 = 25
         good_streak=1, band_count=1

Day 126: Review Good (actual=25)
         base = 25
         growth phase: 25*1.5 = 37 → but >=30, so maintenance
         maintenance: 25+3 = 28
         good_streak=2, band_count=2

Day 154: Review Perfect (actual=28)
         base = 28
         growth phase: 28*2.0 = 56 → but >=30, so maintenance
         maintenance: 28+5 = 33
         good_streak=3 ✓ → Graduate to FC!
         recovery_boost: gap=45-33=12, boost=12*0.3=3.6
         final_interval = 33+4 = 37
         peak_good updated to 28
         Transition: M1 → FC (graduated)
```

### Scenario C: Late Review Success

```
Day 0:   Item in W2, interval=14

Day 45:  Review Good (actual=45, very late!)
         base = 45 (trusted: rating Good + actual > scheduled)
         maintenance phase (45 >= 30): 45+3 = 48
         peak_good updated to 45
         peak_interval_any updated to 45
         → Effectively jumped to M1/FC territory!
         Transition: W2 → M1 (graduated, early due to performance)
```

### Scenario D: Very Bad Cascade

```
Day 0:   Item in M1, interval=30

Day 32:  Review Very Bad (actual=32)
         base = 30 (VeryBad always uses scheduled)
         maintenance: lower=30//3=10, (30+10)//2 = 20
         Actually >=30, use growth: 30*0.3 = 9
         bad_streak=1

Day 41:  Review Bad (actual=9)
         base = 9
         growth phase: 9*0.5 = 4
         bad_streak=2 → Demote to D1!
         demotion_interval = max(1, 9//2) = 4
         Transition: M1 → D1 (demoted, {"bad_streak": 2})

Day 45:  Now rebuilding from D1 with interval=4
```

---

## Configuration

```python
# Interval bands
BANDS = {
    "NM": {"name": "New Memorization", "min": None, "max": None},
    "D1": {"name": "Daily", "min": 1, "max": 6, "target": 1, "reviews": 7, "next": "W1"},
    "W1": {"name": "Weekly", "min": 7, "max": 13, "target": 7, "reviews": 5, "next": "W2"},
    "W2": {"name": "Fortnightly", "min": 14, "max": 29, "target": 14, "reviews": 4, "next": "M1"},
    "M1": {"name": "Monthly", "min": 30, "max": 59, "target": 30, "reviews": 3, "next": "FC"},
    "FC": {"name": "Full Cycle", "min": 60, "max": None, "target": None, "reviews": None, "next": None},
}

# Phase threshold
PHASE_THRESHOLD = 30  # Below: multiplicative, at/above: additive

# Growth phase multipliers (interval < 30)
GROWTH_MULTIPLIERS = {2: 2.0, 1: 1.5, 0: 1.1, -1: 0.5, -2: 0.3}

# Maintenance phase additions (interval >= 30)
MAINTENANCE_ADDITIONS = {2: 5, 1: 3, 0: 1}  # -1, -2 use midpoint

# Recovery boost
RECOVERY_BOOST = 0.3  # Cover 30% of gap to peak

# Graduation thresholds
GOOD_STREAK_TO_GRADUATE = 3
```

---

## Migration Strategy

### Phase 1: Schema Changes

```sql
-- 0022-unified-interval-system.sql

-- 1. Add new columns to hafizs_items
ALTER TABLE hafizs_items ADD COLUMN peak_interval_good INTEGER;
ALTER TABLE hafizs_items ADD COLUMN peak_interval_any INTEGER;
ALTER TABLE hafizs_items ADD COLUMN band_review_count INTEGER DEFAULT 0;

-- 2. Rename interval columns for clarity
ALTER TABLE hafizs_items RENAME COLUMN next_interval TO interval;

-- 3. Add actual_interval to revisions
ALTER TABLE revisions ADD COLUMN actual_interval INTEGER;

-- 4. Create transitions table
CREATE TABLE transitions (
    id INTEGER PRIMARY KEY,
    hafiz_id INTEGER REFERENCES hafizs(id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
    transition_date TEXT,
    from_mode TEXT,
    to_mode TEXT,
    trigger TEXT,
    context TEXT
);

-- 5. Add new mode codes
INSERT INTO modes (code, name, description) VALUES
    ('W2', 'Fortnightly Reps', 'Review every 14 days'),
    ('M1', 'Monthly Reps', 'Review every 30 days');

-- 6. Update existing mode codes (DR→D1, WR→W1)
UPDATE hafizs_items SET mode_code = 'D1' WHERE mode_code = 'DR';
UPDATE hafizs_items SET mode_code = 'W1' WHERE mode_code = 'WR';
UPDATE revisions SET mode_code = 'D1' WHERE mode_code = 'DR';
UPDATE revisions SET mode_code = 'W1' WHERE mode_code = 'WR';
UPDATE modes SET code = 'D1', name = 'Daily' WHERE code = 'DR';
UPDATE modes SET code = 'W1', name = 'Weekly' WHERE code = 'WR';
```

### Phase 2: Backfill Data

```sql
-- Backfill actual_interval in revisions (from consecutive review dates)
WITH ordered_revisions AS (
    SELECT
        id,
        item_id,
        hafiz_id,
        review_date,
        LAG(review_date) OVER (
            PARTITION BY item_id, hafiz_id
            ORDER BY review_date, id
        ) as prev_date
    FROM revisions
)
UPDATE revisions
SET actual_interval = (
    SELECT CAST(JULIANDAY(revisions.review_date) - JULIANDAY(o.prev_date) AS INTEGER)
    FROM ordered_revisions o
    WHERE o.id = revisions.id AND o.prev_date IS NOT NULL
)
WHERE EXISTS (
    SELECT 1 FROM ordered_revisions o
    WHERE o.id = revisions.id AND o.prev_date IS NOT NULL
);

-- Backfill peak_interval_any
UPDATE hafizs_items
SET peak_interval_any = (
    SELECT MAX(actual_interval)
    FROM revisions
    WHERE revisions.item_id = hafizs_items.item_id
      AND revisions.hafiz_id = hafizs_items.hafiz_id
      AND revisions.actual_interval IS NOT NULL
);

-- Backfill peak_interval_good
UPDATE hafizs_items
SET peak_interval_good = (
    SELECT MAX(actual_interval)
    FROM revisions
    WHERE revisions.item_id = hafizs_items.item_id
      AND revisions.hafiz_id = hafizs_items.hafiz_id
      AND revisions.rating >= 1
      AND revisions.actual_interval IS NOT NULL
);
```

### Phase 3: Backfill Transitions

```sql
-- Create 'memorized' transitions from NM revisions
INSERT INTO transitions (hafiz_id, item_id, transition_date, from_mode, to_mode, trigger)
SELECT DISTINCT
    hafiz_id,
    item_id,
    MIN(review_date),
    NULL,
    'NM',
    'memorized'
FROM revisions
WHERE mode_code = 'NM'
GROUP BY hafiz_id, item_id;

-- Note: Mode change transitions would require analyzing consecutive
-- revisions with different mode_codes - complex query, can be done
-- in Python during migration script
```

### Phase 4: Code Changes

New algorithm applies to all new reviews. Existing scheduled intervals are honored until reviewed.

---

## Verification Queries

Before and after migration, verify SRS due items are unchanged:

```sql
-- Items due for review today (should be identical before/after)
SELECT item_id, interval, next_review, mode_code
FROM hafizs_items
WHERE next_review <= :current_date
  AND mode_code IN ('D1', 'W1', 'W2', 'M1', 'SR')
ORDER BY item_id;
```

---

## Removed/Deprecated

- `SRS_INTERVALS` (prime number list) - replaced by multipliers/additions
- `binary_search_less_than()` - no longer needed
- `get_interval_triplet()` - no longer needed
- `last_interval` column in hafizs_items - removed (was `prev_interval`)
- `SRS_MODE_CODE` ('SR') - items in intensive review are still in their band, just flagged
- Concept of "graduation from SRS" - items graduate through bands naturally

---

## Flexible Rep Mode Configuration (Dec 2025)

### Overview

Users can now configure custom repetition counts and starting modes for newly memorized pages. This allows flexible workflows like:
- Starting directly in Weekly mode (skipping Daily)
- Setting custom rep counts (e.g., 3 daily reps instead of 7)
- Setting different rep counts for each mode (e.g., 3 daily, 5 weekly, 0 fortnightly, 1 monthly)

### Database Changes

**Migration: 0024-add-custom-rep-thresholds.sql**

```sql
ALTER TABLE hafizs_items ADD COLUMN custom_daily_threshold INTEGER;
ALTER TABLE hafizs_items ADD COLUMN custom_weekly_threshold INTEGER;
ALTER TABLE hafizs_items ADD COLUMN custom_fortnightly_threshold INTEGER;
ALTER TABLE hafizs_items ADD COLUMN custom_monthly_threshold INTEGER;
```

These columns store per-item custom repetition thresholds. When NULL, the global default from `DEFAULT_REP_COUNTS` is used.

### Configuration Constants

**File: constants.py**

```python
DEFAULT_REP_COUNTS = {
    DAILY_REPS_MODE_CODE: 7,
    WEEKLY_REPS_MODE_CODE: 7,
    FORTNIGHTLY_REPS_MODE_CODE: 7,
    MONTHLY_REPS_MODE_CODE: 7,
}
```

### Threshold Priority

When determining the repetition threshold for graduation:

1. **Custom threshold** (from `custom_*_threshold` column) - highest priority
2. **DEFAULT_REP_COUNTS** - fallback if no custom threshold
3. **REP_MODES_CONFIG["threshold"]** - legacy fallback

### UI Components

**Rep Config Form** (`common_function.py:render_rep_config_form()`):
- Simple mode: Select starting mode + rep count for that mode
- Advanced mode: Set rep counts for all four modes
- Alpine.js-powered toggle between modes

**Profile Page** (`/profile/configure_reps/{hafiz_item_id}`):
- Modal to configure reps for individual items
- Accessible from profile/mode management

**New Memorization** (`/new_memorization/expand/{type}/{number}`):
- Rep config form shown when bulk-selecting pages
- Configuration applied to all selected items

### Example Workflows

**Standard (7-7-7-7)**:
```
Daily (7 reps) → Weekly (7 reps) → Fortnightly (7 reps) → Monthly (7 reps) → Full Cycle
```

**Accelerated (3-5-3-1)**:
```
Daily (3 reps) → Weekly (5 reps) → Fortnightly (3 reps) → Monthly (1 rep) → Full Cycle
```

**Skip Daily (0-7-7-7)**:
```
Weekly (7 reps) → Fortnightly (7 reps) → Monthly (7 reps) → Full Cycle
```

### API

**POST /profile/configure_reps**

Parameters:
- `hafiz_item_id` (or list): Items to configure
- `mode_code`: Target mode
- `rep_count`: Threshold for simple mode
- `rep_count_DR`, `rep_count_WR`, etc.: Thresholds for advanced mode

**POST /new_memorization/bulk_update_as_newly_memorized**

Additional parameters:
- `mode_code`: Starting mode (defaults to DAILY_REPS_MODE_CODE)
- `rep_count`: Custom threshold for starting mode
