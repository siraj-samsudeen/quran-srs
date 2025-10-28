# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Quran SRS is a sophisticated Spaced Repetition System designed to help with Quran memorization and revision. It uses FastHTML as the web framework with SQLite database, focusing on tracking memorization progress across different modes (New Memorization, Daily, Weekly, Full Cycle, SRS). The application supports multi-user scenarios where a single account can manage multiple hafiz profiles (family/teaching contexts).

## Development Commands

### Python Environment
- **Run the application**: `uv run main.py` (NOT `python main.py`)
- **Install dependencies**: `uv sync`
- **Database**: SQLite database at `data/quran_v10.db` managed through fastmigrate with migrations in `migrations/` directory

### Testing
- **Base URL**: `http://localhost:5001` (configurable via BASE_URL env var)

### Frontend Assets
- **Tailwind CSS**: Configuration in `tailwind.config.js`
- **JavaScript**: Static files in `public/` directory (script.js)
- **Styles**: Custom CSS in `public/css/style.css`

## Architecture Overview

### Core Modes System
The application is built around 5 distinct memorization modes, each with different revision algorithms:

1. **New Memorization (mode_id=2)**: For learning completely new pages
2. **Daily Reps (mode_id=3)**: Daily repetition (1-day interval) after initial memorization
3. **Weekly Reps (mode_id=4)**: Weekly repetition (7-day interval) after daily graduation
4. **Full Cycle (mode_id=1)**: Sequential maintenance of all memorized content
5. **SRS Mode (mode_id=5)**: Adaptive spaced repetition for problematic pages

Mode IDs are defined as constants in `globals.py`: `NEW_MEMORIZATION_MODE_ID`, `DAILY_REPS_MODE_ID`, `WEEKLY_REPS_MODE_ID`, `FULL_CYCLE_MODE_ID`, `SRS_MODE_ID`.

### Mode Progression Flow
- **New Memorization** → **Daily Reps** (after first review)
- **Daily Reps** → **Weekly Reps** (after 7 reviews at 1-day intervals)
- **Weekly Reps** → **Full Cycle** (after 7 reviews at 7-day intervals)
- **Full Cycle** → **SRS Mode** (when bad_streak >= 1, triggered on date close)

### Authentication & Multi-User Architecture
The app uses a two-tier authentication system implemented via beforeware in `app/common_function.py`:

1. **User Level** (`user_auth`): Account owner authentication
   - Session key: `user_auth` (user_id)
   - Redirects to `/users/login` if not authenticated

2. **Hafiz Level** (`hafiz_auth`): Profile selection within account
   - Session key: `auth` (hafiz_id)
   - Redirects to `/users/hafiz_selection` if not selected
   - Automatically adds `hafiz_id` to database queries via `xtra()` for `revisions`, `hafizs_items`, and `plans` tables

This allows one account (parent/teacher) to manage multiple hafiz profiles (children/students).

### Database Schema Key Points

**Core Tables:**
- `items`: Quran content broken into items (full pages or page parts)
  - `page_id`: Page number (1-604)
  - `item_type`: "page" or "page-part"
  - `part`: Which part of page (e.g., "1", "2", "3" for multi-part pages)
  - `active`: Whether item is currently in use

- `hafizs_items`: Tracks each hafiz's progress per item
  - `mode_id`: Current mode (1-5)
  - `status_id`: Item status (1=memorized, 4=daily_reps, 5=srs, 6=not_memorized)
  - `next_review`, `next_interval`: For scheduled reviews
  - `last_interval`: Actual days since last review
  - `bad_streak`, `good_streak`: Performance tracking
  - `srs_booster_pack_id`: Links to SRS configuration when in SRS mode

- `revisions`: Individual review records
  - `item_id`, `hafiz_id`, `mode_id`, `revision_date`
  - `rating`: -1 (Bad), 0 (Ok), 1 (Good)
  - `next_interval`: Calculated interval for SRS reviews
  - `plan_id`: Groups revisions into cycles (for Full Cycle mode)

