# CLAUDE.md - Phoenix LiveView Rebuild

**Global Instructions**: See `.claude/CLAUDE.global.md` (symlinked to `~/.claude/CLAUDE.md`) for universal workflow rules and Phoenix-specific patterns.

**Current Goal**: Rebuilding Quran SRS using Phoenix LiveView + Ash Framework with pure TDD. The `_reference/` folder contains the original FastHTML implementation for business logic reference only - don't copy-paste, use as specification.

---

## Testing Strategy

**PhoenixTest**: Unified API for testing both controllers and LiveView (no browser overhead).

---

## Running Tests

**Terminal 1: Start server**
```bash
mix phx.server
```

**Terminal 2: Run tests (continuous watch mode)**
```bash
mix test.interactive
```

---

## Project-Specific Rules

- Never reference FastHTML in commits (future devs won't see _reference/)

---

## Lessons Learnt

-
