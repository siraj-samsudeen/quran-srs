# Dev Log

## MVC Refactoring (Dec 2025)

### Overview

This refactoring established the Phoenix MVC pattern as the standard for the codebase, starting with the hafiz module as a reference implementation.

**Key Achievements:**
- Hafiz module fully refactored to Phoenix MVC pattern
- common_function.py cleaned up (163 lines moved to proper layers)
- All tests passing (13/13)
- Pattern documented for future refactoring

### Phoenix MVC Pattern

**Core Principle:** Schemas live with their contexts (models), not in a central globals file.

**Before (Database-First):**
```python
# globals.py
@dataclass
class Hafiz:
    id: int
    name: str | None = None
    # ...

hafizs = db.t.hafizs
hafizs.cls = Hafiz
```

**After (Phoenix Pattern):**
```python
# hafiz_model.py
from .globals import db

@dataclass
class Hafiz:
    id: int
    name: str | None = None
    # ...

hafizs = db.t.hafizs  # Get table reference
hafizs.cls = Hafiz    # Link schema to table

def get_hafiz(hafiz_id: int) -> Hafiz:
    return hafizs[hafiz_id]
```

**Why This Pattern:**
- ✅ Self-contained: Schema visible when reading model
- ✅ Encapsulation: Model only imports `db` from globals
- ✅ IDE support: Autocomplete works with explicit dataclass
- ✅ Phoenix-like: Matches Ecto schema pattern

### Table Linking Pattern

FastHTML uses `table.cls = Dataclass` to link Python dataclasses to database tables:

```python
hafizs = db.t.hafizs  # Get table reference
hafizs.cls = Hafiz    # Link dataclass

# Now queries return Hafiz objects:
result = hafizs[1]
assert isinstance(result, Hafiz)  # ✅ True
print(result.name)  # ✅ IDE autocomplete works
```

**Without linking:**
```python
result = hafizs[1]  # Returns generic dict-like object
print(result.name)  # ❌ No autocomplete, no type checking
```

### Hafiz Module Structure

**Files:**
- `app/hafiz_model.py` - Dataclass, table reference, CRUD functions
- `app/hafiz_controller.py` - HTTP routes only
- `app/hafiz_view.py` - UI rendering components
- `app/hafiz_test.py` - Unit tests (2) + Integration tests (3)

**Model Layer (hafiz_model.py:1):**
```python
from dataclasses import dataclass
from .globals import db  # ONLY imports db

@dataclass
class Hafiz:
    """Hafiz profile belonging to a user."""
    id: int
    name: str | None = None
    daily_capacity: int | None = None
    user_id: int | None = None
    current_date: str | None = None

hafizs = db.t.hafizs
hafizs.cls = Hafiz

def get_hafiz(hafiz_id: int) -> Hafiz:
    return hafizs[hafiz_id]

def update_hafiz(hafiz_data: Hafiz, hafiz_id: int) -> None:
    hafizs.update(hafiz_data, hafiz_id)
```

**Controller Layer (hafiz_controller.py:1):**
```python
from .hafiz_model import Hafiz, get_hafiz, update_hafiz
from .hafiz_view import render_settings_page

@hafiz_app.get("/settings")
def settings_page(auth):
    current_hafiz = get_hafiz(auth)
    return render_settings_page(current_hafiz, auth)
```

**View Layer (hafiz_view.py:1):**
```python
def render_settings_page(current_hafiz, auth):
    return main_area(
        render_settings_form(current_hafiz),
        active="Settings",
        auth=auth,
    )
```

### Testing Strategy

**Unit Tests (app/hafiz_test.py:23):**
- Pure Python functions
- No HTTP, no browser
- Fast (< 10ms per test)

```python
def test_get_hafiz():
    hafiz = get_hafiz(1)
    assert isinstance(hafiz, Hafiz)
    assert hafiz.id == 1
```

**Integration Tests (app/hafiz_test.py:93):**
- FastHTML routes with TestClient
- No browser needed
- Fast (~50ms per test)

