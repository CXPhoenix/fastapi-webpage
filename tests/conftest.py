"""共用測試 fixtures。

測試使用 FastAPI 的 TestClient（底層為 httpx）驗證 WebPage 套件在
Starlette 0.50.x 與 1.x 上的行為一致。`raise_server_exceptions=False`
讓伺服器端 500／錯誤路徑回傳真正的 Response 而非直接 re-raise，方便斷言。
"""

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_webpage import WebPage

TEMPLATES_DIR = Path(__file__).parent / "templates"


@pytest.fixture
def webpage() -> WebPage:
    """每個測試取得一個全新的 WebPage（避免 pre_context 跨測試外洩）。"""
    return WebPage(TEMPLATES_DIR, site="TestSite")


def build_client(app: FastAPI) -> TestClient:
    """以 raise_server_exceptions=False 建立 TestClient，便於驗證 500 等錯誤路徑。"""
    return TestClient(app, raise_server_exceptions=False)
