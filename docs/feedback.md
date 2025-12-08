# MVC Refactoring Review: `refactor/mvc-cleanup` Branch

**Reviewed:** December 2025

## Summary Statistics

- **+3,605 / -1,088 lines** across 39 files
- **15 commits** since branching from master
- Primary focus: Phoenix-inspired MVC pattern + comprehensive testing

---

## What Was Done

### 1. Layer Separation (Phoenix MVC Pattern)

**New files created:**

| File | Purpose | Lines |
|------|---------|-------|
| `app/app_setup.py` | Middleware, beforeware, headers, app factory | 106 |
| `app/common_model.py` | Data access layer (queries, CRUD) | 335 |
| `app/common_view.py` | UI components (rendering, forms) | 404 |
| `app/hafiz_controller.py` | Route handlers only | 43 |
| `app/hafiz_model.py` | Hafiz dataclass + table linking | 32 |
| `app/hafiz_view.py` | Hafiz UI components (renamed from hafiz.py) | ~50 |

**common_function.py cleanup:**
- Reduced from ~846 lines to re-exports + 1 complex function (`make_summary_table`)
- Functions moved to proper layers:
  - Data access → `common_model.py`
  - UI rendering → `common_view.py`
  - Pure utilities → `utils.py`
  - Backward compatibility maintained via re-exports

### 2. Code Organization

**Moved files:**
- `globals.py` → `app/globals.py`
- `utils.py` → `app/utils.py`

**Renamed for clarity:**
- `app/fixed_reps.py` → `app/fixed_reps_service.py`
- `app/srs_reps.py` → `app/srs_reps_service.py`
- `app/hafiz.py` → `app/hafiz_view.py`

### 3. Testing Infrastructure

**Test folders restructured:**
- `tests/ui/` → `tests/e2e/` (Playwright browser tests)
- `tests/backend/` → `tests/integration/` (TestClient tests)
- `app/*_test.py` for colocated unit/integration tests

**New test files:**

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `app/hafiz_test.py` | 5 | Unit + integration for hafiz module |
| `tests/integration/mode_transitions_test.py` | 8 | DR→WR→FC→SRS transitions |
| `tests/e2e/rating_test.py` | ~8 | Rating dropdown interactions |
| `tests/e2e/close_date_test.py` | ~4 | Close Date workflow |
| `tests/e2e/hafiz_test.py` | ~5 | Hafiz management UI |
| `tests/e2e/new_memorization_test.py` | ~4 | NM workflow |

### 4. Documentation

- `docs/testing-approach.md` (753 lines) - Comprehensive testing strategy following FastHTML patterns
- `docs/dev-log.md` (286 lines) - Refactoring decisions and Phoenix pattern explanation
- `plan.md` (71 lines) - TDD rebuild checklist with completed/pending items

---

## Strengths

1. **Clear Layer Separation**: The Phoenix MVC pattern is well-implemented. Model files are self-contained with dataclass + table linking + CRUD functions.

2. **Table Linking Pattern**: Good use of FastHTML's `table.cls = Dataclass` pattern for IDE autocomplete and type safety:
   ```python
   hafizs = db.t.hafizs
   hafizs.cls = Hafiz  # Now queries return typed Hafiz objects
   ```

3. **Testing Strategy**: Three-tier testing (unit → integration → E2E) aligns with FastHTML official recommendations. The 70/20/10 split is sensible.

4. **Colocated Tests**: `app/hafiz_test.py` demonstrates the pattern of keeping tests near the code they test.

---

## Areas for Improvement

1. **Incomplete Refactoring** - Per `plan.md`, several modules still need MVC treatment:
   - `profile.py` (not refactored)
   - `new_memorization.py` (not refactored)
   - `admin.py` (not refactored)
   - `page_details.py` (not refactored)

2. **`make_summary_table()` Still Mixed**: The largest function in `common_function.py` still mixes business logic with view rendering. This is noted in the plan as needing "deeper refactor."

3. **Inconsistent Naming**: Some modules don't follow the `*_controller.py`, `*_model.py`, `*_view.py` convention:
   - `revision.py` + `revision_model.py` + `revision_view.py` (missing `revision_controller.py`)
   - `profile.py` (monolithic, no MVC split)

4. **Test Coverage Gaps**: The mode transition tests cover the core algorithm but E2E tests may be duplicating integration test coverage.

