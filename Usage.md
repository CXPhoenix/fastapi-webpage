# FastAPI WebPage — Usage Guide

> 本文件為詳細 API 參考手冊。快速入門請參閱 [README.md](README.md)。
> This document is the detailed API reference. For a quick start, see [README.md](README.md).

---

## 安裝 / Installation

```bash
# uv (推薦 / recommended)
uv add git+https://github.com/cxphoenix/fastapi-webpage.git

# pip
pip install git+https://github.com/cxphoenix/fastapi-webpage.git
```

**需求 / Requirements:** Python 3.13+, FastAPI ≥ 0.128.0

---

## 公開匯出 / Public Exports

```python
from fastapi_webpage import WebPage, register_error_handlers
```

---

## `WebPage` 類別 / Class

### 建構子 / Constructor

```python
WebPage(
    template_directory: Path | PathLike | str,
    **global_context: Any,
)
```

| 參數 / Parameter | 型態 / Type | 說明 / Description |
|---|---|---|
| `template_directory` | `Path \| PathLike \| str` | Jinja2 Template 目錄路徑 / Path to templates directory |
| `**global_context` | `Any` | 全域 Context 變數，在所有頁面可用 / Global variables available in every template |

```python
from pathlib import Path
from fastapi_webpage import WebPage

webpage = WebPage(
    template_directory=Path("templates"),
    site_name="My Site",
    version="1.0.0",
)
```

---

### `pre_context` 屬性 / Property

```python
webpage.pre_context  # -> dict
```

讀取目前的 pre-context 字典（唯讀）。
Read-only access to the current pre-context dictionary.

---

### `pre_context_update(value: dict)`

動態更新 pre-context。常用於 Middleware 中，為每個請求注入動態變數。
Dynamically update pre-context. Typically called in middleware to inject per-request variables.

```python
@app.middleware("http")
async def inject_user(request: Request, call_next):
    webpage.pre_context_update({"current_user": get_user(request)})
    return await call_next(request)
```

**Raises:** `ValueError` — 若 `value` 不是 `dict` / if `value` is not a `dict`.

> **注意 / Note:** pre-context 在請求間是共享狀態 (shared mutable state)，適合每次請求覆寫的動態變數。靜態全域變數請改用 `global_context` 建構子參數或 `webpage_context_update()`。
> pre-context is shared mutable state across requests. Use it for dynamic per-request variables that get overwritten each request. For static globals, use the constructor or `webpage_context_update()`.

---

### `webpage_context` 屬性 / Property

```python
webpage.webpage_context  # -> dict
```

讀取目前的全域 webpage_context 字典（唯讀）。
Read-only access to the global webpage context dictionary.

---

### `webpage_context_update(value: dict)`

更新全域 webpage_context。
Update the global webpage context.

```python
webpage.webpage_context_update({"feature_flags": {"dark_mode": True}})
```

**Raises:** `ValueError` — 若 `value` 不是 `dict` / if `value` is not a `dict`.

---

### `@webpage.page(template_file, status_code=200)` 裝飾器 / Decorator

將路由 Handler 的回傳值渲染為 HTML 頁面。
Renders the route handler's return value as an HTML page.

```python
page(
    template_file: PathLike | str,
    status_code: int = 200,
) -> Awaitable
```

| 參數 / Parameter | 預設 / Default | 說明 / Description |
|---|---|---|
| `template_file` | (必填) | Template 檔名，相對於 `template_directory` / Template filename relative to `template_directory` |
| `status_code` | `200` | HTTP 狀態碼 / HTTP status code |

**Handler 回傳型態 / Handler return types:**

| 回傳值 / Return value | 行為 / Behavior |
|---|---|
| `dict` | 注入 Context 並渲染 Template / Injects context and renders template |
| `RedirectResponse` | 透傳並自動修正 Scheme / Passed through with scheme adjustment |
| 其他 `Response` subclass | 直接透傳 / Passed through unchanged |
| 其他型態 / Other types | 拋出 `500 Internal Server Error` |

```python
@app.get("/")
@webpage.page("index.html")
async def home(request: Request):
    return {"title": "首頁", "items": [...]}

@app.get("/dashboard")
@webpage.page("dashboard.html", status_code=200)
async def dashboard(request: Request, user_id: int):
    return {"user": get_user(user_id)}
```

**⚠️ 注意 / Note:** Handler 的第一個參數必須是 `request: Request`，否則 Decorator 會拋出 `500` 錯誤。
The handler must accept `request: Request`, otherwise the decorator raises a `500` error.

---

### `@webpage.redirect(status_code=307)` 裝飾器 / Decorator

將路由 Handler 的回傳值作為重新導向目標，並自動修正 Reverse Proxy 的 Scheme 問題。
Redirects based on the handler's return value, with automatic scheme correction for reverse proxies.

```python
redirect(
    status_code: int = 307,  # HTTP 307 Temporary Redirect
) -> Awaitable
```

