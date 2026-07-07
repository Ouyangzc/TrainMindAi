"""统一异常与错误响应。

AI 服务讲自己干净的 REST/JSON（语义化 HTTP 状态 + 统一错误体），
由 Java 侧适配成 AjaxResult 再返回前端。错误体形如：
    {"error": {"code": "RETRIEVAL_EMPTY", "message": "...", "detail": {...}}}
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """业务/领域异常基类。"""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        http_status: int = status.HTTP_400_BAD_REQUEST,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.detail = detail or {}


def _error_body(code: str, message: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "detail": detail or {}}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=_error_body(exc.code, exc.message, exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = jsonable_encoder(
            exc.errors(),
            custom_encoder={ValueError: str},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body("VALIDATION_ERROR", "请求参数校验失败", {"errors": errors}),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body("HTTP_ERROR", str(exc.detail)),
        )
