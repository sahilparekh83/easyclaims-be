import logging
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "detail": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
                "error_code": exc.detail.get("error_code") if isinstance(exc.detail, dict) else None,
                "errors": [],
            },
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": None,
            "error": {
                "detail": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "errors": exc.errors(),
            },
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "detail": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "errors": [],
            },
        },
    )
