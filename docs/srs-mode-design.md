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
- mode_id: 5 = SRS mode, 1 = Full Cycle mode
- status_id: 5 = SRS active, 6 = Not started
- srs_start_date: When item entered SRS (e.g., '2025-07-09')
- srs_booster_pack_id: Which pack to use (typically 1 = Standard)
- last_review: Date of most recent SRS review
- next_review: When item is due for next SRS review
- last_interval: Previous interval used
- current_interval: Days since last review based on the current_date in the hafiz table
- next_interval: Days to add for next review (NULL = graduated)

### 3. revisions TABLE (review history):
- mode_id: 5 = SRS review, 1 = Full Cycle review
- rating: -1=bad, 0=ok, 1=good
- last_interval: The interval position used to calculate this review (from algorithm state)
- current_interval: Actual days between previous review and this review date
- next_interval: Calculated interval for next review based on this rating

## SRS Lifecycle Events

### EVENT 1: PAGE ENTERS SRS MODE
**What triggers:** EITHER 2 consecutive bad ratings in full-cycle mode, OR user manually adds to SRS

**Note:** SRS feature was implemented starting July 9, 2025 (earliest SRS revision date)

**Database changes in hafizs_items:**
- mode_id = 5 (SRS mode)
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
- mode_id = 1 (returns to Full Cycle mode)
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
- Page 64 reviewed in Full Cycle mode (mode_id=1) while still in SRS
- SRS schedule: Due 2025-08-12 (next day)
- Full Cycle review recorded normally without affecting SRS state

**Key Behaviors:**
1. **SRS State Preserved:** Page remains in SRS mode with next_review=2025-08-12
2. **No SRS Progression:** Full Cycle review doesn't advance SRS intervals
3. **Dual Mode Operation:** Same page can be active in both systems simultaneously
4. **Independent Tracking:** Each mode maintains separate revision history

**Technical Implementation:** The system differentiates reviews by mode_id (1=Full Cycle, 5=SRS) allowing parallel operation without interference. This flexibility lets users review SRS pages in regular sequential order when desired while maintaining their SRS schedule.

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