from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

DOCS_PATHS = {"/docs", "/redoc", "/openapi.json"}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        enable_security_headers: bool = True,
        enable_hsts: bool = False,
        hsts_max_age: int = 31536000,
        frame_options: str = "SAMEORIGIN",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: str = "camera=(), geolocation=(), microphone=()",
        content_security_policy: str = "default-src 'none'; frame-ancestors 'self'",
    ):
        super().__init__(app)
        self.enable = enable_security_headers
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.frame_options = frame_options
        self.referrer_policy = referrer_policy
        self.permissions_policy = permissions_policy
        self.csp = content_security_policy

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if not self.enable:
            return response

        response.headers["X-Frame-Options"] = self.frame_options
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = self.referrer_policy
        response.headers["Permissions-Policy"] = self.permissions_policy

        if request.url.path not in DOCS_PATHS:
            response.headers["Content-Security-Policy"] = self.csp

        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains"
            )

        return response
