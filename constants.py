# Mode Codes (2-character primary keys)
FULL_CYCLE_MODE_CODE = "FC"
NEW_MEMORIZATION_MODE_CODE = "NM"
DAILY_REPS_MODE_CODE = "DR"
WEEKLY_REPS_MODE_CODE = "WR"
SRS_MODE_CODE = "SR"

# Pagination configuration (applies to all modes)
ITEMS_PER_PAGE = 20  # Default page size (configurable per hafiz in settings)
FULL_CYCLE_EXTRA_ROWS = 5  # Extra rows added when Full Cycle limit is reached

RATING_MAP = {"1": "✅ Good", "0": "😄 Ok", "-1": "❌ Bad"}

# Default length for bulk revision entry (pages)
DEFAULT_REVISION_LENGTH = 20
