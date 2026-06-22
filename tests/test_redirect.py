"""測試 @webpage.redirect 裝飾器的各種回傳型態與 scheme 調整。"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from conftest import build_client


def test_return_str_default_status(webpage):
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect()
    async def go(request: Request):
        return "/target"

    resp = build_client(app).get("/go", follow_redirects=False)
    assert resp.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert resp.headers["location"] == "/target"


def test_return_str_int_tuple(webpage):
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect()
    async def go(request: Request):
        return "/target", 303

    resp = build_client(app).get("/go", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/target"


def test_decorator_status_code_override(webpage):
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect(status_code=308)
    async def go(request: Request):
        return "/target"

    resp = build_client(app).get("/go", follow_redirects=False)
    assert resp.status_code == 308


def test_return_url_object(webpage):
    app = FastAPI()

    @app.get("/u", name="u")
    @webpage.redirect()
    async def u(request: Request):
        return request.url_for("u")  # 回傳 starlette URL 物件

    resp = build_client(app).get("/u", follow_redirects=False)
    assert resp.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert resp.headers["location"].endswith("/u")
    assert resp.headers["location"].startswith("http")


def test_return_urlpath_object(webpage):
    app = FastAPI()

    @app.get("/u", name="u")
    @webpage.redirect()
    async def u(request: Request):
        return request.app.url_path_for("u")  # 回傳 starlette URLPath (str 子類別)

    resp = build_client(app).get("/u", follow_redirects=False)
    assert resp.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert resp.headers["location"] == "/u"


def test_return_url_int_tuple(webpage):
    app = FastAPI()

    @app.get("/u", name="u")
    @webpage.redirect()
    async def u(request: Request):
        return request.url_for("u"), 303

    resp = build_client(app).get("/u", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"].endswith("/u")


def test_return_redirectresponse_scheme_adjusted(webpage):
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect()
    async def go(request: Request):
        return RedirectResponse(url="http://example.com/p")

    resp = build_client(app).get(
        "/go", headers={"x-forwarded-proto": "https"}, follow_redirects=False
    )
    assert resp.headers["location"] == "https://example.com/p"


def test_return_other_response_passthrough(webpage):
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect()
    async def go(request: Request):
        return JSONResponse({"ok": True})

    resp = build_client(app).get("/go")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_invalid_return_500(webpage):
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect()
    async def go(request: Request):
        return 123

    assert build_client(app).get("/go").status_code == 500


def test_scheme_http_to_https(webpage):
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect()
    async def go(request: Request):
        return "http://example.com/p"

    resp = build_client(app).get(
        "/go", headers={"x-forwarded-proto": "https"}, follow_redirects=False
    )
    assert resp.headers["location"] == "https://example.com/p"


def test_scheme_ws_to_wss(webpage):
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect()
    async def go(request: Request):
        return "ws://example.com/p"

    resp = build_client(app).get(
        "/go", headers={"x-forwarded-proto": "https"}, follow_redirects=False
    )
    assert resp.headers["location"] == "wss://example.com/p"


def test_relative_url_not_adjusted(webpage):
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect()
    async def go(request: Request):
        return "/relative"

    resp = build_client(app).get(
        "/go", headers={"x-forwarded-proto": "https"}, follow_redirects=False
    )
    assert resp.headers["location"] == "/relative"
