"""autoescape 跨版本一致性測試。

Starlette 0.50.x 的 Jinja2Templates 一律 autoescape=True；Starlette 1.0 改為
依副檔名判斷的 select_autoescape()，使 .jinja2 等非 .html 樣板不再自動轉義。
WebPage 於 __init__ 強制 env.autoescape=True 以維持與舊版一致的安全行為，
本測試以 .jinja2 樣板（在 1.x 預設不會被轉義）驗證該強制設定在兩版本皆生效。
"""

from fastapi import FastAPI, Request

from conftest import build_client


def test_jinja2_template_is_autoescaped(webpage):
    app = FastAPI()

    @app.get("/", name="index")
    @webpage.page("raw.jinja2")  # .jinja2 在 Starlette 1.x 預設不轉義
    async def home(request: Request):
        return {"html_blob": "<script>alert(1)</script>"}

    text = build_client(app).get("/").text
    assert "&lt;script&gt;" in text
    assert "<script>alert(1)</script>" not in text
