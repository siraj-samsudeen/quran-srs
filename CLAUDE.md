# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Quran SRS is a sophisticated Spaced Repetition System designed to help with Quran memorization and revision. It uses FastHTML as the web framework with SQLite database, focusing on tracking memorization progress across different modes (New Memorization, Daily, Weekly, Full Cycle, SRS). The application supports multi-user scenarios where a single account can manage multiple hafiz profiles (family/teaching contexts).

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

**main.py** (6,116 lines): Primary FastHTML application containing:
- Database setup and table definitions using fastmigrate
- Core business logic for all memorization modes
- Route handlers for all web endpoints except authentication
- Uses MonsterUI for enhanced UI components

**users.py**: Separate authentication module with self-contained FastHTML app:
- Login/logout functionality with session management
- Hafiz selection and management
- URL namespace with /users/ prefix (e.g., /users/login, /users/hafiz_selection)
- Direct database connections independent of main.py

**utils.py**: Utility functions and core algorithms:
- Date handling and Islamic calendar utilities
- SRS (Spaced Repetition System) algorithms
- Database migration management via `create_and_migrate_db()`

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

1. `/users/login` - User authentication (handled in users.py)
2. `/users/hafiz_selection` - Choose which hafiz account to manage (handled in users.py)
3. Main application routes require both user_auth and auth sessions
4. Two-tier authentication: `user_auth` (account login) → `auth` (hafiz selection)
5. Session middleware at `main.py:94-100` handles redirects for unauthenticated access

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

### Module Organization
1. **Authentication routes**: Add to `users.py` with /users/ URL prefix
2. **Core application routes**: Add to `main.py` 
3. **Database changes**: Create new sequential migration files in `migrations/` directory
4. **Utility functions**: Add to `utils.py`
5. **Static assets**: Place in `public/` directory
6. **Tests**: Focus on critical user workflows (memorization, revision, data import)

### Database Migration Pattern
- Migrations are numbered sequentially (0001-0012 currently)
- Each migration file contains SQL DDL statements
- Migration system runs automatically via `utils.py:create_and_migrate_db()`
- Never modify existing migration files - always create new ones

## Key Files to Understand

- `main.py:94-100` - Authentication middleware for session handling
- `main.py:21-27` - Database connection and table setup
- `users.py:38` - Self-contained FastHTML app for authentication: `users_app, rt = fast_app()`
- `users.py:40-66` - Login route handlers with proper FastHTML patterns
- `docs/data_model.md` - Complete database schema documentation
- `utils.py:15-27` - Database migration handling
- `migrations/` - Database schema evolution history (sequential numbered files)

## Important Development Notes

### FastHTML Architecture Patterns
- Main app in `main.py` handles core functionality
- Authentication module `users.py` uses separate FastHTML app instance
- URL namespacing prevents route conflicts (/users/ prefix for auth routes)
- Database connections are established independently in each module

### Testing Approach
- Playwright configured for Chrome-only testing via `playwright.config.ts`
- Authentication tests use natural testing patterns (not Gherkin/BDD format)
- Tests cover two-tier authentication flow (user login → hafiz selection)
- Current test files: `tests/users.spec.ts`, `tests/login.spec.ts`