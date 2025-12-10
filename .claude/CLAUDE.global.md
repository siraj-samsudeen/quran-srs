# Global CLAUDE Instructions

This file contains universal workflow rules and technology-specific patterns used across all projects.

**Location**: Master copy at `quran-srs/.claude/CLAUDE.global.md`, symlinked to `~/.claude/CLAUDE.md`

---

## Browser Testing

- Chrome MCP for screenshots, clicking, navigation (primary choice)
  - Uses your existing Chrome session with auth/cookies already set up
  - If disconnected: check `claude mcp list` → open chrome-mcp-server extension (red AI icon) → click Connect
- Playwright as fallback if Chrome MCP unavailable
  - Opens new browser window requiring fresh login/auth setup
- screenshots should be always stored in the local screenshots folder and excluded from git using .gitignore

---

## TDD Workflow (RED-GREEN-REFACTOR)

**Core Principle:** Always start at the UI, drill down only when blocked, complete nested cycles, bubble back up.

**🔴 RED**: Write failing test → Commit: `RED: feature description`
- Tests only, no implementation
- Test must fail for the right reason

**✅ GREEN**: Write minimal code to pass → Commit: `GREEN: feature description`
- Implementation only, no new tests
- No YAGNI (minimal code to pass)

**🔄 REFACTOR**: Improve code (must still pass) → Commit: `REFACTOR: description`
- No behavior change
- Only when duplication emerges (Rule of Three)

**Golden Rules:**
- Never refactor while red
- Never over-implement at green
- Never combine RED+GREEN in one commit

### Drill-Down Protocol

When UI test is blocked by missing backend:

1. **Pause UI cycle**
2. **Drill down**: RED/GREEN/REFACTOR at Context level
   - If Context blocked: drill to Helper level
3. **Bubble back up**: Resume UI cycle (GREEN/REFACTOR)

Git history should show nested cycles clearly.

---

## Testing Philosophy (Kent Beck + DHH)

**Core Principle:** UI tests verify the full stack. If test says "creates project", verify it's actually in DB.

### MECE Test Design
Tests should be **MECE** (Mutually Exclusive, Collectively Exhaustive):
- **Mutually Exclusive**: Each test covers ONE distinct behavior, no overlap
- **Collectively Exhaustive**: Together, tests cover all behaviors of the feature

Example for a toggle feature:
- ✅ Test 1: Off → On (initial state, action, new state)
- ✅ Test 2: On → Off (opposite direction)
- ❌ Bad: Single test doing Off → On → Off (tests two things)

### What to Test
- ✅ User actions work (click, fill, submit)
- ✅ Data persists to DB (via Context functions, not Repo)
- ✅ Data displays to user
- ✅ Bugs you've encountered (test once, not everywhere)

### What NOT to Test
- ❌ Routes/URLs (`assert_path`) - implementation detail
- ❌ Heading text, flash messages - UI copy changes
- ❌ Validation in UI tests - backend concern
- ❌ Framework behavior - trust Phoenix/Ash
- ❌ Hypothetical bugs - test what you've seen break

### Helpers
- ✅ Simple navigation helpers (`visit_projects`) - transparent, reusable
- ❌ Assertion wrappers (`assert_project_exists`) - direct code is clearer

### Pattern
```elixir
test "user can create a project" do
  conn
  |> visit_projects()  # Helper for navigation
  |> click_link("New Project")
  |> fill_in("Name", with: "Launch")
  |> submit()
  |> assert_text("Launch")  # User sees it

  # ✅ Verify DB via Context (not Repo)
  assert Tasks.get_project_by_name("Launch")
end
```

### Edge Cases
Test once if you've seen the bug:
```elixir
# Regression test for multi-item delete bug
describe "multiple projects" do
  test "deletes correct project" do
    # Test this ONCE, not for every resource
  end
end
```

### DB Verification (Pragmatic Rule)
```elixir
# ✅ Prefer Context when function exists:
assert Tasks.get_project!(scope, project.id)

# ✅ Direct Repo OK for simple test verification:
assert Repo.get_by(Project, name: "test")  # Production doesn't need this query
refute Repo.get_by(Project, name: "deleted")

# When to use which:
# - Context: function exists, authorization matters, natural domain operation
# - Repo: simple verification, no auth needed, don't add function just for tests (YAGNI)
# - Ash: ALWAYS use Resource actions (Repo bypasses policies)
```

**Reference:** See project's `docs/how-to-test.md` for detailed examples

---

## Documentation Style

### dev-log.md
Document decisions, tradeoffs, and thought process for knowledge transfer.

### Inline Comments
- Explain **WHY**, not WHAT
- No status comments (no TODO, "will implement later", etc.)
- Keep concise
- For non-obvious code (especially FastHTML/Alpine/HTMX patterns): one-liner comments above the line

