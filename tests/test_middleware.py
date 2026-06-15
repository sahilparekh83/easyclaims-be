import os
os.environ.setdefault("MODE", "DEV")
os.environ.setdefault("JWE_SECRET_KEY", "a" * 64)
os.environ.setdefault("POSTGRES_SERVER", "0.0.0.0")
os.environ.setdefault("POSTGRES_USER", "mystique_agents")
os.environ.setdefault("POSTGRES_PASSWORD", "mystique_agents")
os.environ.setdefault("POSTGRES_DB", "easyclaims")
os.environ.setdefault("POSTGRES_PORT", "5432")

from app.middlewares.rate_limit_middleware import RateLimitMiddleware
from unittest.mock import MagicMock


def test_rate_limiter_allows_under_limit():
    app = MagicMock()
    mw = RateLimitMiddleware(app, default_rate_limit=5, default_rate_period=60)
    for _ in range(5):
        assert mw._is_allowed("127.0.0.1") is True


def test_rate_limiter_blocks_over_limit():
    app = MagicMock()
    mw = RateLimitMiddleware(app, default_rate_limit=3, default_rate_period=60)
    for _ in range(3):
        mw._is_allowed("10.0.0.1")
    assert mw._is_allowed("10.0.0.1") is False


def test_security_headers_middleware_instantiates():
    from app.middlewares.security_headers import SecurityHeadersMiddleware
    app = MagicMock()
    mw = SecurityHeadersMiddleware(app, enable_security_headers=True)
    assert mw.enable is True
