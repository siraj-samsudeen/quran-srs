# CLAUDE.md - TDD Rebuild

## Current Goal

Rebuilding Quran SRS from scratch using pure TDD. The `master` branch is the specification. The `tdd-rebuild` branch is where we build feature parity via strict RED-GREEN-REFACTOR discipline.

---

## Core Rules

### TDD Workflow (RED-GREEN-REFACTOR)

**🔴 RED**: Write failing test → Run test (must fail) → Commit: `RED: feature description`

**✅ GREEN**: Write minimal code to pass → Run test (must pass) → Commit: `GREEN: feature description`

**🔄 REFACTOR** (optional): Improve code → Run test (must still pass) → Commit: `REFACTOR: description`

- Each feature = 2-3 separate commits (never combine RED+GREEN)
- REFACTOR only when duplication emerges (Rule of Three)
- Extract helpers only after patterns repeat 3+ times

### Git Workflow

- **ALWAYS ask approval before committing** - Show what will be committed and wait
- Commit messages must match: `RED:`, `GREEN:`, or `REFACTOR:` pattern
- Never auto-commit

### Testing Strategy (Phoenix LiveView Pattern)

**UI Tests** (`tests/ui/`):
- ✅ Setup via DB, Act via browser, Assert on UI only
- ❌ Never assert on database state

**Backend Tests** (`tests/backend/`):
- ✅ Setup via DB, Act via function calls, Assert on DB and return values
- ⚡ Fast (no browser overhead)

### Browser Configuration

- **Headed** (visible) Chrome during development - user watches tests execute
- Switch to headless later for CI/CD
- Config: `tests/conftest.py` → `headless=False`

### Mentor Mindset

- Challenge assumptions and critique code
- Point out better approaches and anti-patterns
- Question decisions that don't make sense
- Help user learn, don't just execute

---

## User Journey & Dependencies

### Actual User Journey (Timeline)
1. **Day 1**: Auth → Hafiz → Profile (mark memorized) → FC appears on dashboard → Rate items → Close Date
2. **Day 2+**: FC continues, struggling items demote to SRS (if bad_streak ≥ 1)
3. **Later**: Expand learning via New Memorization → DR → WR → back to FC
4. **Ongoing**: All modes visible on dashboard as they become populated

### Key Dependencies
- **FC** requires: Memorized pages (Profile)
- **SRS** requires: FC with bad ratings (Close Date triggers demotion)
- **DR** requires: New Memorization (NM → DR transition)
- **WR** requires: DR graduation (DR → WR after 7 reviews)
- **Dashboard**: Shows only modes with items (empty tables hidden)

---

## File Organization

### Project Structure (TDD Rebuild)
```
_reference/               # Master branch code for reference only
├── main.py              # Original main app file
├── app/                 # All master application modules
├── globals.py           # Master global config
├── utils.py             # Master utility functions
├── public/              # Master static assets
└── package.json         # Master npm config

app/                     # Fresh TDD implementation (build from scratch)
tests/                   # Test files
├── ui/                  # Browser-based UI tests
│   ├── conftest.py     # Playwright fixtures
│   └── test_*.py
├── backend/            # Pure Python backend tests
└── conftest.py         # Shared fixtures (ENV=test, db)

main.py                  # Fresh minimal FastHTML app
migrations/              # Database schema (shared)
docs/                    # Documentation (shared)
data_backup/             # Seed data (shared)
```

### Reference Code Usage

Master branch code lives in `_reference/` directory:
- **DO NOT** copy-paste from `_reference/` - use as specification only
- **DO** reference to understand expected behavior
- **DO** check business logic and edge cases
- **DO NOT** import or use reference code directly

**Key reference files**:
- `_reference/app/users_controller.py` - Authentication flows
- `_reference/main.py` - Home page, Close Date logic
- `_reference/app/profile.py` - Memorization status
- `_reference/app/common_function.py` - Shared utilities, beforeware

---

## Running Tests

**Terminal 1: Start server**
```bash
ENV=test uv run main.py
```

**Terminal 2: Run tests**
```bash
uv run pytest tests/ui/test_authentication.py -v
uv run pytest tests/ui -v
uv run pytest --cov --cov-report=html
```

---

## Current Status

**Phase**: 0 (Smoke Test) | **Next**: Commit documentation → Begin Phase 0 implementation

---

## Lessons Learnt/Corrections from User

### 1. RED Commits Must Only Contain Failing Tests

**Rule:** RED commits should ONLY contain the failing test. Any setup, refactoring, or infrastructure work must be in a separate commit (e.g., `chore:`, `refactor:`, `docs:`).

**Bad Example:**
```
RED: Home page redirects to login

- Added failing test
- Moved master code to _reference/
- Created fresh main.py
- Updated documentation
```

**Good Example:**
```
chore: Move master code to _reference for TDD rebuild

- Moved all app/ code to _reference/app/
- Moved globals.py, utils.py, public/ to _reference/
- Created fresh minimal main.py
- Deleted .sesskey
- Updated CLAUDE.md with new structure

(Separate commit later)
RED: Home page redirects to login

- Added test_home_page_redirects_to_login test
- Test verifies "/" redirects to "/users/login"
```

### 2. No Status Comments in Production Code

**Rule:** Never add comments explaining what the code "will be" or status messages to the user. Code should be clean and self-documenting.

**Bad Example:**
```python
from fasthtml.common import *

# Minimal app setup - will build with TDD
app, rt = fast_app()

serve()
```

**Good Example:**
```python
from fasthtml.common import *

app, rt = fast_app()

serve()
```

**Why:** Comments like "will build with TDD" are meta-commentary about the development process, not about the code itself. They clutter the codebase and become stale quickly. 