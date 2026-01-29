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
    request: Request = context["request"]
    http_url = request.url_for(name, **path_params)
    if scheme := request.headers.get("x-forwarded-proto"):
        return http_url.replace(scheme=scheme)
    return http_url



class WebPage:
    def __init__(
        self,
        template_directory: Path | PathLike | str,
        **global_context: Any,
    ):
        self._template = Jinja2Templates(template_directory)
        self._template.env.globals["url_for"] = urlx_for
        self._webpage_context = dict()
        self._pre_context = dict()
        self._webpage_context.update(global_context)

    @property
    def pre_context(self):
        return self._pre_context

    def pre_context_update(self, value: dict):
        match value:
            case dict():
                self._pre_context.update(value)
            case _:
                raise ValueError("The value need to be a dict")

    @property
    def webpage_context(self):
        return self._webpage_context

    def webpage_context_update(self, value: dict):
        match value:
            case dict():
                self._webpage_context.update(value)
            case _:
                raise ValueError("The value need to be a dict")
    
    # decorator
    def page(
        self, template_file: PathLike | str, status_code: int = status.HTTP_200_OK
    ) -> Awaitable:
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