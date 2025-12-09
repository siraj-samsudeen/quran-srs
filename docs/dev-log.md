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

### Session Key Naming Convention

**Decision:** Use `sess["user_id"]` for user authentication and `sess["auth"]` for hafiz selection.

**Pattern:**
```python
sess["user_id"] = user_id     # ✅ User authentication (explicit)
sess["auth"] = {              # ✅ Hafiz context (FastHTML convention, but as dict!)
    "hafiz_id": hafiz_id,
    "user_id": user_id,
}
```

**Why use a dict for `sess["auth"]`?**

Instead of storing just the hafiz_id as an integer, we store a **dict with multiple context values**:
- ✅ **Self-documenting**: `auth["hafiz_id"]` is clearer than cryptic integer
- ✅ **Extensible**: Can add more fields (`hafiz_name`, permissions, etc.) without changing structure
- ✅ **Explicit**: No guessing what the integer represents

**Example usage in routes:**
```python
def settings_page(auth):  # auth is dict: {"hafiz_id": int, "user_id": int}
    hafiz_id = auth["hafiz_id"]  # ✅ Clear what we're accessing
    user_id = auth["user_id"]    # ✅ Both IDs available
    current_hafiz = get_hafiz(hafiz_id)
```

**Why `sess["auth"]` instead of `sess["hafiz_context"]`?**

FastHTML only recognizes **specific reserved parameter names** for auto-injection. The `auth` parameter is one of these reserved names (like `sess`, `req`, etc.). Custom names like `hafiz_id` or `hafiz_context` are **not recognized** and will be ignored.

**What happens if you use a custom name?**
```python
# This FAILS - FastHTML warning: "hafiz_id has no type annotation and is not a recognised special name"
req.scope['hafiz_id'] = sess.get("auth")  # Set in beforeware
def my_route(hafiz_id):  # FastHTML ignores this, hafiz_id = None
```

**The flow:**
1. `sess["auth"] = {"hafiz_id": 1, "user_id": 123}` (store dict in session)
2. `req.scope["auth"] = sess.get("auth")` (beforeware)
3. `def my_route(auth)` (auth dict auto-injected from req.scope)

### FastHTML Auth Parameter Injection (CRITICAL Pattern)

**IMPORTANT:** FastHTML has specific requirements for `auth` parameter auto-injection to work.

#### The Pattern (What Works)

**Beforeware:**
```python
def hafiz_auth(req, sess):
    """Check hafiz selection and set up query filters."""
    # CRITICAL: Chained assignment sets BOTH req.scope AND local variable
    # auth is a dict: {"hafiz_id": int, "user_id": int}
    auth = req.scope['auth'] = sess.get("auth", None)
    if not auth:
        return RedirectResponse("/users/hafiz_selection", status_code=303)

    # Validate hafiz exists
    hafiz_id = auth.get("hafiz_id")
    if not hafiz_id:
        return RedirectResponse("/users/hafiz_selection", status_code=303)

    try:
        get_hafiz(hafiz_id)
    except NotFoundError:
        del sess["auth"]
        return RedirectResponse("/users/hafiz_selection", status_code=303)

    # Apply xtra filters
    revisions.xtra(hafiz_id=hafiz_id)
    hafizs_items.xtra(hafiz_id=hafiz_id)
    plans.xtra(hafiz_id=hafiz_id)
```

**Routes:**
```python
@hafiz_app.get("/settings")
def settings_page(auth):  # ⚠️ NO TYPE HINT on auth! (auth is dict)
    hafiz_id = auth["hafiz_id"]  # ✅ Self-documenting
    current_hafiz = get_hafiz(hafiz_id)
    return render_settings_page(current_hafiz, hafiz_id)
```

#### Critical Requirements

1. **✅ Session key MUST be `sess["auth"]`** (FastHTML convention)
2. **✅ MUST set `req.scope['auth']`** in beforeware (chained assignment pattern)
3. **✅ Parameter MUST be named `auth`** (FastHTML reserved name - cannot use `hafiz_id` or other names)
4. **✅ NO type hint on `auth` parameter** (no `: int` annotation)

**Why `auth` specifically?** FastHTML only recognizes specific reserved parameter names for auto-injection: `auth`, `sess`, `req`, etc. Custom names like `hafiz_id` are **ignored** and default to `None`, causing errors.

#### What Breaks Auto-Injection

❌ **Type hints on auth parameter:**
```python
def settings_page(auth: int):  # BREAKS injection!
```

❌ **Wrong session key:**
```python
sess["hafiz_id"] = hafiz_id  # BREAKS injection!
```

