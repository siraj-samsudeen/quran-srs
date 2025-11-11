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
- **Documentation updates don't need separate commits** - Update CLAUDE.md as needed within RED/GREEN/REFACTOR commits

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

### Documentation & Best Practices Workflow

**CRITICAL: Always follow this order when starting ANY task:**

1. **Read `docs/llms.txt` first** - This is the project's FastHTML knowledge base
   - Contains FastHTML patterns specific to this project
   - Load relevant sections into context before coding

2. **Check Context7 for latest FastHTML API** - Verify current best practices
   - Use `mcp__context7__resolve-library-id` → `mcp__context7__get-library-docs`
   - Search for relevant topics (e.g., "beforeware authentication routing")
   - Ensure code follows latest FastHTML conventions

3. **_reference/ is NOT the source of truth**
   - Code in `_reference/` was written while learning FastHTML
   - May contain outdated patterns or anti-patterns
   - **ONLY** use `_reference/` to understand business logic and expected behavior
   - **NEVER** copy implementation patterns from `_reference/`

**Example workflow:**
```
Task: Implement authentication
1. grep "auth" docs/llms.txt (load patterns)
2. Context7: get latest FastHTML auth docs
3. Write test (RED)
4. Implement using docs/llms.txt + Context7 patterns (GREEN)
5. Reference _reference/ only for business rules if needed
```

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

## Lessons Learnt

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

### Corrections from User
- never restart the server on your own as changes are
  automatically reloaded.
- docs updates can happen in any commit including RED commit. other chores and other code changes should not be done in RED commit.
- for current status, check the plan.md and the git commits to see where we are in the RED-GREEN-REFACTOR loop for the first unchecked task in the plan.
- explain code line by line always once you finish the task
- use resilient selectors in Playwright tests: `get_by_role()`, `get_by_label()`, `get_by_test_id()` instead of brittle CSS selectors like `input[name='email']`
- do not use docstrings in tests - inline comments are sufficient and clearer

### 3. MonsterUI Setup and Form Patterns

**Rule:** MonsterUI components require `Theme.*.headers()` in `fast_app()` for proper styling.

**Without Theme Headers:**
```python
app, rt = fast_app()  # MonsterUI components render unstyled
```

**With Theme Headers:**
```python
app, rt = fast_app(hdrs=Theme.blue.headers())  # Fully styled components
```

**LabelInput Auto-Naming:**
- `LabelInput("Name")` → automatically sets `name="name"` (lowercase of label)
- `LabelInput("Email")` → automatically sets `name="email"`
- `LabelInput("Confirm Password", name="confirm_password")` → needs explicit `name` when label has spaces

**Form Styling Best Practices:**
- Use `cls=ButtonT.primary` for primary action buttons (CTAs)
- Use `cls="space-y-6"` on containers for consistent vertical spacing
- Use `cls="mt-4"` for specific top margin spacing
- Use `cls=TextT.primary` for primary colored text/links