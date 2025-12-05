"""
Pure SRS Interval Calculation Functions

This module contains pure functions for calculating SRS intervals.
All functions take primitive values (int, float) and return primitives.
No database access - these are easily unit testable.

Why We Moved From Prime Numbers to Streak-Based Intervals
=========================================================

The previous algorithm used prime number sequences [2, 3, 5, 7, 11, 13, ...] for
interval progression. While mathematically elegant, it had practical problems:

1. **Hard to tune**: Prime jumps are fixed (7→11 is +4, but 11→13 is only +2).
   You can't adjust growth rates for different phases of memorization.

2. **Unintuitive**: Users couldn't predict when items would appear next.
   "Why did my interval jump from 11 to 13?" has no satisfying answer beyond
   "because 13 is the next prime."

3. **Bad rating handling**: Dividing by penalties (35% of actual interval) then
   looking up in the prime sequence created inconsistent behavior.

4. **No phase awareness**: The same prime sequence applied whether you were at
   7 days (still building) or 50 days (long-term retention).

The New Streak-Based Algorithm
==============================

The new algorithm uses simple arithmetic with phase-aware multipliers:

**Formula:**
- Good: interval + (streak × phase_multiplier)
- Ok: interval + phase_increment, capped at 40
- Bad: interval ÷ (streak + 1), or drop to 30 if already past 30

**Key Design Decisions:**

1. **40-day threshold**: Based on observation that degradation typically starts
   around 40 days. Ok ratings cap here; only Good can push beyond.

2. **30-day floor for Bad**: Any Bad rating at 30+ drops to 30. This brings
   struggling items back to the "ideal zone" (30-40 days) for focused work.

3. **Streak-based progression**: Rewards consistency. Multiple consecutive Good
   ratings accelerate growth; multiple Bad ratings accelerate reduction.

4. **Graduation by streak, not interval**: 3 consecutive Good ratings = mastery.
   This is more meaningful than "interval > 99 days" because it shows the user
   actually remembers the content consistently.

5. **Phase-aware growth rates**:
   - 0-14 days: Fast growth (×2 multiplier) - building initial retention
   - 14-30 days: Moderate (×1.5) - strengthening
   - 30-40 days: Slow (×1) - ideal zone, careful maintenance
   - 40+ days: Very slow (+3 fixed) - long-term, minimal growth

Late/Early Review Handling
==========================

- **Late + Good**: Full credit for the gap (100%). If you remembered after a
  longer gap, you deserve the full benefit.

- **Late + Ok/Bad**: Partial credit (50%/25%). We don't know if the poor rating
  was due to the delay or genuine difficulty.

- **Early + Good (FC overlap)**: Just reschedule, don't recalculate. This
  happens when an SRS item comes up during Full Cycle before its due date.
  A Good rating there is a "freebie" - we push the schedule forward.

- **Early + Ok/Bad**: Recalculate using planned interval. Something is wrong
  if you're struggling even before the scheduled date.
"""

from typing import Optional

# =============================================================================
# CONFIGURATION - All tunables in one place
# =============================================================================

# Phase-based configuration for interval progression
# Each phase has different growth rates to handle different memorization stages
SRS_PHASE_CONFIG = {
    # Phase 1 (0-14 days): Building phase - faster growth
    # - Good: interval + (streak × 2)
    # - Ok: interval + 2
    (0, 14): {"good_multiplier": 2.0, "ok_increment": 2},

    # Phase 2 (14-30 days): Strengthening phase - moderate growth
    # - Good: interval + (streak × 1.5)
    # - Ok: interval + 1
    (14, 30): {"good_multiplier": 1.5, "ok_increment": 1},

    # Phase 3 (30-40 days): Ideal zone - slow growth, stable retention
    # - Good: interval + (streak × 1)
    # - Ok: stay same (no increment)
    (30, 40): {"good_multiplier": 1.0, "ok_increment": 0},

    # Phase 4 (40+ days): Long-term - very slow fixed growth
    # - Good: interval + 3 (fixed, not streak-based)
    # - Ok: capped at 40
    (40, 999): {"good_increment": 3, "ok_increment": 0},
}

