## SRS Recalculation Algorithm Summary - v1

**Purpose**: Rebuilds the complete interval history for a Quran page when users edit or delete review records, ensuring data consistency between individual revision records and global scheduling state.

**Core Problem**: When users modify historical review data (edit ratings or delete records), the stored intervals become inconsistent because they were calculated based on the original sequence that no longer exists.

**How It Works**:
1. **Fetches all revision records** for the current SRS period (filtered by `srs_start_date`)
2. **Starts fresh** with the booster pack's initial interval (e.g., 2 days)
3. **Replays history chronologically**, recalculating for each review:
   - `current_interval` = actual days between reviews
   - `last_interval` = what the gap was supposed to be
   - `next_interval` = new interval based on rating (good=forward, ok=stay, bad=backward)
4. **Updates both tables**:
   - Individual revision records with corrected intervals
   - Global `hafizs_items` table with final state for scheduling

**Key Features**:
- Preserves original review dates (historical accuracy)
- Handles multiple SRS periods (prevents mixing old/new sessions)
- Maintains proper sequence progression through predefined intervals
- Ensures scheduling consistency after any data modifications

**Result**: All interval data becomes mathematically consistent as if the current revision sequence had always existed from the beginning.