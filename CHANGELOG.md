# Changelog

本專案的所有重大變更都將記錄在此檔案中。

格式基於 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
並遵守 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)。

## [v0.3.0] - 2026-06-22

> 全面相容 Starlette 1.x，同時維持與 Starlette 0.50.x 的向下相容，並持續支援透過 GitHub 安裝。

### 新增 (Added) ✨
-   **相依**: 新增明確的直接相依 `starlette>=0.40.0`（套件直接 import `starlette.datastructures` 與 `starlette.exceptions`），並維持 `fastapi>=0.128.0` 無上限，使套件可同時相容 Starlette 0.50.x 與 1.x。
-   **測試**: 新增首套 pytest 測試套件（40 個測試），涵蓋 `page` / `redirect` / `urlx_for` / scheme 調整 / error handlers / autoescape / 直接呼叫，並內建偵測舊式 `TemplateResponse` 退化的哨兵測試。
-   **CI**: 新增 GitHub Actions 跨版本 CI matrix，分別針對 Starlette 0.50.x（舊堆疊）與 1.x（最新）各執行一次完整測試。

### 變更 (Changed) 🔄
-   **相容性**: 將內部兩處 `Jinja2Templates.TemplateResponse` 由已棄用的舊式呼叫（將 `request` 放在 context dict 內）改為現代 `request`-first 簽名。Starlette 1.0 已移除舊式呼叫，此調整在 Starlette 0.50.x 與 1.x 皆可正常運作，且對使用者 API 無任何影響。
-   **文件**: `Usage.md` 新增 autoescape 行為說明。

### 安全性 (Security) 🔒
-   **XSS 防護**: `WebPage` 於初始化時強制啟用 Jinja2 autoescape（不分副檔名）。Starlette 1.0 將預設 autoescape 由「一律啟用」改為依副檔名的 `select_autoescape()`，導致 `.jinja2` 等非 `.html` 樣板在升級後不再自動轉義（潛在 XSS）。本次修正維持與舊版一致的安全行為；若需輸出原始 HTML，請於 Template 中改用 `{{ value | safe }}`。

## [v0.2.1] - 2026-02-21

### 修復 (Fixed) 🐛
-   **安全性/功能**: 修復 `page` 與 `redirect` 裝飾器中 `_adjust_scheme` 針對相對路徑 (Relative URLs) 會錯誤強制加上 `x-forwarded-proto` scheme 的問題。此修正確保相對路徑可以正常解析，同時避免非預期的路徑錯誤。

## [v0.2.0] - 2026-02-21

### 新增 (Added) ✨
-   **功能**: 新增 `redirect` 裝飾器，提供簡潔的 RedirectResponse 寫法，不僅支援自動轉換 HTTPS/WSS Scheme，更相容多種回傳型態：
    -   `str` | `starlette.URL` | `starlette.URLPath`: 作為目標 URL 並自動套用狀態碼
    -   `tuple[str, int]`: 可自訂覆寫預設狀態碼
    -   `RedirectResponse`: 向原生相容，自動修正 `location` Header 內的 Scheme
    -   其他 `Response`: 直接回傳

## [v0.1.0] - 2026-01-30

### 新增 (Added) 🚀
-   **核心**: `fastapi-webpage` 初始發布。
-   **功能**: 新增 `WebPage` 類別，用於管理 Jinja2 Template 與全域 Context。
-   **功能**: 新增 `urlx_for` 函式，支援 Reverse Proxy 環境下的 `x-forwarded-proto` 處理。
-   **功能**: 新增 `register_error_handlers` Middleware，支援混合式 JSON/HTML 錯誤回應。
-   **文件**: 新增完整的 README，包含快速開始 (Quick Start) 與使用範例。
-   **文件**: 為所有核心類別與函式新增詳細的 Docstrings。

### 變更 (Changed) 🔧
-   **設定**: 更新 `pyproject.toml` 設定，支援透過 `pip install git+...` 與 `uv add git+...` 進行安裝。
