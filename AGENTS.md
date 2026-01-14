# FastHTML Documentation Summary

FastHTML is a Python library that combines Starlette, Uvicorn, HTMX, and fastcore's FastTags to create "server-rendered hypermedia applications." Here are the key points:

## Core Characteristics

FastHTML is **not** compatible with FastAPI syntax and focuses on HTML-first applications rather than API services. It supports optional integrations with Pico CSS and fastlite SQLite, though other CSS frameworks and database libraries can be substituted.

## Key Limitations & Compatibility

The framework works with "JS-native web components and any vanilla JS library, but not with React, Vue, or Svelte." This is a fundamental architectural constraint.

## Essential Patterns

**Minimal structure**: Import from `fasthtml.common`, create an app with `fast_app()`, use the `@rt` decorator for routes, and call `serve()` to run the application.

**FastTags (FT)**: These are "m-expressions plus simple sugar" where positional parameters become children and named parameters become attributes. Special Python keywords require aliases (e.g., `_for` becomes `for`).

**Responses**: Route handlers can return FastTags (auto-rendered to HTML), Starlette responses (passed through), or JSON-serializable types.

## Advanced Features

- **Beforeware**: Functions running before route handlers for authentication/authorization
- **Form handling**: Dataclass type annotations automatically unpack form bodies into matching attributes
- **Database integration**: fastlite provides CRUD operations with optional SQLAlchemy compatibility
- **Real-time**: WebSocket and Server-Sent Events support via HTMX extensions
- **MonsterUI**: A component library offering Tailwind-based, shadcn-like functionality

## Development Notes

Use `serve()` automatically—no `if __name__ == "__main__"` needed. For titled pages, use `Titled()` which handles title tags and H1 elements.


## User Corrections

- Always runs tests before finishing the work. 
- Run playwright tests in headless mode. 
- use uv run pytest to run tests and uv run main.py to run the app.
- Use mailsiraj@gmail.com/123 for testing the functionality on the browser. choose hafiz "Siraj"