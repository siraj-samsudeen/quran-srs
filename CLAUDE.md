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

### Application Code
```
app/
├── users_controller.py    # User auth routes
├── users_view.py          # User auth UI
├── users_model.py         # User DB operations
└── common_function.py     # Shared utilities, beforeware
```

### Test Code
```
tests/
├── ui/                    # Browser-based UI tests
│   ├── conftest.py        # Playwright fixtures
│   └── test_*.py
├── backend/               # Pure Python backend tests
└── conftest.py           # Shared fixtures (ENV=test, db)
```

---

## Master Branch Reference

Use `master` as specification to understand:
- Expected behavior and business logic
- Database schema
- UI components

**Do NOT copy-paste from master** - use as spec, rebuild via TDD.

**Key files**:
- `app/users_controller.py` - Authentication
- `main.py` - Home page, Close Date
- `app/profile.py` - Memorization status
- `app/common_function.py` - Shared utilities

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
