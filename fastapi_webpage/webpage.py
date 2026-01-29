import inspect
import time
from functools import wraps
from os import PathLike
from pathlib import Path
from typing import Any, Awaitable, Callable

from fastapi import HTTPException, Request, status
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context


@pass_context
def urlx_for(
    context: dict,
    name: str,
    **path_params: Any,
) -> str:
    """
    擴充 FastAPI 的 `url_for` 函式。

    當 Request 的 Header 中包含 `x-forwarded-proto` 時，自動將 URL scheme 替換為該 Protocol，
    以支援 Reverse Proxy 環境（如 Cloudflare, Traefik, Nginx 等）。

    Args:
        context (dict): Jinja2 的 context，必須包含 "request"。
        name (str): Route 的名稱。
        **path_params (Any): URL 路徑參數。

    Returns:
        str: 產生的 URL 字串。
    """
    request: Request = context["request"]
    http_url = request.url_for(name, **path_params)
    if scheme := request.headers.get("x-forwarded-proto"):
        return http_url.replace(scheme=scheme)
    return http_url



class WebPage:
    """
    管理網頁渲染與全域 Context 的類別。

    此類別負責初始化 Jinja2 環境，並提供 Decorator 與直接呼叫的方法來渲染 Template。
    它可以管理全域的 `webpage_context` 與 `pre_context`，讓多個頁面共享相同的變數。
    """
    def __init__(
        self,
        template_directory: Path | PathLike | str,
        **global_context: Any,
    ):
        """
        初始化 WebPage 實例。

        Args:
            template_directory (Path | PathLike | str): Template 檔案的目錄路徑。
            **global_context (Any): 全域的 Context 變數，會在所有頁面中可用。
        """
        self._template = Jinja2Templates(template_directory)
        self._template.env.globals["url_for"] = urlx_for
        self._webpage_context = dict()
        self._pre_context = dict()
        self._webpage_context.update(global_context)

    @property
    def pre_context(self):
        """取得目前的 pre_context (預處理 Context)。"""
        return self._pre_context

    def pre_context_update(self, value: dict):
        """
        更新 pre_context。

        Args:
            value (dict): 要更新到 pre_context 的字典。

        Raises:
            ValueError: 如果 value 不是 dict。
        """
        match value:
            case dict():
                self._pre_context.update(value)
            case _:
                raise ValueError("The value need to be a dict")

    @property
    def webpage_context(self):
        """取得目前的 webpage_context (網頁全域 Context)。"""
        return self._webpage_context

    def webpage_context_update(self, value: dict):
        """
        更新 webpage_context。

        Args:
            value (dict): 要更新到 webpage_context 的字典。

        Raises:
            ValueError: 如果 value 不是 dict。
        """
        match value:
            case dict():
                self._webpage_context.update(value)
            case _:
                raise ValueError("The value need to be a dict")
    
    # decorator
    def page(
        self, template_file: PathLike | str, status_code: int = status.HTTP_200_OK
    ) -> Awaitable:
        """
        裝飾器 (Decorator)，用將 FastAPI 的 API 函式回傳值渲染為 HTML 頁面。

        被裝飾的函式必須回傳 `dict`，該 dict 將作為 Context 傳入 Template。
        如果 Request 為 API 請求（預期回傳 JSON），請勿使用此裝飾器，或自行處理 Content Negotiation。

        Args:
            template_file (PathLike | str): Template 檔案名稱 (相對於 template_directory)。
            status_code (int, optional): HTTP 狀態碼。預設為 200 OK。

        Returns:
            Awaitable: 裝飾後的非同步函式。
        """
        def decorator(func: Callable | Awaitable):
            @wraps(func)
            async def wrap(**kargs):
                request: Request = kargs.get("request")
                if request is None:
                    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR)
                context: dict[str, Any] = func(**kargs)
                if inspect.isawaitable(context):
                    context = await context
                match context:
                    case Response():
                        return context
                    case dict():
                        context.update(
                            {
                                "request": request,
                                "webpage": self._webpage_context,
                                "css_timestamp": str(int(time.time())),
                            }
                        )
                        context.update(self._pre_context)
                        wp_response = self._template.TemplateResponse(
                            name=template_file, context=context, status_code=status_code
                        )
                        return wp_response
                    case _:
                        raise HTTPException(
                            status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={
                                "error_msgs": [
                                    "套用到 @Webpage().page() 的函式，必須回傳 dict。",
                                    f"function name: {func.__name__}",
                                    f"info: {func.__code__}",
                                ]
                            },
                        )

            return wrap

        return decorator

    def __call__(
        self,
        template_file: PathLike | str,
        request: Request,
        context: dict[str, Any] = {},
        **kargs,
    ):
        """
        直接渲染指定的 Template 並回傳 Response。

        Args:
            template_file (PathLike | str): Template 檔案名稱。
            request (Request): FastAPI 的 Request 物件。
            context (dict[str, Any], optional): 額外的 Context 變數。預設為空字典。
            **kargs: 其他參數。
                - status_code (int): HTTP 狀態碼。
                - headers (dict): HTTP Headers。

        Returns:
            Response: FastAPI TemplateResponse 物件。
        """
        context.update({"request": request})
        context.update(self._pre_context)
        context.update({"webpage": self._webpage_context})
        wp_response = self._template.TemplateResponse(
            name=template_file, context=context
        )
        if kargs.get("status_code") and isinstance(kargs.get("status_code"), int):
            wp_response.status_code = kargs.get("status_code")
        if kargs.get("headers") and isinstance(kargs.get("headers"), dict):
            wp_response.headers.update(kargs.get("headers"))
        return wp_response