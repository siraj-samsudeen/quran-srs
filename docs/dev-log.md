# Dev Log

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
