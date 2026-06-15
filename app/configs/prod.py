from .base import Settings


class SettingsProd(Settings):
    DEBUG: bool = False
    COOKIE_SECURE: bool = True
    HSTS_ENABLED: bool = True
    SAMESITE_MODE: str = "none"
