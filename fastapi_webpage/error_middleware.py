from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .webpage import WebPage


def register_error_handlers(app: FastAPI, webpage: WebPage, error_templ_file: str = "error.jinja2"):
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
