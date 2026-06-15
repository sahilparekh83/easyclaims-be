import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from ..configs.common import get_settings

logger = logging.getLogger(__name__)


class PermissionsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next):
        route_permissions = self.settings.ROUTE_PERMISSIONS
        if not route_permissions:
            return await call_next(request)

        path = request.url.path
        required_roles = None
        for route_prefix, roles in route_permissions.items():
            if path.startswith(route_prefix):
                required_roles = roles
                break

        if not required_roles:
            return await call_next(request)

        user_payload = getattr(request.state, "user_payload", None)
        if not user_payload:
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "data": None,
                    "error": {"detail": "Forbidden", "error_code": "PERMISSION_DENIED", "errors": []},
                },
            )

        user_roles = user_payload.get("roles", [])
        if not any(role in user_roles for role in required_roles):
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "data": None,
                    "error": {"detail": "Insufficient permissions", "error_code": "PERMISSION_DENIED", "errors": []},
                },
            )

        return await call_next(request)