5. **~~Remove Re-exports, Use Direct Imports~~** ✅ DONE: Re-exports have been removed from `common_function.py`. All files now import directly from source modules (`common_model`, `common_view`, `app_setup`, `utils`). Only `make_summary_table()` remains in `common_function.py` (marked as TODO for future refactoring).

---

## Recommendations

1. **Complete the MVC Refactoring** for remaining modules before merging, or document them as "Phase 2" work.

2. **Refactor `make_summary_table()`** - Split into:
   - Model: `get_items_for_summary(mode_code, auth)`
   - View: `render_summary_table(items, mode_code)`

3. **Consider Merging Incrementally** - The hafiz MVC pattern is complete and well-tested. Could merge that as a standalone PR and continue other modules on a new branch.

4. **Add CI Integration** - Consider adding a test run to validate all 13+ tests pass before merge.

---

## Comparison Against Official FastHTML Guidance

Based on the [FastHTML LLM context](https://gist.github.com/decodingchris/1da7b1ae6b58bd2259a986581e77fbdc) and [FastHTML by example](https://gist.github.com/jph00/f1cfe4f94a12cb4fd57ad7fc43ebd1d0):

### Alignment with FastHTML Patterns ✅

| FastHTML Guidance | Refactoring Implementation | Status |
|-------------------|---------------------------|--------|
| Use `fast_app()` for app creation | `create_app_with_auth()` wraps `fast_app()` | ✅ Aligned |
| Beforeware for authentication | `user_bware`, `hafiz_bware` in `app_setup.py` | ✅ Aligned |
| `table.cls = Dataclass` for typed queries | `hafizs.cls = Hafiz` pattern used | ✅ Aligned |
| TestClient for testing views | Used in `hafiz_test.py` integration tests | ✅ Aligned |
| Components as functions returning FT | `render_settings_page()`, `rating_dropdown()` | ✅ Aligned |
| HTMX for interactivity | `hx_get`, `hx_post`, `hx_swap` used throughout | ✅ Aligned |

### FastHTML Testing Guidance

The refactoring's testing approach **aligns well** with official recommendations:

```python
# FastHTML docs: "Use Starlette's TestClient to validate view output"
from starlette.testclient import TestClient
client = TestClient(app)
response = client.get('/')
assert "Welcome" in response.text
```

The `hafiz_test.py` follows this pattern exactly.

### Key Observations

1. **Database pattern is correct**: The `db.t.tablename` + `table.cls = Dataclass` pattern matches FastHTML's fastlite integration.

2. **Route definitions are idiomatic**: Using `@hafiz_app.get("/settings")` aligns with FastHTML's decorator-based routing.

3. **Component pattern is good**: Reusable functions like `render_settings_form()` returning FT elements follow FastHTML's component model.

---

## Verdict

**Good progress on establishing the MVC pattern.** The hafiz module serves as a solid reference implementation. The testing infrastructure is well-designed. However, the refactoring is ~40% complete based on the `plan.md` checklist.

**Alignment with FastHTML**: The implementation correctly uses FastHTML patterns (beforeware, TestClient, typed tables, FT components). The strict MVC organization is appropriate for this codebase size and complexity.

**Recommended action:** Complete the remaining module refactoring, remove re-exports in favor of direct imports, and consider merging incrementally (hafiz MVC first, then other modules).

---

## Hafiz Module Deep Review: MVC Reference Implementation

The hafiz module (`hafiz_controller.py`, `hafiz_model.py`, `hafiz_view.py`, `hafiz_test.py`) serves as the reference implementation for MVC refactoring. This section provides a detailed review.

### Module Structure

```
app/
├── hafiz_controller.py  (32 lines)  - Route handlers only
├── hafiz_model.py       (106 lines) - Dataclass + table + CRUD (all hafiz operations)
├── hafiz_view.py        (68 lines)  - UI components with __all__ exports
├── hafiz_test.py        (129 lines) - Colocated unit + integration tests
tests/
├── conftest.py          (65 lines)  - Shared auth fixtures (client, auth_session, hafiz_session)
└── e2e/
    └── hafiz_test.py    (73 lines)  - Browser-based E2E tests
```

### What Works Well ✅

1. **Controller is thin** - Routes only orchestrate, no business logic:
   ```python
   @hafiz_app.get("/settings")
   def settings_page(auth):
       current_hafiz = get_hafiz(auth)
       return render_settings_page(current_hafiz, auth)
   ```

2. **Model is self-contained** - Dataclass + table linking + CRUD in one file:
   ```python
   @dataclass
   class Hafiz:
       id: int
       name: str | None = None
       ...

   hafizs = db.t.hafizs
   hafizs.cls = Hafiz  # Type linking

   def get_hafiz(hafiz_id: int) -> Hafiz:
       return hafizs[hafiz_id]
   ```

3. **View components are reusable** - Small, focused functions:
   ```python
   def render_settings_form(current_hafiz):  # Returns Form()
   def render_settings_page(current_hafiz, auth):  # Wraps form in layout
   ```

4. **Tests cover all layers**:
   - Unit tests: Test model functions directly
   - Integration tests: Test routes with TestClient (no browser)
   - E2E tests: Test user interactions with Playwright

5. **Colocated tests** - `app/hafiz_test.py` lives next to the code it tests, making it easy to maintain.

### Areas to Improve ⚠️ → All Fixed ✅

1. ~~**Hafiz CRUD is split across files**~~ ✅ DONE: All hafiz CRUD functions consolidated in `hafiz_model.py`:
   - `get_hafiz()`, `update_hafiz()`, `insert_hafiz()`, `delete_hafiz()`
   - `get_hafizs_for_user()`, `populate_hafiz_items()`, `create_new_plan()`
   - `users_model.py` now only handles user-level operations

2. ~~**Missing `__all__` exports**~~ ✅ DONE: Added explicit exports to both modules:
   ```python
   # hafiz_model.py
   __all__ = ["Hafiz", "hafizs", "get_hafiz", "update_hafiz", "insert_hafiz", ...]

   # hafiz_view.py
   __all__ = ["render_settings_form", "render_settings_page", "render_theme_page"]
   ```

3. ~~**`update_stats_column` route is misplaced**~~ ✅ DONE: Moved to `admin.py` at `/admin/update_stats_column`. Updated reference in `page_details.py`.

4. ~~**Test fixtures could be shared**~~ ✅ DONE: Added shared fixtures to `tests/conftest.py`:
   - `client` - TestClient for the app
   - `auth_session` - Login cookies
   - `hafiz_session` - Auth + hafiz selection cookies
   - `parse_html` - lxml parser for XPath assertions

### Template for Other Modules

When refactoring other modules, follow this pattern:

**1. `{module}_model.py`**
```python
"""
{Module} Model - Data access layer
"""
from dataclasses import dataclass
from .globals import db

@dataclass
class {Entity}:
    id: int
    # ... fields

# Table linking
{table} = db.t.{table}
{table}.cls = {Entity}

# CRUD functions
def get_{entity}(id: int) -> {Entity}: ...
def update_{entity}(data: {Entity}, id: int): ...
def delete_{entity}(id: int): ...
def list_{entities}(where: str = None) -> list[{Entity}]: ...
```

**2. `{module}_view.py`**
```python
"""
{Module} View - UI components
"""
from fasthtml.common import *
from monsterui.all import *
from .common_view import main_area

def render_{entity}_form(entity): ...
def render_{entity}_page(entity, auth): ...
def render_{entity}_list(entities, auth): ...
```

**3. `{module}_controller.py`**
```python
"""
{Module} Controller - Route handlers
"""
from fasthtml.common import *
from .app_setup import create_app_with_auth
from .{module}_model import get_{entity}, update_{entity}
from .{module}_view import render_{entity}_page

{module}_app, rt = create_app_with_auth()

@{module}_app.get("/{entity}/{id}")
def {entity}_detail(auth, id: int):
    entity = get_{entity}(id)
    return render_{entity}_page(entity, auth)
```

**4. `{module}_test.py`** (colocated)
```python
"""
{Module} Tests - Unit and integration
"""
import pytest
from starlette.testclient import TestClient

# Unit tests - no HTTP
def test_get_{entity}(): ...

# Integration tests - TestClient
@pytest.fixture
def client(): ...

def test_{entity}_page_get(client, auth_session): ...
```

### Verdict on Hafiz Module

**Grade: A**

The hafiz module is now a complete reference implementation:
- ✅ Clear MVC separation (controller/model/view)
- ✅ All CRUD consolidated in model
- ✅ Explicit `__all__` exports
- ✅ Proper route placement
- ✅ Shared test fixtures
- ✅ Comprehensive test coverage (unit + integration + E2E)

This module serves as the template for refactoring remaining modules.