❌ **Not setting req.scope:**
```python
auth = sess.get("auth", None)  # Missing req.scope['auth'] =
```

#### Why No Type Hints?

FastHTML's parameter resolution checks type annotations to determine how to inject parameters:
- **With type hint** (`auth: int`): FastHTML looks for query param, form data, or path param
- **Without type hint** (`auth`): FastHTML checks `req.scope` for matching key

This is FastHTML's convention used throughout the codebase (revision.py, admin.py, etc.).

#### Attempted Alternatives (Failed)

**❌ Pre-fetching with dataclass injection:**
```python
# Beforeware
req.scope["current_hafiz"] = get_hafiz(hafiz_id)

# Route
def settings_page(current_hafiz: Hafiz):  # FastHTML treats as form param!
```
**Why it failed:** FastHTML's `_is_body()` check identifies dataclass annotations as body/form parameters, even when present in `req.scope`.

**Decision:** Stick with FastHTML's `auth` convention (no type hints, manual `get_hafiz()` in routes).

### Modular Routing with Sub-Apps

FastHTML uses **sub-apps with `Mount()`** for modular routing, equivalent to FastAPI's `APIRouter` pattern.

#### Pattern

Each controller module creates its own sub-app:

```python
# hafiz_controller.py
from .app_setup import create_app_with_auth

hafiz_app, rt = create_app_with_auth()  # Create sub-app

@hafiz_app.get("/settings")  # Route: /hafiz/settings (after mounting)
def settings_page(auth, sess):
    current_hafiz = get_hafiz(auth)
    return render_settings_page(current_hafiz, auth)
```

Main app mounts all sub-apps with path prefixes:

```python
# main.py
from app.hafiz_controller import hafiz_app
from app.users_controller import users_app

app, rt = create_app_with_auth(
    routes=[
        Mount("/hafiz", hafiz_app, name="hafiz"),  # All hafiz_app routes under /hafiz
        Mount("/users", users_app, name="users"),  # All users_app routes under /users
    ]
)
```

#### Why This Pattern?

**Benefits:**
- ✅ **Modularity**: Each controller is self-contained (routes + logic in one file)
- ✅ **Namespace isolation**: `/hafiz/*` routes live in `hafiz_controller.py`
- ✅ **Independent auth**: Each sub-app can have different beforeware (e.g., skip auth for `/users/login`)
- ✅ **Testability**: Can test each sub-app independently with `TestClient(hafiz_app)`
- ✅ **Clean main.py**: Just mounts sub-apps, no individual route imports

**Comparison with other frameworks:**
- **FastAPI**: `APIRouter` + `app.include_router(router)`
- **Flask**: `Blueprint` + `app.register_blueprint(bp)`
- **Django**: `include()` in URLconf
- **FastHTML**: Sub-app + `Mount()` in routes list

This is the standard pattern across all modern web frameworks for organizing routes.

### CRUD Design Decisions

#### Why `update_hafiz()` Returns `None`

FastHTML's `table.update()` doesn't return the updated record by default. To return it, we'd need an extra query:

```python
def update_hafiz(hafiz: Hafiz, hafiz_id: int) -> Hafiz:
    hafizs.update(hafiz, hafiz_id)
    return hafizs[hafiz_id]  # Extra database query
```

**Decision:** Follow FastHTML convention and return `None`. No current caller needs the return value (YAGNI principle).

**Tradeoff:**
- ✅ Pro: No extra database query
- ✅ Pro: Consistent with FastHTML's design
- ❌ Con: Inconsistent with `insert_hafiz()` and `delete_hafiz()` (they do return records)

#### Why `hafiz_id` is Separate from `hafiz.id` in `update_hafiz()`

The ID parameter comes from a **trusted source** (session/auth), not from form data:

```python
# Controller (hafiz_controller.py:30)
def update_settings(auth, hafiz: Hafiz, sess):
    current_hafiz = get_hafiz(auth)
    update_hafiz(hafiz, current_hafiz.id)  # ✅ ID from auth (trusted)
    # NOT: update_hafiz(hafiz, hafiz.id)  # ❌ ID from form (untrusted)
```

**Security concern:** User could manipulate form data to include `id=999` (trying to update someone else's hafiz). Separate parameter forces caller to explicitly provide the ID from a trusted source.

**Pattern:**
```python
def update_hafiz(hafiz: Hafiz, hafiz_id: int) -> None:
    # hafiz_id is separate from hafiz.id to prevent ID tampering via form input
    hafizs.update(hafiz, hafiz_id)
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
    hafiz_id = sess.get("hafiz_id")   # Read from session
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
