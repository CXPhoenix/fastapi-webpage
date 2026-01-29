# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added 🚀
-   **Core**: Initial release of `fastapi-webpage`.
-   **Feature**: `WebPage` class for managing Jinja2 templates and global context.
-   **Feature**: `urlx_for` function with `x-forwarded-proto` support for reverse proxies.
-   **Feature**: `register_error_handlers` middleware for hybrid JSON/HTML error responses.
-   **Docs**: Comprehensive README with Quick Start and usage examples.
-   **Docs**: Detail docstrings for all core classes and functions.

### Changed 🔧
-   **Config**: Updated `pyproject.toml` to support installation via `pip install git+...` and `uv add git+...`.