```python
def test_settings_page_get(client, hafiz_session):
    response = client.get("/hafiz/settings", cookies=hafiz_session)
    assert response.status_code == 200
    assert "Hafiz Preferences" in response.text
```

**E2E Tests (tests/ui/):**
- Playwright browser tests
- Only for JavaScript interactions
- Slow (~2-3s per test)

### common_function.py Cleanup

**Problem:** common_function.py was a 356-line mixed bag:
- Re-exports from other modules
- Model layer functions (DB queries)
- Utility functions (pure data manipulation)
- Complex business logic (mixing layers)

**Solution:** Move functions to proper layers.

**Moved to common_model.py (Data Layer):**
```python
# Statistical updates
populate_hafizs_items_stat_columns(item_id)

# Queries and calculations
get_actual_interval(item_id)
get_page_count(records, item_ids)
get_full_review_item_ids(auth, total_page_count, ...)

# Business logic that queries data
get_srs_daily_limit(auth)
get_full_cycle_daily_limit(auth)
```

**Moved to utils.py (Pure Utility):**
```python
# Data manipulation (no DB)
group_by_type(data, current_type, field)
```

**Kept in common_function.py:**
```python
# Re-exports for backward compatibility
from .common_model import (...)
from .common_view import (...)
from .utils import group_by_type

# Complex function needing deeper refactor
def make_summary_table(mode_code, auth, ...):
    # Mixes business logic + view rendering
    # TODO: Split into service + view layers
```

### Impact

**Before:**
- 356 lines in common_function.py
- Mixed layers (model/view/utility)
- Unclear where to add new functions

**After:**
- 193 lines in common_function.py (46% reduction)
- Clear layer separation
- Re-exports maintain backward compatibility
- Model has 163 new lines (proper home for data functions)

### Lessons Learned

#### 1. Self-Contained Models

Each model should only import `db` from globals, not table references:

```python
# ✅ Good (hafiz_model.py)
from .globals import db
hafizs = db.t.hafizs

# ❌ Bad (previous pattern)
from .globals import hafizs
```

This makes models self-contained and reduces coupling.

#### 2. Backward Compatibility via Re-Exports

Keep existing imports working while refactoring:

```python
# common_function.py
from .common_model import (
    populate_hafizs_items_stat_columns,
    get_page_count,
    # ... all moved functions
)
```

Allows gradual migration - old imports still work.

#### 3. Test Environment Setup

Integration tests need environment setup:

```python
# hafiz_test.py
import os
from dotenv import load_dotenv

os.environ["ENV"] = "test"  # Use test database
load_dotenv()  # Load credentials from .env
```

Without this, tests fail authentication.

#### 4. Missing Functions Break Silently

Creating revision_model.py revealed missing functions:
- `get_revision_by_id()`
- `update_revision()`
- `cycle_full_cycle_plan_if_completed()`

These were being called but never implemented. Refactoring exposed the gaps.

### Next Steps

Apply this pattern to remaining modules:
1. profile.py → profile_controller.py, profile_model.py, profile_view.py
2. new_memorization.py → (same pattern)
3. admin.py → (same pattern)
4. page_details.py → (same pattern)

Each refactor should:
- Create self-contained model with dataclass
- Add unit + integration tests
- Move business logic to model/service layer
- Keep view layer pure (UI rendering only)

---

## FastHTML Authentication Concepts (Nov 2025)

### HTTP is Stateless
Every HTTP request is a stranger to the server. You log in on request 1, but request 2 (even 2 seconds later) has no memory of it. The server treats each request as a completely new interaction.

### Session Cookies Solve This
1. You log in → server creates session (`{user_id: 123}`)
2. Server sends session cookie (random ID like `abc123xyz`) to browser
3. **Key magic**: Browser automatically sends this cookie with every future request
4. Server reads cookie → looks up session → "Oh, you're user 123!"

You don't write code for step 3 - browsers do this automatically for all cookies on the same domain.

