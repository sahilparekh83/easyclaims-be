import logging
import logging.config
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from .api import api_router
from .configs.common import get_settings
from .events import startup_handler, shutdown_handler
from .middlewares import log_time
from .middlewares.security_headers import SecurityHeadersMiddleware
from .middlewares.timeout_middleware import TimeoutMiddleware
from .middlewares.jwt_middleware import JWTMiddleware
from .middlewares.permissions import PermissionsMiddleware
from .middlewares.rate_limit_middleware import RateLimitMiddleware
from .core.handlers import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from .version import __version__


def create_application() -> FastAPI:
    settings = get_settings()

    logging.config.dictConfig(settings.LOGGING_CONFIG)
    logger = logging.getLogger(settings.PROJECT_SLUG)

    app = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
        version=__version__,
        openapi_url=f"{settings.API_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.include_router(api_router, prefix=settings.API_STR)
    logger.info("API router registered at %s", settings.API_STR)

    _static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    os.makedirs(_static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")
    logger.info("StaticFiles mounted at /static → %s", _static_dir)

    app.add_event_handler("startup", startup_handler)
    app.add_event_handler("shutdown", shutdown_handler)

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Middleware registered outermost-first (executes top-down in add_middleware order)
    app.add_middleware(BaseHTTPMiddleware, dispatch=log_time)

    app.add_middleware(
        RateLimitMiddleware,
        default_rate_limit=settings.API_RATE_LIMIT,
        default_rate_period=settings.API_RATE_PERIOD,
        excluded_paths=settings.RATE_LIMIT_EXCLUDED_PATHS,
        api_str=settings.API_STR,
    )

    app.add_middleware(PermissionsMiddleware)

    app.add_middleware(
        JWTMiddleware,
        excluded_paths=settings.EXCLUDED_PATHS,
        api_str=settings.API_STR,
        x_api_key_paths=settings.X_API_KEY_PATHS,
    )

    app.add_middleware(
        TimeoutMiddleware,
        timeout_seconds=settings.REQUEST_TIMEOUT_SECONDS,
    )

    app.add_middleware(
        SecurityHeadersMiddleware,
        enable_security_headers=settings.SECURITY_HEADERS_ENABLED,
        enable_hsts=settings.HSTS_ENABLED,
        hsts_max_age=settings.HSTS_MAX_AGE,
        frame_options=settings.FRAME_OPTIONS,
        referrer_policy=settings.REFERRER_POLICY,
        permissions_policy=settings.PERMISSIONS_POLICY,
        content_security_policy=settings.CONTENT_SECURITY_POLICY,
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    cors_origins = [str(o) for o in settings.CORS_ORIGINS] if settings.CORS_ORIGINS else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=settings.CORS_ORIGIN_REGEX,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
    )

    return app
