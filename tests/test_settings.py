import os
os.environ.setdefault("MODE", "DEV")
os.environ.setdefault("JWE_SECRET_KEY", "a" * 64)
os.environ.setdefault("POSTGRES_SERVER", "0.0.0.0")
os.environ.setdefault("POSTGRES_USER", "mystique_agents")
os.environ.setdefault("POSTGRES_PASSWORD", "mystique_agents")
os.environ.setdefault("POSTGRES_DB", "easyclaims")
os.environ.setdefault("POSTGRES_PORT", "5432")

from app.configs.common import get_settings


def test_dev_settings_loads():
    settings = get_settings()
    assert settings.PROJECT_NAME == "EasyClaims"
    assert settings.DEBUG is True
    assert settings.COOKIE_SECURE is False
    assert "/auth/send-otp" in settings.EXCLUDED_PATHS
    assert "postgresql+psycopg://" in settings.SQLALCHEMY_DATABASE_URI
