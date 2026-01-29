# FastAPI WebPage

FastAPI WebPage 是一個專為 FastAPI 設計的輕量級網頁渲染輔助套件，旨在簡化 Jinja2 Template 的整合與使用。它提供了直覺的 Decorator 風格 API、全域 Context 管理，以及智慧的 Content Negotiation 錯誤處理機制。

## ✨ 特色 (Features)

-   **Decorator 風格 API**: 使用 `@webpage_app.page` 裝飾器輕鬆將 API 回傳資料渲染為 HTML 頁面。
-   **全域 Context 管理**: 支援 `webpage_context` (全域變數) 與 `pre_context` (預處理變數)，方便在多個頁面間共享資料（如使用者資訊、網站設定）。
-   **智慧 URL 產生**: 內建 `urlx_for`，自動支援 Reverse Proxy (如 Cloudflare, Traefik, Nginx) 的 `X-Forwarded-Proto` Header，解決 Protocol Mismatch 問題。
-   **混合錯誤處理 (Hybrid Error Handling)**: `register_error_handlers` 可根據 Client 的 `Accept` Header 自動判斷並回傳 JSON 錯誤訊息或渲染友善的 HTML 錯誤頁面。

## 📦 安裝 (Installation)

目前你可以透過 GitHub 直接安裝此套件：

### 使用 uv (推薦)

```bash
uv add git+https://github.com/user/fastapi-webpage.git
```

### 使用 pip

```bash
pip install git+https://github.com/user/fastapi-webpage.git
```

## 🚀 快速開始 (Quick Start)

### 1. 初始化 WebPage

首先，你需要建立一個 FastAPI App 並初始化 `WebPage` 實例。

```python
from fastapi import FastAPI, Request
from fastapi_webpage import WebPage, register_error_handlers
from pathlib import Path

app = FastAPI()

# 初始化 WebPage，指定 Template 目錄
# global_context 中的變數會在所有 Template 中可用
webpage = WebPage(
    template_directory=Path("templates"),
    site_name="My Awesome Site"
)

# (選用) 註冊錯誤處理，自動切換 JSON/HTML 錯誤回應
register_error_handlers(app, webpage)
```

### 2. 建立頁面 Route

使用 `webpage.page` Decorator 來包裝你的 Route Handler。Handler 只需要回傳一個 `dict`，WebPage 會自動將其作為 Context 傳入 Template。

```python
@app.get("/")
@webpage.page("index.html")  # 指定要渲染的 Template 檔案
async def sensitive_url_route(request: Request):
    # 回傳的 dict 會被合併到 Jinja2 Context 中
    return {
        "title": "首頁",
        "message": "Hello, FastAPI WebPage!"
    }
```

**對應的 `templates/index.html`:**

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }} - {{ webpage.site_name }}</title>
</head>
<body>
    <h1>{{ message }}</h1>
    <p>歡迎來到 {{ webpage.site_name }}</p>
</body>
</html>
```

注意：`{{ webpage.site_name }}` 來自初始化時傳入的 `global_context`，在 Template 中透過 `webpage` 變數存取。

### 3. 動態更新 Context

你可以在程式執行過程中動態更新全域 Context，例如在 Middleware 中注入使用者資訊。

```python
@app.middleware("http")
async def add_user_middleware(request: Request, call_next):
    # 範例：在 pre_context 中注入當前時間或使用者狀態
    webpage.pre_context_update({"current_user": "Guest"})
    response = await call_next(request)
    return response
```

## 📖 進階功能

### 錯誤處理 (Error Handling)

`register_error_handlers` 函式提供了智慧的錯誤處理機制。

-   **API Client (如 Postman, Frontend Fetch)**: 當 Header 包含 `Accept: application/json` 時，發生錯誤會回傳標準的 JSON 格式 (例如 `{"detail": "Not Found"}`)。
-   **瀏覽器使用者**: 當發生錯誤時 (如 404, 500)，會自動渲染指定的錯誤 Template (預設為 `error.jinja2`)。

**error.jinja2 範例:**

```html
<!DOCTYPE html>
<html>
<body>
    <h1>發生錯誤 ({{ status_code }})</h1>
    <p>{{ detail }}</p>
    <a href="{{ url_for('sensitive_url_route') }}">回首頁</a>
</body>
</html>
```

### URL 在 Reverse Proxy 後的處理

在 Template 中使用 `url_for` 時，若你的應用程式部署在 Reverse Proxy (如 Nginx, Cloudflare) 後方，且 Proxy 透過 HTTP 與 App溝通但對外提供 HTTPS，標準的 `url_for` 可能會產生 `http://` 的連結。

FastAPI WebPage 內建擴充的 `url_for` (在 Template 中直接使用 `url_for` 即可)，會自動檢查 `x-forwarded-proto` Header 並修正 URL Scheme，確保連結正確指向 `https://`。

## 🛠️ 開發與貢獻

本專案使用 `uv` 進行依賴管理。

```bash
# 安裝依賴
uv sync

# 執行測試 (若有 Setup 測試)
uv run pytest
```

## 授權 (License)

[LICENSE](./LICENSE)
