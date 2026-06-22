"""透過 @webpage.redirect 驗證 _adjust_scheme 的邊界行為（含 v0.2.1 相對路徑修復）。"""

from fastapi import FastAPI, Request

from conftest import build_client


def _redirect_app(webpage, target: str):
    app = FastAPI()

    @app.get("/go")
    @webpage.redirect()
    async def go(request: Request):
        return target

    return app


def test_absolute_http_to_https_under_proxy(webpage):
    resp = build_client(_redirect_app(webpage, "http://h.example/p")).get(
        "/go", headers={"x-forwarded-proto": "https"}, follow_redirects=False
    )
    assert resp.headers["location"] == "https://h.example/p"


def test_absolute_no_header_unchanged(webpage):
    resp = build_client(_redirect_app(webpage, "http://h.example/p")).get(
        "/go", follow_redirects=False
    )
    assert resp.headers["location"] == "http://h.example/p"


def test_relative_passthrough(webpage):
    """v0.2.1 修復：無 netloc 的相對 URL 不得被加上 scheme。"""
    resp = build_client(_redirect_app(webpage, "/dashboard")).get(
        "/go", headers={"x-forwarded-proto": "https"}, follow_redirects=False
    )
    assert resp.headers["location"] == "/dashboard"


def test_relative_with_query_passthrough(webpage):
    """無 netloc 的相對 URL（含 query）同樣不得被加上 scheme。"""
    resp = build_client(_redirect_app(webpage, "/login?next=/x")).get(
        "/go", headers={"x-forwarded-proto": "https"}, follow_redirects=False
    )
    assert resp.headers["location"] == "/login?next=/x"
