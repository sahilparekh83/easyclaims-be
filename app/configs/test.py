import os
from .base import Settings


class SettingsTest(Settings):
    DEBUG: bool = True
    COOKIE_SECURE: bool = False
    HSTS_ENABLED: bool = False
    OTP_EXPIRE_MINUTES: int = 1
    POSTGRES_DB: str = os.getenv("TEST_POSTGRES_DB", "easyclaims_test")
