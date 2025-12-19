# Mode Codes (2-character primary keys)
FULL_CYCLE_MODE_CODE = "FC"
NEW_MEMORIZATION_MODE_CODE = "NM"
DAILY_REPS_MODE_CODE = "DR"
WEEKLY_REPS_MODE_CODE = "WR"
FORTNIGHTLY_REPS_MODE_CODE = "FR"
MONTHLY_REPS_MODE_CODE = "MR"
SRS_MODE_CODE = "SR"

# Pagination
ITEMS_PER_PAGE = 5
FULL_CYCLE_EXTRA_ROWS = 5  # Extra rows added when Full Cycle limit is reached

RATING_MAP = {"1": "✅ Good", "0": "😄 Ok", "-1": "❌ Bad"}

# Pagination configuration (applies to all modes)
ITEMS_PER_PAGE = 5

# Default length for bulk revision entry (pages)
DEFAULT_REVISION_LENGTH = 20

# Modes that support manual graduation (excludes FC, NM, SR which don't graduate manually)
GRADUATABLE_MODES = [
    DAILY_REPS_MODE_CODE,
    WEEKLY_REPS_MODE_CODE,
    FORTNIGHTLY_REPS_MODE_CODE,
    MONTHLY_REPS_MODE_CODE,
]

# Default repetition counts for each rep mode before graduation to next mode
DEFAULT_REP_COUNTS = {
    DAILY_REPS_MODE_CODE: 7,
    WEEKLY_REPS_MODE_CODE: 7,
    FORTNIGHTLY_REPS_MODE_CODE: 7,
    MONTHLY_REPS_MODE_CODE: 7,
}

# Status constants (derived from memorized + mode_code)
STATUS_NOT_MEMORIZED = "NOT_MEMORIZED"
STATUS_LEARNING = "LEARNING"
STATUS_REPS = "REPS"
STATUS_SOLID = "SOLID"
STATUS_STRUGGLING = "STRUGGLING"

# Status display: (icon, label)
STATUS_DISPLAY = {
    STATUS_NOT_MEMORIZED: ("📚", "Not Memorized"),
    STATUS_LEARNING: ("🌱", "Learning"),
    STATUS_REPS: ("🏋️", "Reps"),
    STATUS_SOLID: ("💪", "Solid"),
    STATUS_STRUGGLING: ("😰", "Struggling"),
}
