# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Quran SRS is a Spaced Repetition System designed to help with Quran memorization and revision. It uses FastHTML as the web framework with SQLite database, focusing on tracking memorization progress across different modes (New Memorization, Daily, Weekly, Full Cycle, SRS).

## Development Commands

### Python Environment
- **Run the application**: `python main.py`
- **Install dependencies**: `uv sync` (if using uv)
- **Database**: SQLite database managed through fastmigrate with migrations in `migrations/` directory

### Testing
- **Run Playwright tests**: `npx playwright test` and use only chrome browser to test
- **Run specific test**: `npx playwright test tests/quran_srs-test.spec.ts`
- **Show test report**: `npx playwright show-report`

### Frontend Assets
- **Tailwind CSS**: Configuration in `tailwind.config.js` (minimal setup)
- **JavaScript**: Static files in `public/` directory (script.js, recent_review_logic.js, watch_list_logic.js)

## Architecture

### Core Components

**main.py**: Main FastHTML application file containing:
- Database setup and table definitions using fastmigrate
- Authentication system with user sessions
- Route handlers for all web endpoints
- Uses MonsterUI for enhanced UI components

**Database Schema** (see `docs/data_model.md` for full details):
- **User Management**: `users`, `hafizs`, `hafizs_users` (many-to-many relationship)
- **Quran Structure**: `mushafs`, `surahs`, `pages`, `items`
- **Revision Tracking**: `revisions`, `modes`, `hafizs_items`, `statuses`, `full_cycles`
- **SRS Features**: `srs_booster_pack` for spaced repetition algorithm

### Key Concepts

1. **Multi-User Support**: Users can manage multiple hafiz accounts (family/teaching scenarios)
2. **Flexible Item Types**: Supports page, page-part, and surah-based memorization units
3. **Multiple Modes**: New Memorization, Daily, Weekly, Full Cycle, SRS with different revision algorithms
4. **Rating System**: Good (1), Ok (0), Bad (-1) ratings track memorization strength
5. **Status Tracking**: Strong, Weakened, Forgotten, Not Memorized, New Memorization, Tough Page

### Database Management

- **Migrations**: Located in `migrations/` directory, numbered sequentially (0001-0012)
- **Migration System**: Uses fastmigrate for database versioning
- **Database Path**: `data/quran_v10.db` (SQLite) - this is a copy from production for local testing purposes
- **Table Creation**: Handled automatically in `utils.py:create_and_migrate_db()`

### Authentication Flow

1. `/login` - User authentication
2. `/hafiz_selection` - Choose which hafiz account to manage
3. Main application routes require both user_auth and auth sessions

### Frontend Architecture

- **FastHTML**: Server-side rendering with reactive components
- **MonsterUI**: Enhanced UI component library
- **Alpine.js & Hyperscript**: Client-side interactivity
- **Tailwind CSS**: Utility-first styling (minimal configuration)

## Testing

- **Framework**: Playwright for end-to-end testing
- **Test Files**: Located in `tests/` directory
- **Test Data**: CSV files for import testing (mode_import_for_test.csv, incorrect_mode_for_test.csv)
- **Browser Support**: Chromium, Firefox, WebKit configured

## Development Workflow

1. Database changes require new migration files in `migrations/`
2. Main application logic goes in `main.py`
3. Utility functions in `utils.py`
4. Static assets in `public/`
5. Tests should cover critical user workflows (memorization, revision, data import)

## Key Files to Understand

- `main.py:94-100` - Authentication middleware
- `main.py:21-27` - Database connection and table setup
- `docs/data_model.md` - Complete database schema documentation
- `utils.py:15-27` - Database migration handling
- `migrations/` - Database schema evolution history