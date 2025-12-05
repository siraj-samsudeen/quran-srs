# Dev Log

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

---

## 2025-12-05: SRS Algorithm Change - From Prime Numbers to Streak-Based

### Background

The SRS (Spaced Repetition System) algorithm determines when items should be reviewed
based on past performance. The previous implementation used prime number sequences
for interval progression.

### Why We Changed

The prime-based algorithm had several issues:

1. **Hard to tune**: Prime jumps are fixed (7→11 is +4, 11→13 is +2). Can't adjust
   growth rates for different phases of memorization.

2. **Unintuitive for users**: "Why did my interval jump from 11 to 13?" has no
   satisfying answer beyond "because 13 is the next prime."

3. **Bad rating handling**: Dividing by penalties (35% of actual) then looking up
   in the prime sequence created inconsistent behavior.

4. **No phase awareness**: Same sequence whether at 7 days or 50 days.

### The New Algorithm

**Streak-based with phase multipliers:**

| Phase | Good | Ok | Bad |
|-------|------|-----|-----|
| 0-14 days | `interval + (streak × 2)` | +2 | `÷ (streak + 1)` |
| 14-30 days | `interval + (streak × 1.5)` | +1 | `÷ (streak + 1)` |
| 30-40 days | `interval + (streak × 1)` | stay | Drop to 30 |
| 40+ days | `interval + 3` (fixed) | cap at 40 | Drop to 30 |

**Key design decisions:**

1. **40-day threshold**: Observation that degradation starts around 40 days.
   Ok ratings cap here; only Good can push beyond.

2. **30-day floor**: Bad rating at 30+ drops to 30, bringing items back to
   the "ideal zone" for focused work.

3. **Graduation by streak**: 3 consecutive Good = mastery. More meaningful than
   "interval > 99 days".

4. **Phase-aware growth**: Different multipliers for building (fast), strengthening
   (moderate), and maintenance (slow) phases.

### Option B: FC Reviews Affect SRS

When a SRS item is reviewed during Full Cycle:
- **Old behavior**: Just reschedule, don't recalculate
- **New behavior**: Full SRS recalculation (any revision affects SRS)

Rationale: The user DID review the page. The rating should count regardless of
which mode triggered the review. If they got Good in FC, it should count toward
graduation. If Bad, it should affect the interval.

### Backward Compatibility

- Old `next_interval` values stored on revisions are preserved
- `populate_hafizs_items_stat_columns()` reads intervals from revision history,
  does NOT recalculate them
- This ensures algorithm changes don't retroactively affect historical data

### Testing Strategy

Tests use MECE (Mutually Exclusive, Collectively Exhaustive) framework:
- 76 unit tests for pure calculation functions
- 14 integration tests including backward compatibility
- Synthetic fixtures (committed) for CI
- Full production fixtures (gitignored) for local verification

### Files Changed

- `app/srs_interval_calc.py` - New pure calculation module
- `app/srs_reps.py` - Rewritten to use new calculations
- `main.py` - Option B: FC review triggers SRS recalc
- `app/common_function.py` - History replay preserves intervals
