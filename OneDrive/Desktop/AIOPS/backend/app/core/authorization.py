from __future__ import annotations

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.exceptions import AppException
from app.core.request_context import get_request_id
from app.security.tokens import TokenService


class AuthorizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        authorization = request.headers.get("Authorization")
        request.state.token_payload = None

        if authorization:
            scheme, _, token = authorization.partition(" ")
            if scheme.lower() != "bearer" or not token:
                return auth_error("invalid_authorization_header", "Authorization header is invalid.")
            try:
                request.state.token_payload = TokenService().decode_token(token, expected_type="access")
            except AppException as exc:
                return auth_error(exc.code, exc.message)

        return await call_next(request)


def auth_error(code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": {},
                "request_id": get_request_id(),
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
