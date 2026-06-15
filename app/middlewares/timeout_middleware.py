import asyncio
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout_seconds: int = 30):
        super().__init__(app)
        self.timeout = timeout_seconds

    async def dispatch(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout)
        except asyncio.TimeoutError:
            logger.warning("Request timeout: %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=504,
                content={
                    "success": False,
                    "data": None,
                    "error": {
                        "detail": "Request timed out",
                        "error_code": "REQUEST_TIMEOUT",
                        "errors": [],
                    },
                },
            )