# Starting intervals when entering SRS mode from Full Cycle
SRS_START_INTERVAL = {
    -1: 3,   # Bad rating -> 3-day interval
    0: 10,   # Ok rating -> 10-day interval
}

# Graduation: exit SRS back to Full Cycle after N consecutive Good ratings
SRS_GRADUATION_STREAK = 3

# Minimum interval (prevents items bouncing back next day)
SRS_MIN_INTERVAL = 3

# Ok rating can never push interval above this value
SRS_OK_CAP = 40

# Bad rating at or above this interval drops to this floor
SRS_BAD_FLOOR = 30

# Late review credit percentages (how much of the "gap" to credit)
LATE_REVIEW_CREDIT = {
    1: 1.0,    # Good: 100% credit for late gap
    0: 0.5,    # Ok: 50% credit
    -1: 0.25,  # Bad: 25% credit
}


# =============================================================================
# PURE CALCULATION FUNCTIONS
# =============================================================================

def get_phase_config(interval: int) -> dict:
    """
    Get the phase configuration for a given interval.

    Args:
        interval: Current interval in days

    Returns:
        Dict with phase-specific config (good_multiplier or good_increment, ok_increment)

    Example:
        >>> get_phase_config(10)
        {"good_multiplier": 2.0, "ok_increment": 2}
        >>> get_phase_config(45)
        {"good_increment": 3, "ok_increment": 0}
    """
    for (min_val, max_val), config in SRS_PHASE_CONFIG.items():
        if min_val <= interval < max_val:
            return config
    # Fallback for any interval >= 999 (shouldn't happen)
    return {"good_increment": 3, "ok_increment": 0}


def get_base_interval(planned: int, actual: int, rating: int) -> Optional[int]:
    """
    Calculate the base interval accounting for early/late reviews.

    Args:
        planned: The planned interval (what was scheduled)
        actual: The actual interval (days since last review)
        rating: -1 (Bad), 0 (Ok), or 1 (Good)

    Returns:
        - None if early + Good (signals reschedule-only, no recalculation)
        - planned if early + Ok/Bad
        - Adjusted interval if late (planned + credit * gap)

    Example:
        >>> get_base_interval(10, 20, 1)   # Late + Good: full credit
        20
        >>> get_base_interval(10, 20, 0)   # Late + Ok: 50% credit
        15
        >>> get_base_interval(10, 7, 1)    # Early + Good: reschedule only
        None
        >>> get_base_interval(10, 7, 0)    # Early + Ok: use planned
        10
    """
    if actual < planned:
        # Early review (strictly before due date)
        if rating == 1:  # Good
            return None  # Signal: reschedule only, don't recalculate
        return planned   # Ok/Bad: use planned as base

    if actual == planned:
        # On-time review: use planned as base for all ratings
        return planned

    # Late review (actual > planned)
    gap = actual - planned
    credit = LATE_REVIEW_CREDIT.get(rating, 0.5)
    return planned + int(gap * credit)


def calculate_good_interval(base: int, good_streak: int) -> int:
    """
    Calculate next interval for Good rating.

    Args:
        base: Base interval to build upon
        good_streak: Current consecutive Good streak

    Returns:
        New interval after Good rating

    Example:
        >>> calculate_good_interval(7, 2)   # Phase 1: 7 + (2 × 2) = 11
        11
        >>> calculate_good_interval(20, 2)  # Phase 2: 20 + (2 × 1.5) = 23
        23
        >>> calculate_good_interval(35, 2)  # Phase 3: 35 + (2 × 1) = 37
        37
        >>> calculate_good_interval(45, 3)  # Phase 4: 45 + 3 = 48 (fixed)
        48
    """
    config = get_phase_config(base)

    if "good_increment" in config:
        # Phase 4: fixed increment, not streak-based
        return base + config["good_increment"]
    else:
        # Phases 1-3: streak × multiplier
        multiplier = config["good_multiplier"]
        return base + int(good_streak * multiplier)


