import os
from functools import lru_cache
from .base import Settings


@lru_cache()
def get_settings() -> Settings:
    mode = os.environ.get("MODE", "DEV").upper()
    if mode == "TEST":
        from .test import SettingsTest
        return SettingsTest()
    if mode == "PROD":
        from .prod import SettingsProd
        return SettingsProd()
    from .dev import SettingsDev
    return SettingsDev()
