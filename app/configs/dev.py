from .base import Settings


class SettingsDev(Settings):
    DEBUG: bool = True
    COOKIE_SECURE: bool = False
    HSTS_ENABLED: bool = False
    SAMESITE_MODE: str = "lax"