def calculate_ok_interval(base: int) -> int:
    """
    Calculate next interval for Ok rating.

    Args:
        base: Base interval to build upon

    Returns:
        New interval after Ok rating, capped at SRS_OK_CAP (40)

    Example:
        >>> calculate_ok_interval(7)   # Phase 1: 7 + 2 = 9
        9
        >>> calculate_ok_interval(20)  # Phase 2: 20 + 1 = 21
        21
        >>> calculate_ok_interval(35)  # Phase 3: 35 + 0 = 35 (stay)
        35
        >>> calculate_ok_interval(45)  # Phase 4: cap at 40
        40
    """
    config = get_phase_config(base)
    new_interval = base + config["ok_increment"]

    # Ok can never exceed the cap
    return min(new_interval, SRS_OK_CAP)


def calculate_bad_interval(base: int, bad_streak: int) -> int:
    """
    Calculate next interval for Bad rating.

    Args:
        base: Base interval to build upon
        bad_streak: Current consecutive Bad streak (1 = first bad)

    Returns:
        New interval after Bad rating:
        - Under 30: base ÷ (streak + 1), minimum SRS_MIN_INTERVAL
        - 30+: drops to SRS_BAD_FLOOR (30)

    Example:
        >>> calculate_bad_interval(10, 1)  # 10 ÷ 2 = 5
        5
        >>> calculate_bad_interval(21, 2)  # 21 ÷ 3 = 7
        7
        >>> calculate_bad_interval(4, 1)   # 4 ÷ 2 = 2 → min 3
        3
        >>> calculate_bad_interval(35, 1)  # 30+ zone: drop to 30
        30
        >>> calculate_bad_interval(50, 2)  # 30+ zone: drop to 30
        30
    """
    if base >= SRS_BAD_FLOOR:
        # At or above the floor: always drop to floor
        return SRS_BAD_FLOOR

    # Under the floor: divide by (streak + 1)
    divisor = bad_streak + 1
    new_interval = base // divisor

    # Enforce minimum
    return max(new_interval, SRS_MIN_INTERVAL)


def calculate_next_interval(
    base: int,
    rating: int,
    good_streak: int,
    bad_streak: int
) -> int:
    """
    Main calculation: determine next SRS interval based on rating and streaks.

    Args:
        base: Base interval (from get_base_interval, accounting for early/late)
        rating: -1 (Bad), 0 (Ok), or 1 (Good)
        good_streak: Current consecutive Good streak
        bad_streak: Current consecutive Bad streak

    Returns:
        Next interval in days

    Example:
        >>> calculate_next_interval(10, 1, 2, 0)   # Good, streak 2, phase 1
        14
        >>> calculate_next_interval(20, 0, 0, 0)   # Ok, phase 2
        21
        >>> calculate_next_interval(35, -1, 0, 1)  # Bad, 30+ zone
        30
    """
    if rating == 1:  # Good
        return calculate_good_interval(base, good_streak)
    elif rating == 0:  # Ok
        return calculate_ok_interval(base)
    else:  # Bad (-1)
        return calculate_bad_interval(base, bad_streak)


def should_graduate(good_streak: int) -> bool:
    """
    Check if item should graduate from SRS back to Full Cycle.

    Args:
        good_streak: Current consecutive Good streak

    Returns:
        True if streak >= graduation threshold

    Example:
        >>> should_graduate(2)
        False
        >>> should_graduate(3)
        True
    """
    return good_streak >= SRS_GRADUATION_STREAK


def should_reschedule_only(actual: int, planned: int, rating: int) -> bool:
    """
    Check if this is an early Good review that should just reschedule.

    Args:
        actual: Actual days since last review
        planned: Planned interval
        rating: -1, 0, or 1

    Returns:
        True if early + Good (reschedule without recalculating interval)

    Example:
        >>> should_reschedule_only(7, 10, 1)   # Early + Good
        True
        >>> should_reschedule_only(10, 10, 1)  # On-time + Good
        False
        >>> should_reschedule_only(7, 10, 0)   # Early + Ok
        False
    """
    return actual < planned and rating == 1
