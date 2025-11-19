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

## Documentation Style

### dev-log.md
Document decisions, tradeoffs, and thought process for knowledge transfer.

### Inline Comments
- Explain **WHY**, not WHAT
- No status comments (no TODO, "will implement later", etc.)
- Keep concise

---

## Instructions to Claude

### Formatting
- Do not overuse bolding format
- Use H3/H4/H5/H6 for nested sections instead of bold headings
- Use simple bulleted lists without bolded phrases in each bullet

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
- ALWAYS ask approval before committing - show what will be committed and wait
- Never auto-commit
- Commit messages: `RED:`, `GREEN:`, `REFACTOR:`, or `chore:` pattern
- No references to claude in commit message
- Commit message should match the task description in plan.md
- Update plan.md: check off task in GREEN commits
- Any setup/infrastructure work and docs update goes in `chore:` commits (never in RED commits)

### Process
- Every dev project should have plan.md, dev_log.md, and CLAUDE.md - prompt the user if they are not there
- plan.md tasks = user-facing features = GitHub issues. The
  RED-GREEN-REFACTOR breakdown happens during implementation, not in planning.
- Use Context7 MCP to check the latest docs for any library across languages
- In Phoenix projects, always check AGENTS.md and usage rules first before answering anything about code or starting to code

---

## Phoenix Projects

[Patterns will be added as we discover them]

---

## FastHTML Projects

[Patterns will be added as we discover them]
