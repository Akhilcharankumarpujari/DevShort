from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.request_context import get_request_id

logger = logging.getLogger(__name__)


class AppException(Exception):
    def __init__(
        self,
        *,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str = "application_error",
        message: str = "Application error",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "application_exception",
            extra={"path": request.url.path, "code": exc.code, "status_code": exc.status_code},
        )
        return error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "http_error"
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "resource_not_found"
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "unauthorized"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = "forbidden"
        logger.info(
            "http_exception",
            extra={"path": request.url.path, "code": code, "status_code": exc.status_code},
        )
        return error_response(
            status_code=exc.status_code,
            code=code,
            message=str(exc.detail),
            details={},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.info(
            "validation_exception",
            extra={"path": request.url.path, "error_count": len(exc.errors())},
        )
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="validation_error",
            message="Request validation failed.",
            details={"errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        settings = get_settings()
        logger.exception("unhandled_exception", extra={"path": request.url.path})
        details: dict[str, Any] = {}
        if not settings.is_production:
            details["exception"] = exc.__class__.__name__
        return error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_server_error",
            message="Internal server error.",
            details=details,
        )


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any],
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": get_request_id(),
            }
        },
    )
