import os
import logging
from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from ..configs.common import get_settings
from ..db.queries.user_query import UserQuery
from ..services.auth_service import AuthService

logger = logging.getLogger(__name__)


class JWTMiddleware(BaseHTTPMiddleware):
    ALLOWED_ALGORITHMS = ["dir"]
    ALLOWED_ENCRYPTION = ["A256GCM", "A128GCM"]

    def __init__(self, app, excluded_paths: list, api_str: str, x_api_key_paths: list):
        super().__init__(app)
        self.settings = get_settings()
        self.excluded_paths = excluded_paths
        self.api_str = api_str
        self.x_api_key_paths = x_api_key_paths
        self.x_api_key_value = os.getenv("API_KEY", "")
        self.auth_service = AuthService()
        self.user_query = UserQuery()

    def _normalize_path(self, path: str) -> str:
        if path.startswith(self.api_str):
            return path[len(self.api_str):]
        return path

    def _is_excluded(self, path: str) -> bool:
        return any(path.startswith(ep) for ep in self.excluded_paths)

    def _requires_api_key(self, path: str) -> bool:
        return any(path.startswith(ap) for ap in self.x_api_key_paths)

    def _cors_error(self, detail: str, status_code: int, origin: str, error_code: str = None) -> JSONResponse:
        origin_val = origin if origin in self.settings.CORS_ORIGINS else ""
        headers = {
            "Access-Control-Allow-Origin": origin_val,
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Allow-Credentials": "true",
        }
        response = JSONResponse(
            content={
                "success": False,
                "data": None,
                "error": {"detail": detail, "error_code": error_code, "errors": []},
            },
            status_code=status_code,
            headers=headers,
        )
        if status_code == 401:
            self._clear_cookies(response)
        return response

    def _clear_cookies(self, response: Response) -> None:
        for key in ("access_token", "refresh_token"):
            response.delete_cookie(
                key=key,
                path="/",
                secure=self.settings.COOKIE_SECURE,
                httponly=True,
                samesite=self.settings.SAMESITE_MODE,
            )

    def _extract_token(self, request: Request) -> Optional[str]:
        token = request.cookies.get("access_token")
        if token:
            return token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header.split(" ", 1)[1]
        return None

    def _authenticate(self, request: Request, origin: str) -> Optional[JSONResponse]:
        token = self._extract_token(request)
        if not token:
            return self._cors_error("Authorization header missing", 401, origin, "AUTH_MISSING_TOKEN")

        try:
            payload = self.auth_service.decode_token(token)
            self.auth_service.validate_token_expiry(payload)
            jti = payload.get("jti")
            if not jti:
                return self._cors_error("Token missing jti", 401, origin, "AUTH_INVALID_TOKEN")
            session = self.user_query.get_auth_session_by_jti(jti)
            if not session:
                return self._cors_error("Session not found or expired", 401, origin, "AUTH_SESSION_EXPIRED")
            user = self.user_query.get_user_by_id(payload.get("sub"))
            if not user:
                return self._cors_error("User not found", 401, origin, "AUTH_INVALID_TOKEN")
            request.state.user = user
            request.state.user_payload = payload
        except Exception as exc:
            logger.exception("JWT validation error: %s", exc)
            return self._cors_error("Invalid token", 401, origin, "AUTH_INVALID_TOKEN")
        return None

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        path = self._normalize_path(request.scope["path"])
        origin = request.headers.get("Origin", "")

        if self._is_excluded(path):
            response = await call_next(request)
            if getattr(response, "status_code", None) == 401:
                self._clear_cookies(response)
            return response

        x_api_key = request.headers.get("x-api-key", "")
        if self._requires_api_key(path):
            if x_api_key == self.x_api_key_value and self.x_api_key_value:
                request.state.user = None
                request.state.user_payload = None
                return await call_next(request)
            return self._cors_error("Invalid x-api-key", 401, origin, "AUTH_INVALID_API_KEY")

        error = self._authenticate(request, origin)
        if error:
            return error

        response = await call_next(request)
        if getattr(response, "status_code", None) == 401:
            self._clear_cookies(response)
        return response
