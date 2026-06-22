"""測試 @webpage.page 裝飾器。"""

import warnings

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, RedirectResponse

from conftest import build_client


def test_dict_renders_200(webpage):
    app = FastAPI()

    @app.get("/", name="index")
    @webpage.page("index.jinja2")
    async def home(request: Request):
        return {"msg": "hi"}

    resp = build_client(app).get("/")
    assert resp.status_code == 200
    assert 'id="msg">hi' in resp.text
    assert "TestSite" in resp.text  # webpage 全域 context 可用


def test_custom_status_code(webpage):
    app = FastAPI()

    @app.get("/", name="index")
    @webpage.page("index.jinja2", status_code=201)
    async def home(request: Request):
        return {"msg": "hi"}

    assert build_client(app).get("/").status_code == 201


def test_context_merge_precedence(webpage):
    """優先序：pre_context > 自動注入 > handler dict。"""
    app = FastAPI()
    webpage.pre_context_update({"msg": "PRE"})

    @app.get("/", name="index")
    @webpage.page("index.jinja2")
    async def home(request: Request):
        return {"msg": "HANDLER", "foo": "bar"}

    text = build_client(app).get("/").text
    assert 'id="msg">PRE' in text  # pre_context 勝過 handler
    assert 'id="foo">bar' in text  # handler 專屬鍵保留
    assert 'id="css">' in text and 'id="css">nocss' not in text  # 自動注入 css_timestamp


def test_no_deprecation_warning_on_render(webpage):
    """跨版本哨兵：現代 TemplateResponse 呼叫不得觸發 Starlette 的舊式棄用警告。

    將該特定棄用訊息升級為錯誤；若 render 退回舊式呼叫，server 端會拋錯，
    在 raise_server_exceptions=False 下轉為 500，使本測試失敗。
    """
    app = FastAPI()

    @app.get("/", name="index")
    @webpage.page("index.jinja2")
    async def home(request: Request):
        return {"msg": "hi"}

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "error",
            message="The .TemplateResponse. now requires the .request. argument",
            category=DeprecationWarning,
        )
        resp = build_client(app).get("/")
    assert resp.status_code == 200


def test_redirect_response_return_scheme_adjusted(webpage):
    app = FastAPI()

    @app.get("/", name="index")
    @webpage.page("index.jinja2")
    async def home(request: Request):
        return RedirectResponse(url="http://example.com/p")

    resp = build_client(app).get(
        "/", headers={"x-forwarded-proto": "https"}, follow_redirects=False
    )
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "https://example.com/p"


def test_redirect_response_relative_passthrough(webpage):
    app = FastAPI()

    @app.get("/", name="index")
    @webpage.page("index.jinja2")
    async def home(request: Request):
        return RedirectResponse(url="/local")

    resp = build_client(app).get(
        "/", headers={"x-forwarded-proto": "https"}, follow_redirects=False
    )
    assert resp.headers["location"] == "/local"  # 相對 URL 不被改 scheme


def test_other_response_passthrough(webpage):
    app = FastAPI()

    @app.get("/", name="index")
    @webpage.page("index.jinja2")
    async def home(request: Request):
        return PlainTextResponse("RAW")

    resp = build_client(app).get("/")
    assert resp.status_code == 200
    assert resp.text == "RAW"


def test_invalid_return_500(webpage):
    app = FastAPI()

    @app.get("/", name="index")
    @webpage.page("index.jinja2")
    async def home(request: Request):
        return 42  # 非 dict / Response

    assert build_client(app).get("/").status_code == 500


def test_missing_request_param_500(webpage):
    app = FastAPI()

    @app.get("/", name="index")
    @webpage.page("index.jinja2")
    async def home():  # 沒有 request 參數
        return {"msg": "hi"}

    assert build_client(app).get("/").status_code == 500


def test_sync_handler_supported(webpage):
    """handler 為同步函式（非 async）也應正常渲染。"""
    app = FastAPI()

    @app.get("/", name="index")
    @webpage.page("index.jinja2")
    def home(request: Request):
        return {"msg": "sync"}

    resp = build_client(app).get("/")
    assert resp.status_code == 200
    assert 'id="msg">sync' in resp.text
