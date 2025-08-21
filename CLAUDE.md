# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## PROJECT MIGRATION CONTEXT

**CRITICAL: This repository is undergoing active migration from FastHTML to Phoenix while maintaining production FastHTML system.**

### Current Status
- **Master Branch**: FastHTML production code (requires occasional bug fixes)  
- **Phoenix-migration Branch**: Phoenix migration development (this branch)
- **Migration Goal**: Replace FastHTML with Phoenix while preserving all functionality
- **URL Continuity**: All GitHub URLs, stars, bookmarks must remain valid throughout migration

### Repository Evolution Path
1. **Django** (legacy) → **FastHTML** (current prod) → **Phoenix** (target)
2. All previous code has been overwritten in-place to maintain URL continuity
3. Git history preserves the complete evolution story

## PROJECT OVERVIEW

Quran SRS is a sophisticated Spaced Repetition System designed to help with Quran memorization and revision. The system tracks memorization progress across different modes and supports multi-user scenarios where a single account can manage multiple hafiz profiles (family/teaching contexts).

### Core Features
- **Multiple Memorization Modes**: Daily Reps, Weekly Reps, Fortnightly Reps, Monthly Reps, Full Cycle, New Memorization, Adaptive Reps
- **Multi-User Support**: Single account managing multiple hafiz profiles
- **Granular Tracking**: Page-level and line-level memorization units  
- **Spaced Repetition**: Adaptive scheduling based on performance
- **Multi-Mushaf Support**: Support for different Quran editions (Hafs, Warsh, etc.)

## DEVELOPMENT PRACTICES

### Critical Workflow Requirements (ESSENTIAL for all projects)

**Commit Process:**
1. **ALWAYS stage files first** - Never commit without user review
2. **Ask for approval** - Present staged files and wait for explicit "commit" command  
3. **Atomic commits** - One task at a time, test each change, commit, then next step

**Commit Message Format:**

