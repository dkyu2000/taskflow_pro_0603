"""에러 응답 표준 — { error: { code, message, meta? } }."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """표준 애플리케이션 에러."""

    def __init__(self, status_code: int, code: str, message: str, meta: dict | None = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.meta = meta
        super().__init__(message)


def _body(code: str, message: str, meta: dict | None = None) -> dict:
    err: dict = {"code": code, "message": message}
    if meta:
        err["meta"] = meta
    return {"error": err}


# 상태코드 → 기본 code 매핑 (StarletteHTTPException 변환용)
_STATUS_CODE = {
    400: "VALIDATION_ERROR",
    401: "TOKEN_EXPIRED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(exc.code, exc.message, exc.meta),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content=_body("VALIDATION_ERROR", "입력값이 올바르지 않습니다", {"errors": exc.errors()}),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        code = _STATUS_CODE.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else "요청을 처리할 수 없습니다"
        return JSONResponse(status_code=exc.status_code, content=_body(code, message))