- `plans`: Defines Full Cycle revision plans
  - `hafiz_id`, `start_page`, `completed`
  - Used to track progress through complete Quran cycles

**Critical Relationships:**
- One hafiz has many `hafizs_items` (one per Quran item)
- One item can have many `revisions` across different modes and dates
- Revisions in Full Cycle mode link to `plans` via `plan_id`

### Key Business Logic

**Date Management:**
Each hafiz has a `current_date` field that acts as the "system date" for that profile. This allows:
- Independent timelines for different hafiz profiles
- Testing and demo scenarios
- Review of past data without affecting current progress

The "Close Date" operation (main.py:716-745) is critical:
1. Processes all reviews for the current date
2. Updates `hafizs_items` based on mode-specific logic
3. Triggers SRS mode for items with bad streaks
4. Advances the hafiz's `current_date` by one day

**Mode-Specific Update Logic:**
- **Full Cycle**: Updates `last_interval` based on actual days, moves SRS items' `next_review` forward (main.py:695-707)
- **New Memorization**: Promotes to Daily Reps mode on close (main.py:709-714)
- **Daily/Weekly Reps**: Handled by `update_rep_item()` in `app/fixed_reps.py` - counts reviews and graduates to next mode after threshold
- **SRS**: Handled by `update_hafiz_item_for_srs()` in `app/srs_reps.py` - calculates next interval using booster pack algorithm, graduates to Full Cycle when complete

**Display Count Logic:**
Full Cycle mode shows a dynamic number of items on the home page (main.py:546-577):
- Base count: `get_display_count(auth)` (based on hafiz's capacity)
- Additional count: Session-stored extra pages (`full_cycle_display_count`)
- Users can add +1, +2, +3, +5 pages via buttons to see more suggestions

### File Structure

**Main Application:**
- `main.py`: Main app initialization, home page route with all summary tables, Close Date logic
- `globals.py`: Database setup, mode constants, table references
- `utils.py`: Helper functions for dates, formatting, list operations

**App Modules (mounted as sub-apps):**
- `app/users_controller.py`: User authentication routes
- `app/revision.py`: Revision CRUD operations and bulk operations
- `app/new_memorization.py`: New memorization workflow
- `app/profile.py`: Hafiz profile management
- `app/hafiz.py`: Hafiz-specific settings (capacity, current_date override)
- `app/admin.py`: Admin utilities and database management
- `app/page_details.py`: Detailed item/page information views
- `app/common_function.py`: Shared utilities (authentication, rendering helpers, data fetching)
- `app/revision_model.py`: Data access layer for revisions
- `app/fixed_reps.py`: Daily/Weekly Reps logic with `REP_MODES_CONFIG`
- `app/srs_reps.py`: SRS mode logic including interval calculations

**Supporting Files:**
- `docs/design.md`: Comprehensive design vision through user conversations
- `docs/data_model.md`: Database schema documentation
- `docs/srs-mode-design.md`: SRS algorithm specifications

### Common Development Patterns

**Adding/Removing Revisions:**
Use `add_revision_record()` and `remove_revision_record()` from `app/common_function.py`. These handle both database operations and hafizs_items stat updates.

**Rendering Summary Tables:**
The `make_summary_table()` function (app/common_function.py) generates mode-specific review tables with checkboxes for bulk operations. It handles:
- Item filtering by mode and date
- Checkbox states for already-reviewed items
- Rating dropdowns
- Shift-click multi-select via Alpine.js

**Database Queries:**
- Use table objects from `globals.py` (e.g., `revisions()`, `hafizs_items()`)
- For complex queries, use `db.q()` with raw SQL
- Always include `hafiz_id` filters (automatically added by `xtra()` when using beforeware)

**Page References:**
Items can represent full pages or page parts (e.g., page 5 might have items for "5.1", "5.2", "5.3"). Use `get_page_description()` to render human-readable descriptions.
