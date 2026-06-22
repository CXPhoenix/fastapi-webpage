"""測試 urlx_for（Jinja2 全域 url_for），透過真實 template 渲染驗證。"""

import re

from fastapi import FastAPI, Request

from conftest import build_client


def _href(text: str) -> str:
    m = re.search(r'id="self" href="([^"]*)"', text)
    assert m, f"找不到 self href，body=\n{text}"
    return m.group(1)


def _app(webpage):
    app = FastAPI()

    @app.get("/", name="index")
    @webpage.page("index.jinja2")
    async def home(request: Request):
        return {"msg": "hi"}

    return app


def test_url_for_default_scheme(webpage):
    resp = build_client(_app(webpage)).get("/")
    href = _href(resp.text)
    assert href.startswith("http://")  # TestClient 預設 http


def test_url_for_forwarded_https(webpage):
    resp = build_client(_app(webpage)).get("/", headers={"x-forwarded-proto": "https"})
    href = _href(resp.text)
    assert href.startswith("https://")


def test_url_for_forwarded_ws(webpage):
    resp = build_client(_app(webpage)).get("/", headers={"x-forwarded-proto": "ws"})
    href = _href(resp.text)
    assert href.startswith("ws://")  # ws 在白名單內，直接採用


def test_url_for_rejects_dangerous_scheme(webpage):
    """不在白名單的 scheme（如 javascript）必須被強制改為 https。"""
    resp = build_client(_app(webpage)).get(
        "/", headers={"x-forwarded-proto": "javascript"}
    )
    href = _href(resp.text)
    assert href.startswith("https://")
    assert "javascript" not in href
