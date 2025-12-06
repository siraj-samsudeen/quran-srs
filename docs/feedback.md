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

3. **Backward Compatibility**: Re-exports in `common_function.py` ensure existing code doesn't break while allowing gradual migration.

4. **Testing Strategy**: Three-tier testing (unit → integration → E2E) aligns with FastHTML official recommendations. The 70/20/10 split is sensible.

5. **Colocated Tests**: `app/hafiz_test.py` demonstrates the pattern of keeping tests near the code they test.

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

### Divergence from FastHTML Philosophy ⚠️

| Concern | Details |
|---------|---------|
| **Over-engineering risk** | FastHTML encourages simple, single-file apps for smaller projects. The Phoenix MVC pattern adds 6+ files per module which may be overkill for this app size. |
| **Not strictly MVC** | FastHTML docs state it's "not strictly MVC" and allows flexible organization. The rigid `*_controller.py`, `*_model.py`, `*_view.py` naming may fight the framework's philosophy. |
| **Re-export complexity** | The `common_function.py` re-exports add indirection. FastHTML favors direct imports via `from fasthtml.common import *`. |

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

4. **Consider simpler organization**: For a ~15-route app, the full Phoenix MVC split may introduce unnecessary complexity. FastHTML's philosophy favors "hypermedia-based" simplicity over traditional enterprise patterns.

---

## Verdict

**Good progress on establishing the MVC pattern.** The hafiz module serves as a solid reference implementation. The testing infrastructure is well-designed. However, the refactoring is ~40% complete based on the `plan.md` checklist.

**Alignment with FastHTML**: The implementation correctly uses FastHTML patterns (beforeware, TestClient, typed tables, FT components). However, the strict MVC file organization diverges from FastHTML's "flexible, Pythonic" philosophy.

**Recommended action:** Either complete the remaining module refactoring, or split into smaller PRs (merge hafiz MVC now, continue others separately). Consider whether the full MVC split is necessary for all modules, or if simpler organization would suffice for smaller modules.
