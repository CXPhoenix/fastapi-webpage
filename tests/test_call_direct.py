"""測試 WebPage.__call__（直接渲染，不經裝飾器）。"""

from fastapi import FastAPI, Request

from conftest import build_client


def test_direct_render(webpage):
    app = FastAPI()

    @app.get("/", name="index")
    async def home(request: Request):
        return webpage("index.jinja2", request, {"msg": "D"})

    resp = build_client(app).get("/")
    assert resp.status_code == 200
    assert 'id="msg">D' in resp.text


def test_direct_status_code(webpage):
    app = FastAPI()

    @app.get("/", name="index")
    async def home(request: Request):
        return webpage("index.jinja2", request, {"msg": "D"}, status_code=418)

    assert build_client(app).get("/").status_code == 418


def test_direct_headers_merged(webpage):
    app = FastAPI()

    @app.get("/", name="index")
    async def home(request: Request):
        return webpage(
            "index.jinja2", request, {"msg": "D"}, headers={"x-custom": "yes"}
        )

    resp = build_client(app).get("/")
    assert resp.headers.get("x-custom") == "yes"