**Handler 回傳型態 / Handler return types:**

| 回傳值 / Return value | 行為 / Behavior |
|---|---|
| `str` | 以 Decorator 的 `status_code` 重新導向 / Redirects with decorator's `status_code` |
| `URL \| URLPath` | 轉為 `str` 後同上 / Converted to `str` then same as above |
| `(str, int)` | 以 tuple 內的狀態碼重新導向 / Redirects with the status code from the tuple |
| `(URL \| URLPath, int)` | 同上 / Same as above |
| `RedirectResponse` | 透傳並自動修正 Location Header 的 Scheme / Passed through with scheme fix |
| 其他 `Response` subclass | 直接透傳 / Passed through unchanged |
| 其他型態 / Other types | 拋出 `500 Internal Server Error` |

```python
from fastapi.responses import RedirectResponse

# 回傳 str — 使用 Decorator 的 status_code (303)
@app.post("/login")
@webpage.redirect(status_code=303)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    if authenticate(form_data):
        return "/dashboard"
    return "/login?error=1"

# 回傳 tuple — 動態指定狀態碼
@app.post("/logout")
@webpage.redirect()
async def logout(request: Request):
    return "/login", 302

# 回傳 RedirectResponse — 向後相容
@app.get("/old-url")
@webpage.redirect()
async def legacy(request: Request):
    return RedirectResponse(url="/new-url")

# 使用 url_for — 支援 URL / URLPath 物件
@app.get("/go-home")
@webpage.redirect()
async def go_home(request: Request):
    return request.url_for("home"), 303
```

---

### `webpage(template_file, request, context={}, **kargs)` 直接呼叫 / Direct Call

不使用裝飾器，直接渲染 Template。適合在 Dependency 或 Error Handler 中使用。
Render a template directly without a decorator. Useful inside dependencies or error handlers.

```python
__call__(
    template_file: PathLike | str,
    request: Request,
    context: dict[str, Any] = {},
    **kargs,
) -> TemplateResponse
```

| 參數 / Parameter | 說明 / Description |
|---|---|
| `template_file` | Template 檔名 / Template filename |
| `request` | FastAPI `Request` 物件 / FastAPI `Request` object |
| `context` | 額外的 Template 變數 / Additional template variables |
| `status_code` (karg) | HTTP 狀態碼 / HTTP status code |
| `headers` (karg) | 自訂 HTTP Headers / Custom HTTP headers |

```python
# 手動渲染 404 頁面
async def custom_404(request: Request):
    return webpage(
        "404.html",
        request,
        context={"message": "找不到頁面"},
        status_code=404,
        headers={"Cache-Control": "no-store"},
    )
```

---

## `register_error_handlers(app, webpage, error_templ_file="error.jinja2")`

為 FastAPI App 註冊全域的錯誤處理器，根據 `Accept` Header 自動選擇回應格式。
Registers global error handlers on the FastAPI app, auto-selecting response format based on the `Accept` header.

```python
register_error_handlers(
    app: FastAPI,
    webpage: WebPage,
    error_templ_file: str = "error.jinja2",
)
```

| 參數 / Parameter | 預設 / Default | 說明 / Description |
|---|---|---|
| `app` | (必填) | FastAPI App 實例 / FastAPI app instance |
| `webpage` | (必填) | 已初始化的 `WebPage` 實例 / Initialized `WebPage` instance |
| `error_templ_file` | `"error.jinja2"` | 錯誤頁面 Template 檔名 / Error page template filename |

**Content Negotiation 行為 / Behavior:**

| `Accept` Header | 回應格式 / Response Format |
|---|---|
| 包含 `application/json` / Contains `application/json` | JSON (`{"detail": "..."}`) |
| 其他 / Other | HTML (使用 `error_templ_file` / using `error_templ_file`) |

**攔截的例外 / Intercepted exceptions:**

- `StarletteHTTPException` (HTTP 4xx / 5xx)
- `RequestValidationError` (422 Unprocessable Entity)
- `Exception` (所有未捕獲的例外 / All uncaught exceptions → 500)

```python
from fastapi import FastAPI
from fastapi_webpage import WebPage, register_error_handlers

app = FastAPI()
webpage = WebPage(Path("templates"), site_name="My Site")
register_error_handlers(app, webpage)                        # 使用預設 error.jinja2
register_error_handlers(app, webpage, "errors/custom.html") # 使用自訂 Template
```

**錯誤 Template 可用的 Context 變數 / Available context variables in error template:**

| 變數 / Variable | 型態 / Type | 說明 / Description |
|---|---|---|
| `status_code` | `int` | HTTP 狀態碼 / HTTP status code |
| `detail` | `str` | 錯誤訊息 / Error message |
| `request` | `Request` | FastAPI Request 物件 / FastAPI Request object |
| `webpage` | `dict` | 全域 WebPage Context / Global WebPage context |
| `css_timestamp` | `str` | 快取破壞時間戳 / Cache-busting timestamp |
| `url_for` | `callable` | Reverse Proxy 修正版的 URL 函式 / Proxy-aware URL function |

