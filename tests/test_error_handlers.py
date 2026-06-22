"""測試 register_error_handlers 的 content negotiation（HTML vs JSON）。"""

from fastapi import FastAPI, HTTPException, Request

from fastapi_webpage import register_error_handlers
from conftest import build_client


def _app(webpage):
    app = FastAPI()
    register_error_handlers(app, webpage)

    @app.get("/boom")
    async def boom(request: Request):
        raise HTTPException(status_code=404, detail="nope")

    @app.get("/items/{n}")
    async def items(request: Request, n: int):
        return {"n": n}

    @app.get("/crash")
    async def crash(request: Request):
        raise ValueError("kaboom")

    return app


def test_httpexception_html(webpage):
    resp = build_client(_app(webpage)).get("/boom", headers={"accept": "text/html"})
    assert resp.status_code == 404
    assert 'id="code">404' in resp.text
    assert 'id="detail">nope' in resp.text


def test_httpexception_json(webpage):
    resp = build_client(_app(webpage)).get(
        "/boom", headers={"accept": "application/json"}
    )
    assert resp.status_code == 404
    assert resp.json() == {"detail": "nope"}


def test_validation_error_html(webpage):
    resp = build_client(_app(webpage)).get(
        "/items/abc", headers={"accept": "text/html"}
    )
    assert resp.status_code == 422
    assert 'id="code">422' in resp.text


def test_validation_error_json(webpage):
    resp = build_client(_app(webpage)).get(
        "/items/abc", headers={"accept": "application/json"}
    )
    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body
    assert isinstance(body["detail"], list)


def test_unhandled_exception_html(webpage):
    resp = build_client(_app(webpage)).get("/crash", headers={"accept": "text/html"})
    assert resp.status_code == 500
    assert 'id="code">500' in resp.text


def test_unhandled_exception_json(webpage):
    resp = build_client(_app(webpage)).get(
        "/crash", headers={"accept": "application/json"}
    )
    assert resp.status_code == 500
    assert resp.json() == {"detail": "Internal Server Error"}
