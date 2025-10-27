# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Quran SRS is a sophisticated Spaced Repetition System designed to help with Quran memorization and revision. It uses FastHTML as the web framework with SQLite database, focusing on tracking memorization progress across different modes (New Memorization, Daily, Weekly, Full Cycle, SRS). The application supports multi-user scenarios where a single account can manage multiple hafiz profiles (family/teaching contexts).

## Development Commands

### Python Environment
- **Run the application**: `uv run main.py` (NOT `python main.py`)
- **Install dependencies**: `uv sync` (if using uv)
- **Database**: SQLite database managed through fastmigrate with migrations in `migrations/` directory

### Testing
- **Run Playwright tests**: `npx playwright test` and use only chrome browser to test
- **Run specific test**: `npx playwright test tests/quran_srs-test.spec.ts`
- **Show test report**: `npx playwright show-report`

### Frontend Assets
- **Tailwind CSS**: Configuration in `tailwind.config.js` (minimal setup)
- **JavaScript**: Static files in `public/` directory (script.js)

[... rest of the existing content remains unchanged ...]