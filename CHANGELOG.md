# Changelog

本專案的所有重大變更都將記錄在此檔案中。

格式基於 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
並遵守 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)。

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
