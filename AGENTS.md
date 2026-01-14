# FastHTML Documentation Summary

FastHTML is a Python library that combines Starlette, Uvicorn, HTMX, and fastcore's FastTags to create "server-rendered hypermedia applications." Here are the key points:

## Core Characteristics

FastHTML is **not** compatible with FastAPI syntax and focuses on HTML-first applications rather than API services. 

## Key Limitations & Compatibility

The framework works with "JS-native web components and any vanilla JS library, but not with React, Vue, or Svelte." This is a fundamental architectural constraint.

## Essential Patterns

**Minimal structure**: Import from `fasthtml.common`, create an app with `fast_app()`, use the `@rt` decorator for routes, and call `serve()` to run the application.

**FastTags (FT)**: These are "m-expressions plus simple sugar" where positional parameters become children and named parameters become attributes. Special Python keywords require aliases (e.g., `_for` becomes `for`).

**Responses**: Route handlers can return FastTags (auto-rendered to HTML), Starlette responses (passed through), or JSON-serializable types.

## Advanced Features

- **Beforeware**: Functions running before route handlers for authentication/authorization
- auth is hafiz_id not user_id - user_id is like an account and hafiz_id is the real user grouped under the user. 
- **Form handling**: Dataclass type annotations automatically unpack form bodies into matching attributes
- **Database integration**: fastlite provides CRUD operations
- **MonsterUI**: A component library offering Tailwind-based, shadcn-like functionality


## User Corrections

- Always runs tests before finishing the work. 
- use uv run pytest to run tests and uv run main.py to run the app.
- Use mailsiraj@gmail.com for testing the functionality on the browser. query the sqlite prod DB for password. choose hafiz "Siraj"
- example query - sqlite3 data/quran_v10.db "SELECT email, password FROM users WHERE email = 'mailsiraj@gmail.com' LIMIT 1;"