Example:
```python
# DaisyUI checkbox class + custom class for JS targeting
cls="checkbox bulk-select-checkbox",
# when checkbox changes, count ALL checked checkboxes in this table
**{"@change": "count = $root.querySelectorAll('.bulk-select-checkbox:checked').length"},
```

---

## Instructions to Claude

### Formatting
- Do not overuse bolding format
- Use H3/H4/H5/H6 for nested sections instead of bold headings
- Use simple bulleted lists without bolded phrases in each bullet
- Place comments directly above the specific line they explain, not at the beginning of a code block
- Always provide clickable file references with line numbers (e.g., `file.py:123`) so user can click to open in VSCode

### Code Changes
- Don't touch files unrelated to the current feature (no drive-by fixes or comment updates)
- Only modify what's necessary for the current task

### Communication
- **Avoid repeating same ideas in multiple places** - each concept should appear once
- **Always challenge and push back** - don't just execute, critique and question
- Point out better approaches and anti-patterns
- Help user learn through critical dialogue
- Show the user your chain of thought and help him understand how you arrived at your answer
- If you are showing something that the user is not familiar with, show him URLs of docs/blogs/videos to help him understand the idea thoroughly
- Don't write too much code or don't do too many changes at once - the user should be able to review your work in 2-3 minutes approx.
- If you are in a multi-step process, pause at each step, explain your reasoning, provide him the options and get to know his thought before taking the next step.

### Git Workflow
- ALWAYS ask approval before committing - show what will be committed and wait for explicit "commit" instruction
- For UI changes: take a screenshot before asking for commit approval so user can verify visually
- If user gives feedback or asks questions during review, answer them and wait for explicit commit approval
- Never auto-commit
- Commit messages: `RED:`, `GREEN:`, `REFACTOR:`, or `chore:` pattern
- No references to claude in commit message
- Commit message should match the task description in plan.md
- Update plan.md: check off task in GREEN commits
- Any setup/infrastructure work and docs update goes in `chore:` commits (never in RED commits)

### Experimental/Exploratory Coding
When figuring something out or exploring unfamiliar territory:
- Keep human in the loop at every step - get feedback/approval before proceeding
- Never do hacky or non-standard things just to "make it work"
- Follow proper practices for each tool/framework - maintainability over speed
- Write one line (or a few related lines) at a time, then pause for review
- Show how you would test the code and explain the testing process + expected output
- Slow down - be methodical and step-by-step
- avoid unnecesary complexity - i prefer simplicity, but sophistication and flexibility where it matters and
  make devx easier is always welcome.

### Process
- Every dev project should have plan.md, dev_log.md, and CLAUDE.md - prompt the user if they are not there
- plan.md tasks = user-facing features = GitHub issues. The
  RED-GREEN-REFACTOR breakdown happens during implementation, not in planning.
- Use Context7 MCP to check the latest docs for any library across languages
- In Phoenix projects, always check AGENTS.md and usage rules first before answering anything about code or starting to code
- always comment on things that are not understandable just by reading the code. e.g. current_date: str - not clear why date is stored as a str just by reading code.

---

## CSS / Tailwind / DaisyUI

### Use Standard Color Variables
Use DaisyUI's OKLCH color variables instead of hex colors:
```css
/* ❌ Bad - hardcoded hex */
background-color: #e0f2fe;

/* ✅ Good - DaisyUI primary at 10% opacity */
background-color: oklch(var(--p)/0.1);

/* Common patterns */
--p    /* primary */
--s    /* secondary */
--a    /* accent */
--n    /* neutral */
--b1   /* base-100 (background) */
--bc   /* base-content (text) */
```

In Tailwind arbitrary values:
```python
# Tab active state with primary color
":class": "isActive ? 'tab-active [--tab-bg:oklch(var(--p)/0.1)] [--tab-border-color:oklch(var(--p))]' : ''"
```

---

## Phoenix Projects

[Patterns will be added as we discover them]

---

## FastHTML Projects

### pytest-playwright Fixture Override
To override pytest-playwright's built-in `base_url` fixture, use `scope="session"`:
```python
# tests/conftest.py
@pytest.fixture(scope="session")  # Must be session-scoped!
def base_url():
    return os.getenv("BASE_URL", "http://localhost:5001")
```

### Alpine.js + HTMX Integration
When combining Alpine.js with HTMX for elements that get replaced:
- Use `style="display: none"` instead of `x-cloak` for elements that should start hidden after HTMX swap
- `x-cloak` works for initial page load, but fails on HTMX swaps (timing issue between cloak removal and x-show evaluation)
- `@click` handlers provide immediate feedback before HTMX round-trip completes