```html
<!-- templates/error.jinja2 -->
<!DOCTYPE html>
<html>
<body>
  <h1>{{ status_code }} — 發生錯誤</h1>
  <p>{{ detail }}</p>
  <a href="{{ url_for('home') }}">返回首頁</a>
</body>
</html>
```

---

## Template 自動注入變數 / Auto-Injected Template Variables

當使用 `@webpage.page()` 或直接呼叫 `webpage()` 時，以下變數會自動注入：
These variables are automatically available in every template rendered via `@webpage.page()` or `webpage()`:

| 變數 / Variable | 型態 / Type | 說明 / Description |
|---|---|---|
| `request` | `Request` | FastAPI Request 物件 / FastAPI Request object |
| `webpage` | `dict` | 全域 WebPage Context（含建構子的 `global_context`）/ Global WebPage context (includes constructor's `global_context`) |
| `css_timestamp` | `str` | Unix 時間戳字串，可附加至靜態資源 URL 用於快取破壞 / Unix timestamp string for cache-busting static assets |
| `url_for` | `callable` | Reverse Proxy 修正版的 `url_for`，自動偵測 `x-forwarded-proto` / Proxy-aware `url_for` that respects `x-forwarded-proto` |

```html
<!-- 存取全域 Context -->
<title>{{ webpage.site_name }}</title>

<!-- 快取破壞 -->
<link rel="stylesheet" href="/static/app.css?v={{ css_timestamp }}">

<!-- Reverse Proxy 安全的 URL 生成 -->
<a href="{{ url_for('dashboard') }}">Dashboard</a>
```

---

## Context 合併順序 / Context Merge Order

Template 中的變數優先順序（後者覆蓋前者 / later overrides earlier）：

```
自動注入 (request, webpage, css_timestamp, url_for)
    ↓ 被 pre_context 覆蓋
pre_context  (由 pre_context_update() 設定)
    ↓ 被 route context 覆蓋
Route Context  (Handler 回傳的 dict)
```

實際上在 `page()` 裝飾器內的合併流程：

```python
context = handler_return_dict          # Route 回傳值
context.update({                       # 注入系統變數
    "request": request,
    "webpage": self._webpage_context,
    "css_timestamp": str(int(time.time())),
})
context.update(self._pre_context)      # pre_context 最後合併（優先級最高）
```

> **重要 / Important:** `pre_context` 的優先級高於 Route 回傳的 dict，因此 Middleware 注入的變數（如 `current_user`）可以安全地覆蓋 Handler 的同名變數。
> `pre_context` has higher priority than the route's dict, so middleware-injected variables (e.g., `current_user`) safely override handler variables with the same name.

---

## Reverse Proxy 支援 / Reverse Proxy Support

當服務部署於 Cloudflare、Nginx、Traefik 等 Reverse Proxy 後方，外部請求使用 HTTPS，但 Proxy 轉發至後端時可能使用 HTTP，導致生成的 URL scheme 不正確。

FastAPI WebPage 透過 `x-forwarded-proto` Header 自動修正此問題：

| 原始 Scheme / Original | `x-forwarded-proto` | 修正後 / Fixed |
|---|---|---|
| `http` | `https` | `https` |
| `ws` | `wss` | `wss` |
| `https` | (不存在) | `https`（不變） |
| 其他無效值 | 任何值 | `https`（安全預設值） |

**相對路徑不受影響 / Relative paths are unaffected:** `/dashboard`、`/api/v1/users` 等相對路徑不會被修改。只有包含 `netloc`（主機名稱）的絕對 URL 才會進行 Scheme 修正。

This auto-correction applies to:
- `url_for()` in templates
- `@webpage.page()` decorator — when handler returns `RedirectResponse`
- `@webpage.redirect()` decorator — all redirect target URLs

---

## 完整範例 / Full Example

```python
from pathlib import Path
from fastapi import Depends, FastAPI, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_webpage import WebPage, register_error_handlers

app = FastAPI()
webpage = WebPage(
    template_directory=Path("templates"),
    site_name="My App",
    version="1.0",
)
register_error_handlers(app, webpage)


# --- Middleware: inject current user per request ---
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    user = await get_current_user(request)
    webpage.pre_context_update({"current_user": user})
    return await call_next(request)


# --- Page route ---
@app.get("/")
@webpage.page("index.html")
async def home(request: Request):
    return {"title": "首頁", "posts": get_recent_posts()}


# --- Redirect route ---
@app.post("/login")
@webpage.redirect(status_code=303)
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    if authenticate(form.username, form.password):
        return "/dashboard"
    return "/login?error=1"


# --- Direct render (no decorator) ---
@app.get("/maintenance")
async def maintenance(request: Request):
    return webpage(
        "maintenance.html",
        request,
        context={"message": "系統維護中"},
        status_code=503,
    )
```