Based on [Conventional Commits](https://www.conventionalcommits.org/) and [How to Write a Git Commit Message](https://cbea.ms/git-commit/):

```
<type>: <imperative subject line - max 50 chars>

[optional body wrapped at 72 chars explaining why, not how]

[optional footer for breaking changes or references]
```

**Commit Types:**
- `feature:` New functionality (not feat)
- `fix:` Bug fixes
- `refactor:` Code changes that neither fix bugs nor add features
- `docs:` Documentation only changes
- `test:` Adding or updating tests
- `chore:` Maintenance tasks (dependencies, config, etc.)
- `style:` Code formatting, whitespace, etc.
- `migration:` Specific to Phoenix migration work

**Commit Message Rules:**
1. Capitalize the subject line
2. Don't end subject with a period
3. Use imperative mood ("Add feature" not "Added feature")
4. Subject completes: "If applied, this commit will ___"
5. Body explains what and why, not how
6. Reference issues and PRs in footer when applicable

**Plan Structure:**
- **plan.md**: Simple todo list for coordination and task tracking
- **changelog.md**: Document actual changes as they happen (Keep a Changelog format)
- **data_model.md**: Living documentation written as Phoenix schema is implemented
- **vision.md**: Long-term system architecture and philosophy

**Changelog Workflow:**
- Update changelog AFTER commits are made, not before
- Document noteworthy changes that impact users/developers
- Group related commits into meaningful entries
- Focus on business impact, not just technical details

**Task Execution Pattern:**
1. Small step → Do → Test → Update plan & details → Commit
2. Use TodoWrite tool frequently for task tracking and progress visibility
3. Mark todos complete immediately after finishing (don't batch)
4. Only one task in_progress at a time

### Branch Management Strategy
- **Master branch**: Keep stable for production hotfixes when needed
- **Phoenix branch**: Clean development environment for Phoenix implementation  
- **Final switchover**: When Phoenix is production-ready, merge/replace master

## PHOENIX MIGRATION

### Current Migration Status
**Phase: Ready to Create Phoenix Application**

### Key Migration Files
- **`docs/plan.md`** - Simple todo list for Phoenix migration steps
- **`docs/vision.md`** - Complete system philosophy and architecture
- **`docs/changelog.md`** - Historical context and future changes
- **`docs/data_model.md`** - Living documentation of actual Phoenix schema (empty, to be written)
- **`data/seeds.exs`** + **`data/seeds/`** - CSV seed data ready for Phoenix import
- **`docs/temp-notes.md`** - Temporary implementation notes (gitignored)

### Database Schema Decisions

**Mode Codes (2-Character Primary Keys)**
- Uses 2-character string codes instead of integer IDs for storage efficiency and readability
- Codes: `DR` (Daily Reps), `WR` (Weekly Reps), `FR` (Fortnightly Reps), `MR` (Monthly Reps), `FC` (Full Cycle), `NM` (New Memorization), `AR` (Adaptive Reps)

**Data Normalization**
- Removed redundant fields: `items.surah_name` (accessible via FK), `pages.starting_verse/ending_verse` (all NULL)
- Kept essential FKs: `pages.mushaf_id` (multi-mushaf support), `items.page_id` (multiple items per page)
- **CRITICAL**: `items.start_text ≠ pages.start_text` - items represent specific memorization units within pages

**Multi-Mushaf Support**
- Structure: `mushafs (1) → pages (604) → items (836)`
- Future support for different Quran editions (Hafs, Warsh, etc.)

### Development Commands

**Phoenix Development (when Phoenix app exists):**
- **Create database**: `mix ecto.create`
- **Run migrations**: `mix ecto.migrate`
- **Generate LiveViews**: `mix phx.gen.live Context Schema table field:type`
- **Run server**: `mix phx.server`
- **Run tests**: `mix test`
- **Interactive shell**: `iex -S mix`
- **Reset database**: `mix ecto.drop && mix ecto.create && mix ecto.migrate`

**Seed Data:**
- **Location**: CSV files in `data/seeds/` + import script `data/seeds.exs`  
- **Import master data**: `mix run priv/repo/seeds.exs` (requires CSV dependency: `{:csv, "~> 3.0"}`)

### Database Management
- **Phoenix**: SQLite for development (matching FastHTML), PostgreSQL for production
- **Connection**: Database files in `data/` directory (preserved from FastHTML)
- **Migrations**: Phoenix migrations in `priv/repo/migrations/`
- **Seeds**: CSV files in `priv/repo/seeds/` + import script `priv/repo/seeds.exs`

## FASTHTML LEGACY (Production System)

### FastHTML Commands (for production bug fixes)
- **Run application**: `uv run main.py` (NOT `python main.py`)
- **Install dependencies**: `uv sync`
- **Database**: SQLite with fastmigrate migrations in `migrations/` directory

### Testing (FastHTML)
- **Run Playwright tests**: `npx playwright test` (chrome browser only)
- **Run specific test**: `npx playwright test tests/quran_srs-test.spec.ts`
- **Show test report**: `npx playwright show-report`

### Frontend Assets (FastHTML)
- **Tailwind CSS**: Configuration in `tailwind.config.js`
- **JavaScript**: Static files in `public/` directory

## DATA MODEL

### Core Tables
- **mushafs** - Quran editions (primary key: id)
- **surahs** - Quran chapters (114 total)  
- **pages** - Quran pages (604 total, references mushaf)
- **items** - Memorization units (836 total, can be page parts/lines)
- **modes** - Memorization modes (primary key: 2-char code)
- **statuses** - Memorization status types
- **users** - User accounts
- **hafizs** - Memorization profiles (many per user)
- **hafizs_items** - Tracks memorization progress per hafiz+item
- **revisions** - Review history (high volume table)
- **plans** - Full cycle plans

### Key Relationships
- Multi-user: `users (1) → hafizs (many)`
- Multi-mushaf: `mushafs (1) → pages (many) → items (many)`
- Progress tracking: `hafizs (1) → hafizs_items (many) ← items (1)`
- Review history: `hafizs_items (1) → revisions (many)`

## IMPORTANT REMINDERS

### Migration Context
- **Always remember**: This is a FastHTML → Phoenix migration
- **Production support**: FastHTML system requires occasional bug fixes on master branch  
- **URL continuity**: Critical business requirement - all existing links must continue working
- **Data preservation**: SQLite database and all memorization data must be preserved
- **Feature parity**: Phoenix system must match all FastHTML functionality

### File Organization  
- **docs/**: Clean documentation (vision.md, plan.md, changelog.md, data_model.md)
- **data/**: Database files and CSV seed data (seeds/, seeds.exs, quran_v10.db)  
- **.claude/settings.json**: Consolidated permissions for Phoenix development tools

### Development Tools
- **Serena**: File & symbol management MCP
- **Context7**: Documentation lookup MCP  
- **Playwright**: Browser automation for E2E testing
- **Tidewave**: Project evaluation and logs MCP

## NEXT STEPS

Following the plan.md todo list:

1. **Create Phoenix 1.8.0 application** in current directory
2. **Generate default auth system** (mix phx.gen.auth)
3. **Create master data tables** (mushafs, pages, surahs, items) 
4. **Migrate master data** from CSV files in data/seeds/
5. **Create learner tables** (hafiz, hafiz_item relationships)
6. **Implement business logic** and LiveView interfaces
7. **Port Playwright tests** and add Phoenix-specific testing

---

**Remember**: This migration preserves the evolution story while maintaining production stability and URL continuity. The Phoenix implementation should match FastHTML functionality while leveraging Phoenix's superior architecture for long-term maintainability.

## LEARNINGS FROM WORKING WITH USER

### Code Style and Patterns
- **Functional pipelines preferred**: Always use `|>` chains over intermediate variables
- **Capture operator syntax**: Use `&function/1` instead of `fn x -> function(x) end` 
- **DRY principle**: Extract reusable helpers when patterns repeat (like CSV loading)
- **Elixir best practices**: Use `:code.priv_dir/1` for robust file paths, not manual `__DIR__` manipulation

### Phoenix Development Workflow
- **Mix generators**: Use `--no-scope` flag for system-wide master data (no user scoping)
- **Master data strategy**: Use database migrations for production-required data, seeds.exs for development convenience
- **File organization**: 
  - `priv/repo/master_data/` - Production reference data (CSV files)
  - `priv/repo/seeds/` - Development/test sample data
  - `priv/repo/migrations/` - Schema + master data loading
- **Context functions**: Always use changeset validation, never direct `Repo.insert_all`

### Testing Philosophy
- **Health checks over comprehensive**: Simple smoke tests that verify essential data exists
- **Catch regressions**: Tests should detect duplicate data from running seeds twice
- **Exact counts**: Use `== 114` not `>= 114` to catch duplicates
- **Master data in tests**: Use `assert item in list` not `assert list == [item]` when master data present
- **Comments for test changes**: Explain why assertions changed (e.g., "master data from migrations also present")

### Development Process
- **Small atomic commits**: One task → do → test → commit → next task
- **Stage first, then commit**: Always review staged changes before committing
- **Concise commit messages**: Subject line only, no unnecessary details
- **Update documentation**: Keep changelog.md current with actual changes
- **Changelog format**: One bullet per commit, not per change
  - Format: `- [type]: [main description]` with sub-bullets for details
  - Group all related changes under single commit entry
  - Don't fragment into many small separate bullets

### Communication Preferences
- **Brief explanations**: Explain bash commands before running them
- **No unnecessary preamble**: Direct answers, minimal fluff
- **Show SQL results**: After database operations, verify with queries
- **Ask for clarification**: When patterns could be improved (like piping operations)
- **Listen to corrections**: When user says "stop" or corrects approach, immediately adjust
- **Pattern recognition**: Notice when user asks "should we..." - they're suggesting improvements

### Technical Preferences
- **Explorer over CSV library**: Use DataFrame approach for consistency with pandas-like workflows
- **Functional over imperative**: Prefer pipelines and functional composition
- **Production-ready patterns**: Think about deployment and scalability from start
- **Clean abstractions**: Extract helpers when patterns will be repeated

## PHOENIX ARCHITECTURE LEARNINGS

### Context Design Philosophy
- **Contexts are business boundaries**, not table/schema groupings
- **Contexts group related business logic**, not just CRUD operations
- **If schemas frequently query each other**, they belong in the same context
- **If they share business rules**, they belong in the same context

### Quran SRS Context Structure
Use domain-driven contexts for this project:

**Quran Context** - Core Quran structure and memorization units:
- `Quran.Mushaf` - Different Quran layouts (15-line, 13-line, etc.)
- `Quran.Surah` - The 114 universal surahs
- `Quran.Page` - Pages within each mushaf (mushaf-dependent)
- `Quran.Ayah` - Individual verses
- `Quran.Item` - Memorization units (pages, partial pages, surahs, ayah ranges)

**Accounts Context** - User management and authentication:
- `Accounts.User` - User accounts
- `Accounts.UserToken` - Auth tokens

**Learning Context** (future) - Memorization tracking:
- `Learning.Hafiz` - Memorization profiles
- `Learning.HafizItem` - Progress tracking
- `Learning.Revision` - Review history
- `Learning.Plan` - Memorization plans

### Data Architecture Insights

#### Mushaf-Page-Surah Relationship
- **Mushafs are layout systems**, not content variations
- **Surahs are mushaf-independent** - 114 universal surahs across all mushafs
- **Pages are mushaf-dependent** - cannot exist without mushaf context
- **Items get mushaf context through pages** when relevant (no direct mushaf_id needed)

#### Juz (Para) System
- Quran divided into 30 Juz for monthly completion
- Each Juz = ~20 pages (except Juz 30 with 23 pages)
- Juz 1: Pages 1-21, Juz 2: Pages 22-41, etc.
- Page-based but consistent across similar mushafs

#### Item Design Decisions
- **No mushaf_id in items table** - gets context through page_id when needed
- **Surah items don't need page_id** - they're mushaf-independent
- **Partial pages need surah_id** - to identify which surah the partial belongs to
- **Standard vs user items** - boolean flag instead of scope field

### Generator Best Practices
- Use `--no-scope` flag for system-wide master data (no user scoping)
- Generate under appropriate context from the start
- Add indexes and validations after initial generation
- Consider relationships when choosing generation order (generate referenced tables first)