### Request Scope vs Session
- **`sess`** = persistent storage, but might be stale (admin deleted user, but cookie still exists)
- **`req.scope`** = per-request validated data (beforeware already checked it's valid)

Convention: Beforeware validates session data and puts clean results in `req.scope`. Handlers read from `req.scope`, not `sess` directly. Single source of truth for the request.

### FastHTML Beforeware Pattern
Middleware that runs before every route handler:

```python
def auth_before(req, sess):
    auth = sess.get("auth")           # Read from session
    req.scope["auth"] = auth          # Store validated data
    if not auth:
        return RedirectResponse("/login", status_code=303)  # Intercept
    # No return = continue to route handler

beforeware = Beforeware(auth_before, skip=["/login", "/signup"])
```

- **Skip list**: Routes that don't need auth (supports regex)
- **Return redirect**: Intercepts request, handler never runs
- **No return**: Request continues to the route handler

---

## Alpine.js + HTMX Bulk Action Bar Visibility Issue

### The Problem

After implementing a bulk edit feature for ratings, the bulk action bar would show "Selected: 0" instead of hiding after clicking Good/Ok/Bad buttons. The bar should disappear completely after a bulk action is applied.

### Architecture Context

The bulk action bar uses:
- **Alpine.js** for reactive state (`x_data="{ count: 0 }"`, `x_show="count > 0"`)
- **HTMX** for server communication (`hx_post`, `hx_swap="outerHTML"`)

When a checkbox is clicked, Alpine increments `count` and shows the bar. When a bulk button is clicked, HTMX replaces the entire table (including the bar) with fresh HTML from the server.

### Solutions Attempted

#### Attempt 1: Reset count on click
```python
**{"@click": "count = 0"}
```
Added to bulk buttons to immediately reset count when clicked. This helped hide the bar *during* the HTMX request, but after the swap completed, the bar still showed with "Selected: 0".

#### Attempt 2: CSS `:has()` selector
```css
[id^="summary_table_"]:not(:has(.bulk-select-checkbox:checked)) [id^="bulk-bar-"] {
  display: none !important;
}
```
Pure CSS solution to hide the bar when no checkboxes are checked. Didn't work initially due to browser caching the old CSS file. After cache clear, it works but felt like a workaround rather than fixing the root cause.

#### Attempt 3: Alpine.initTree() on HTMX swap
```javascript
document.body.addEventListener('htmx:load', function(event) {
  Alpine.initTree(event.detail.elt);
});
```
Re-initializes Alpine on HTMX-swapped content. Didn't solve the visibility issue.

### Root Cause

The issue was `x_cloak=True` on the bulk bar. `x-cloak` is designed to hide elements *before* Alpine initializes, then Alpine removes it. But with HTMX swaps:

1. Fresh HTML arrives with `x-cloak` attribute
2. Alpine removes `x-cloak` and evaluates `x-show="count > 0"` where `count = 0`
3. There's a brief moment where the element is visible before `x-show` hides it

The real problem: the timing between `x-cloak` removal and `x-show` evaluation caused a visible "Selected: 0" flash.

### The Fix

Changed from `x_cloak=True` to inline `style="display: none"`:

```python
return Div(
    # ... bar content ...
    x_show="count > 0",
    style="display: none",  # Instead of x_cloak=True
)
```

Why this works:
1. **Initial load**: Bar hidden via inline style
2. **Checkbox click**: Alpine's `x-show="count > 0"` evaluates true, overrides inline style, shows bar
3. **Bulk action click**: `@click="count = 0"` immediately hides bar (good UX feedback)
4. **After HTMX swap**: New HTML arrives with `style="display: none"`, bar stays hidden by default

The key insight: inline `style="display: none"` provides a *default hidden state* that Alpine can override, whereas `x-cloak` is a *temporary* hide that gets removed by Alpine.

### Final Solution

**`app/common_function.py`**:
- Added `@click="count = 0"` to bulk buttons (immediate feedback while HTMX processes)
- Changed `x_cloak=True` to `style="display: none"` (the key fix)

### Lesson Learned

When combining Alpine.js with HTMX for reactive UI that gets replaced:
- Use inline `style="display: none"` instead of `x-cloak` for elements that should start hidden after HTMX swap
- `@click` handlers provide immediate feedback before HTMX round-trip completes
