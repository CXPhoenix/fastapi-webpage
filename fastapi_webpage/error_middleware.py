from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .webpage import WebPage


def register_error_handlers(app: FastAPI, webpage: WebPage, error_templ_file: str = "error.jinja2"):
    """
    註冊全域的錯誤處理函式 (Error Handlers)。

    此函式會攔截 StarletteHTTPException, RequestValidationError 以及一般的 Exception。
    它會根據 Request 的 `Accept` Header 來決定回傳 JSON 格式的錯誤訊息或是渲染 HTML 錯誤頁面。

    - 如果 header 包含 "application/json"，則回傳 `JSONResponse` (FastAPI 預設行為)。
    - 否則，使用 `WebPage` 渲染指定的錯誤 Template。

    Args:
        app (FastAPI): FastAPI App 實例。
        webpage (WebPage): 已初始化的 WebPage 實例，用於渲染 Template。
        error_templ_file (str, optional): 錯誤頁面的 Template 檔名 (相對於 template_directory)。預設為 "error.jinja2"。
    """
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        accept = request.headers.get("accept", "")
        if "application/json" in accept:

            # Actually, Starlette default handler returns plain text for HTTPException if not overridden, 
            # OR we should return a JSONResponse explicitly. 
            # FasterAPI default exception handler returns JSON. 
            # If we return None, does it fall back? No, exception handlers need to return a Response.
            # Let's rely on FastAPI's default behavior by NOT registering this handler for JSON? 
            # No, once registered, it catches all. 
            # We explicitly return JSONResponse for JSON clients.
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )
            
        return webpage(
            template_file=error_templ_file,
            request=request,
            context={"status_code": exc.status_code, "detail": exc.detail},
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        accept = request.headers.get("accept", "")
        if "application/json" in accept:
            from fastapi.responses import JSONResponse
            from fastapi.encoders import jsonable_encoder
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": jsonable_encoder(exc.errors())},
            )

        return webpage(
            template_file=error_templ_file, 
            request=request,
            context={
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "detail": str(exc),
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        accept = request.headers.get("accept", "")
        if "application/json" in accept:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal Server Error"},
            )

        return webpage(
            template_file=error_templ_file,
            request=request,
            context={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal Server Error",
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
