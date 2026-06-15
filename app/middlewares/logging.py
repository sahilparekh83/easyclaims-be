import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)


async def log_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "%s %s %s %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response
