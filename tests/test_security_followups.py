"""v0.3.1 follow-up：__call__ 可變預設參數修正，與 redirect 危險 scheme 阻擋。"""

import inspect

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from fastapi_webpage import WebPage
from conftest import build_client


# --- Follow-up 1：__call__ 可變預設參數 / 呼叫者 dict 隔離 ---

def test_call_default_context_is_none():
    """靜態守衛：__call__ 的 context 預設必須是 None（不可為可變的 {}）。"""
    sig = inspect.signature(WebPage.__call__)
    assert sig.parameters["context"].default is None


def test_call_does_not_mutate_caller_dict(webpage):
    """webpage(...) 不得把 request/webpage/pre_context 寫回呼叫者傳入的 dict。"""
    app = FastAPI()
    captured = {}

    @app.get("/", name="index")
    async def home(request: Request):
        caller_ctx = {"msg": "X"}
        resp = webpage("index.jinja2", request, caller_ctx)
        captured["keys"] = set(caller_ctx.keys())
        return resp

    build_client(app).get("/")
    assert captured["keys"] == {"msg"}


def test_call_no_context_repeatable(webpage):
    """連續以無 context 參數呼叫應穩定運作，不共用殘留狀態。"""
    app = FastAPI()

    @app.get("/", name="index")
    async def home(request: Request):
        return webpage("index.jinja2", request)

    client = build_client(app)
    assert client.get("/").status_code == 200
    assert client.get("/").status_code == 200


# --- Follow-up 2：redirect / page 阻擋危險 scheme ---

@pytest.mark.parametrize(
    "target",
    [
        "javascript:alert(1)",
        "JavaScript:alert(1)",          # 大小寫不敏感
        "data:text/html,<script>1</script>",
        "vbscript:msgbox(1)",
    ],
)
def test_redirect_str_rejects_dangerous_scheme(webpage, target):
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect()
    async def go(request: Request):
        return target

    assert build_client(app).get("/go").status_code == 500


def test_redirect_tuple_rejects_dangerous_scheme(webpage):
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect()
    async def go(request: Request):
        return "data:text/html,x", 303

    assert build_client(app).get("/go").status_code == 500


def test_page_redirectresponse_rejects_dangerous_scheme(webpage):
    app = FastAPI()

    @app.get("/", name="index")
    @webpage.page("index.jinja2")
    async def home(request: Request):
        return RedirectResponse(url="javascript:alert(1)")

    assert build_client(app).get("/").status_code == 500


def test_redirect_relative_still_allowed(webpage):
    """相對 URL（無 scheme、無 netloc）不得被誤判為危險，須正常 redirect。"""
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect()
    async def go(request: Request):
        return "/safe/path?next=/x"

    resp = build_client(app).get("/go", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/safe/path?next=/x"


def test_redirect_absolute_web_url_still_allowed(webpage):
    """合法的 http(s) 絕對 URL 不受影響。"""
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect()
    async def go(request: Request):
        return "https://example.com/p"

    resp = build_client(app).get("/go", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "https://example.com/p"
