# Mode Codes (2-character primary keys)
FULL_CYCLE_MODE_CODE = "FC"
NEW_MEMORIZATION_MODE_CODE = "NM"
DAILY_REPS_MODE_CODE = "DR"
WEEKLY_REPS_MODE_CODE = "WR"
FORTNIGHTLY_REPS_MODE_CODE = "FR"
MONTHLY_REPS_MODE_CODE = "MR"
SRS_MODE_CODE = "SR"

RATING_MAP = {"1": "✅ Good", "0": "😄 Ok", "-1": "❌ Bad"}

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

# Rating colors for Tabulator row backgrounds
RATING_COLORS = {
    "1": "#dcfce7",   # green-100 for Good
    "0": "#fef9c3",   # yellow-100 for Ok
    "-1": "#fee2e2",  # red-100 for Bad
}

# SRS exclusion zone: pages ahead of current Full Cycle position to exclude from SRS
# (~3 days at 20 pages/day)
SRS_EXCLUSION_ZONE_PAGES = 60

# Tabulator configuration
TABULATOR_INIT_DELAY_MS = 100
TABULATOR_MOBILE_BREAKPOINT_PX = 768
TABULATOR_PAGE_SIZE_MOBILE = 5
TABULATOR_PAGE_SIZE_DESKTOP = 10
TABULATOR_PAGE_SIZES = [5, 10, 25, 50, 100]
