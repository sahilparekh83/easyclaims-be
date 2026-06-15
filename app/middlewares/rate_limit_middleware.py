import time
import logging
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        default_rate_limit: int = 60,
        default_rate_period: int = 60,
        excluded_paths: list = None,
        api_str: str = "/api/v1",
    ):
        super().__init__(app)
        self.limit = default_rate_limit
        self.period = default_rate_period
        self.excluded_paths = excluded_paths or []
        self.api_str = api_str
        self._buckets: dict = defaultdict(deque)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_excluded(self, path: str) -> bool:
        normalized = path[len(self.api_str):] if path.startswith(self.api_str) else path
        return any(normalized.startswith(ep) for ep in self.excluded_paths)

    def _is_allowed(self, key: str) -> bool:
        now = time.time()
        window = self._buckets[key]
        while window and window[0] <= now - self.period:
            window.popleft()
        if len(window) >= self.limit:
            return False
        window.append(now)
        return True

    async def dispatch(self, request: Request, call_next):
        if self._is_excluded(request.url.path):
            return await call_next(request)

        ip = self._get_client_ip(request)
        if not self._is_allowed(ip):
            logger.warning("Rate limit exceeded for %s", ip)
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "data": None,
                    "error": {
                        "detail": "Too many requests",
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "errors": [],
                    },
                },
            )

        return await call_next(request)
