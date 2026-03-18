---
name: use-fastapi-webpage
description: This skill should be used when the user asks to "add a page route", "render a template", "set up redirect", "register error handlers", "inject global context", or mentions fastapi_webpage, WebPage, webpage.page, webpage.redirect, or FastAPI server-side rendering with Jinja2.
---

# fastapi-webpage

SSR package for FastAPI: decorator-style Jinja2 template rendering with reverse proxy-safe URLs and hybrid error handling.

## Quick Reference

| API | Description |
|---|---|
| `WebPage(template_dir, **global_ctx)` | Initialize Jinja2 environment and global context |
| `webpage.pre_context_update(dict)` | Update per-request dynamic context (use in middleware) |
| `webpage.webpage_context_update(dict)` | Update static global context |
| `@webpage.page("tmpl.html", status_code=200)` | Route decorator: handler returns `dict` → HTML |
| `@webpage.redirect(status_code=307)` | Route decorator: handler returns URL → RedirectResponse |
| `webpage("tmpl.html", request, context={}, status_code=200, headers={})` | Direct render without decorator |
| `register_error_handlers(app, webpage)` | Register global error handlers (auto JSON vs HTML) |

## Setup

```python
from pathlib import Path
from fastapi_webpage import WebPage, register_error_handlers

webpage = WebPage(Path("templates"), site_name="My Site")
register_error_handlers(app, webpage)  # optional, default template: error.jinja2
```

## `@webpage.page` Decorator

Handler **must** return `dict`. Other valid returns: `RedirectResponse` (scheme-fixed), any `Response` (pass-through).

```python
@app.get("/")
@webpage.page("index.html")
async def home(request: Request):
    return {"title": "Home", "items": get_items()}
```

## `@webpage.redirect` Decorator

| Return type | Behavior |
|---|---|
| `str` | Redirect with decorator's `status_code` |
| `(str, int)` | Redirect with custom status code |
| `URL \| URLPath` | Converted to `str`, same as above |
| `(URL \| URLPath, int)` | Same |
| `RedirectResponse` | Pass-through with scheme fix |
| Other `Response` | Pass-through unchanged |

```python
@app.post("/login")
@webpage.redirect(status_code=303)
async def login(request: Request):
    return "/dashboard"          # str

@app.post("/logout")
@webpage.redirect()
async def logout(request: Request):
    return "/login", 302         # (str, int)
```

## Auto-Injected Template Variables

`@webpage.page()` injects all four; direct `webpage()` call injects all **except `css_timestamp`**:

| Variable | `@webpage.page` | direct `webpage()` | Description |
|---|---|---|---|
| `request` | ✓ | ✓ | FastAPI Request object |
| `webpage` | ✓ | ✓ | Global WebPage context (includes `WebPage(**global_ctx)`) |
| `css_timestamp` | ✓ | **✗** | Unix timestamp for cache-busting — add manually if needed |
| `url_for` | ✓ | ✓ | Reverse proxy-aware `url_for` (respects `x-forwarded-proto`), injected as Jinja2 global |

```html
<title>{{ webpage.site_name }}</title>
<link rel="stylesheet" href="/static/app.css?v={{ css_timestamp }}">
<a href="{{ url_for('home') }}">Back to home</a>
```

## Context Merge Order

Priority from **lowest to highest** (later steps overwrite earlier ones):

```
1. route dict        [handler return value — applied first]
2. auto-injected     [request, webpage, css_timestamp]
3. pre_context       [pre_context_update() — applied last, wins over everything]
```

`url_for` is a Jinja2 environment global — always available, not part of the context dict merge.

Use `pre_context_update()` in middleware to inject per-request variables like `current_user` that must not be overridden by route handlers.

## Error Handlers

```python
register_error_handlers(app, webpage, error_templ_file="error.jinja2")
```

Intercepts `StarletteHTTPException`, `RequestValidationError`, and `Exception`.

Content negotiation: `Accept: application/json` → JSON; otherwise → HTML via `error_templ_file`.

Error template receives: `status_code` (int), `detail` (str), plus all auto-injected variables (`request`, `webpage`, `url_for`).

```html
<!-- templates/error.jinja2 -->
<h1>{{ status_code }}</h1>
<p>{{ detail }}</p>
<a href="{{ url_for('home') }}">Home</a>
```

## Common Mistakes

| Mistake | Fix |
|---|---|
| Handler does not return `dict` for `@page` | Return a `dict`; do not apply `@page` to non-HTML routes |
| Missing `request: Request` in handler | `@page` reads `request` from `kargs` — omitting it raises 500 |
| `register_error_handlers` not called | Browsers receive JSON errors instead of HTML error pages |
| URL still `http://` behind reverse proxy | Ensure the proxy forwards the `x-forwarded-proto` header |
| Non-dict passed to `pre_context_update` | Raises `ValueError` — always pass a `dict` |
| Missing `css_timestamp` in direct `webpage()` call | Direct calls do not inject `css_timestamp` — add `"css_timestamp": str(int(time.time()))` to context manually |
