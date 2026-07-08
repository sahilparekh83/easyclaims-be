import os
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator, model_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class LoggingConfig(BaseModel):
    version: int
    disable_existing_loggers: bool = False
    formatters: Dict[str, Dict[str, Any]]
    handlers: Dict[str, Dict[str, Any]]
    loggers: Dict[str, Dict[str, Any]]


class Settings(BaseSettings):
    PROJECT_NAME: str = "EasyClaims"
    PROJECT_SLUG: str = "easyclaims"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    API_STR: str = "/api/v1"

    # ── Database ──────────────────────────────────────────────────────────────
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "easyclaims")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "easyclaims_dev")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_SSL_MODE: str = os.getenv("POSTGRES_SSL_MODE", "disable")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def assemble_db_connection(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("SQLALCHEMY_DATABASE_URI"):
            return values
        ssl_mode = values.get("POSTGRES_SSL_MODE") or "disable"
        values["SQLALCHEMY_DATABASE_URI"] = (
            f"postgresql+psycopg://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_SERVER')}:"
            f"{values.get('POSTGRES_PORT')}/"
            f"{values.get('POSTGRES_DB')}?"
            f"sslmode={ssl_mode}"
        )
        return values

    # ── Auth / JWE ────────────────────────────────────────────────────────────
    JWE_SECRET_KEY: str = os.getenv("JWE_SECRET_KEY", "")
    ALGORITHM: str = "dir"
    ENCRYPTION: str = "A256GCM"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "1800"))
    REFRESH_TOKEN_EXPIRE_SECONDS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_SECONDS", "86400"))

    # ── X-API-Key ─────────────────────────────────────────────────────────────
    API_KEY: str = os.getenv("API_KEY", "")

    @property
    def X_API_KEY_PATHS(self) -> List[str]:
        raw = os.getenv("X_API_KEY_PATHS", "")
        return [p.strip() for p in raw.split(",") if p.strip()]

    # ── OTP ───────────────────────────────────────────────────────────────────
    OTP_EXPIRE_MINUTES: int = int(os.getenv("OTP_EXPIRE_MINUTES", "10"))
    OTP_MAX_ATTEMPTS: int = int(os.getenv("OTP_MAX_ATTEMPTS", "3"))

    # ── Email provider — "resend" or "gmail" (SMTP) ──────────────────────────────
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "resend").lower()

    # ── SMTP ──────────────────────────────────────────────────────────────────
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() == "true"
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM_EMAIL: str = os.getenv("RESEND_FROM_EMAIL", "EasyClaims <developer@easyclaims.in>")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")

    # ── Frontend URL (used in welcome emails / links) ─────────────────────────
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    # ── Storage ───────────────────────────────────────────────────────────────
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")  # local | gcs | azure
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "easyclaims-policies")
    GCS_PROJECT: str = os.getenv("GCS_PROJECT", "")
    GCS_CREDENTIALS_FILE: str = os.getenv("GCS_CREDENTIALS_FILE", "")
    AZURE_CONTAINER: str = os.getenv("AZURE_CONTAINER", "policies")
    AZURE_CONNECTION_STRING: str = os.getenv("AZURE_CONNECTION_STRING", "")

    # ── Middleware ────────────────────────────────────────────────────────────
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    API_RATE_LIMIT: int = int(os.getenv("API_RATE_LIMIT", "60"))
    API_RATE_PERIOD: int = int(os.getenv("API_RATE_PERIOD", "60"))

    @property
    def RATE_LIMIT_EXCLUDED_PATHS(self) -> List[str]:
        raw = os.getenv("RATE_LIMIT_EXCLUDED_PATHS", "")
        return [p.strip() for p in raw.split(",") if p.strip()]

    @property
    def ROUTE_PERMISSIONS(self) -> Dict[str, List[str]]:
        raw = os.getenv("ROUTE_PERMISSIONS", "{}")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    # ── CORS / Cookies ────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = []
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_ORIGIN_REGEX: Optional[str] = None
    COOKIE_DOMAIN: Optional[str] = os.getenv("COOKIE_DOMAIN", None)
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    SAMESITE_MODE: str = os.getenv("SAMESITE_MODE", "lax").lower()

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def validate_cors_origins(cls, value):
        if isinstance(value, str):
            return [u.strip() for u in value.split(",") if u.strip()]
        return value

    # ── Security Headers ──────────────────────────────────────────────────────
    SECURITY_HEADERS_ENABLED: bool = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
    HSTS_ENABLED: bool = os.getenv("HSTS_ENABLED", "false").lower() == "true"
    HSTS_MAX_AGE: int = int(os.getenv("HSTS_MAX_AGE", "31536000"))
    FRAME_OPTIONS: str = os.getenv("FRAME_OPTIONS", "SAMEORIGIN")
    REFERRER_POLICY: str = os.getenv("REFERRER_POLICY", "strict-origin-when-cross-origin")
    PERMISSIONS_POLICY: str = os.getenv(
        "PERMISSIONS_POLICY",
        "accelerometer=(), autoplay=(), camera=(), geolocation=(), microphone=(), payment=()",
    )
    CONTENT_SECURITY_POLICY: str = os.getenv(
        "CONTENT_SECURITY_POLICY",
        "default-src 'none'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'",
    )

    # ── Excluded Paths (JWT bypass) ───────────────────────────────────────────
    EXCLUDED_PATHS: List[str] = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/auth/send-otp",
        "/auth/verify-otp",
        "/auth/refresh",
        "/auth/logout",
        "/policy-types",
        "/partner-types",
        "/webhook/whatsapp/incoming",
        "/static",
    ]

    # ── Gemini AI ─────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # ── Twilio ────────────────────────────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_FROM: str = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    TWILIO_CONTENT_SID: str = os.getenv("TWILIO_CONTENT_SID", "")

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG").upper()
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "false").lower() == "true"
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "easyclaims.logs")

    @property
    def LOGGING_CONFIG(self) -> dict:
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": self.LOG_LEVEL,
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "easyclaims": {"handlers": ["console"], "level": self.LOG_LEVEL},
                "uvicorn": {"handlers": ["console"]},
                "uvicorn.access": {"handlers": []},
                "root": {"handlers": ["console"], "level": self.LOG_LEVEL},
            },
        }

    class Config:
        case_sensitive = True
