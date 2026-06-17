# EasyClaims Backend — Design Spec

**Date:** 2026-06-15
**Status:** Approved
**Author:** Chinar Vartak

---

## Overview

Standalone FastAPI backend for the EasyClaims platform. Handles authentication (email + OTP), user management, and role-based access control for two user types: SuperAdmin and Customer. Mirrors the folder structure and internal patterns of `mystique_auth_service` but runs as an independent project outside the monorepo with no Pants build dependency.

---

## Tech Stack

| Concern | Choice |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 (sync) |
| DB Driver | psycopg3 (sync) |
| Migrations | Alembic |
| Settings | Pydantic Settings 2.x |
| Auth tokens | JWE — python-jose (dir + A256GCM) |
| OTP delivery | SMTP email (smtplib) |
| Build system | pyproject.toml (standalone, no Pants) |

---

## Project Structure

```
easyclaims_backend/
├── pyproject.toml
├── .env.example
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── app/
│   ├── application.py           # FastAPI app factory (create_application)
│   ├── constants.py
│   ├── globals.py
│   ├── version.py
│   ├── configs/
│   │   ├── base.py              # BaseSettings with all fields
│   │   ├── common.py            # get_settings() with @lru_cache
│   │   ├── dev.py               # SettingsDev
│   │   ├── test.py              # SettingsTest
│   │   └── prod.py              # SettingsProd
│   ├── db/
│   │   ├── base.py              # Declarative Base (auto __tablename__)
│   │   ├── session.py           # engine, SessionLocal, session_scope()
│   │   ├── models/
│   │   │   ├── user.py          # User, OTPLog
│   │   │   └── roles.py         # Role, UserRole
│   │   └── queries/
│   │       ├── generic_repository.py
│   │       ├── user_query.py
│   │       └── role_query.py
│   ├── middlewares/
│   │   ├── jwt_middleware.py    # JWE validation, excluded_paths, x_api_key_paths
│   │   ├── rate_limit_middleware.py  # In-memory sliding window
│   │   ├── permissions.py       # Role-based route access
│   │   ├── timeout_middleware.py
│   │   └── security_headers.py
│   ├── api/
│   │   ├── __init__.py          # api_router aggregator
│   │   ├── auth.py              # /auth endpoints
│   │   ├── users.py             # /users endpoints
│   │   └── roles.py             # /roles endpoints
│   ├── services/
│   │   ├── auth_service.py      # JWE token create/decode
│   │   ├── otp_service.py       # OTP generate, hash, verify
│   │   ├── email_service.py     # SMTP sender
│   │   └── user_service.py
│   ├── schemas/
│   │   ├── base.py              # ResponseModel, ErrorResponse
│   │   ├── auth.py              # SendOTPRequest, VerifyOTPRequest, TokenResponse
│   │   └── user.py              # UserResponse, UserCreate
│   ├── core/
│   │   └── handlers.py          # HTTPException, ValidationError, generic handlers
│   ├── events/
│   │   └── base.py              # startup_handler, shutdown_handler
│   └── utils/
│       ├── security.py          # decode_jwe_token, http_auth
│       └── logging.py           # ColorFormatter, StandardFormatter
├── seeders/
│   ├── seed_data.py
│   └── roles.json               # Initial roles seed
├── main.py                      # Uvicorn entry point
└── entrypoint.py                # Alembic migrate → uvicorn (Docker)
```

---

## Data Models

### `users`
```
id            UUID PK
email         VARCHAR UNIQUE NOT NULL
name          VARCHAR
user_type     ENUM('SUPERADMIN', 'CUSTOMER') NOT NULL
is_active     BOOLEAN DEFAULT true
is_deleted    BOOLEAN DEFAULT false
created_at    TIMESTAMPTZ
updated_at    TIMESTAMPTZ
```

### `roles`
```
id            UUID PK
role_name     VARCHAR UNIQUE NOT NULL   # e.g. SUPERADMIN, CLAIMS_AGENT, CUSTOMER
role_type     ENUM('ADMIN', 'CUSTOMER')
is_active     BOOLEAN DEFAULT true
```

### `user_roles` (pivot)
```
id            UUID PK
user_id       FK → users.id
role_id       FK → roles.id
assigned_by   FK → users.id (nullable — NULL = system/seeded)
is_active     BOOLEAN DEFAULT true
created_at    TIMESTAMPTZ
UNIQUE(user_id, role_id)
```

### `otp_log`
```
id            UUID PK
user_id       FK → users.id
email         VARCHAR NOT NULL          # denormalized for pre-lookup
otp_code      VARCHAR NOT NULL          # bcrypt hash of 6-digit code
expires_at    TIMESTAMPTZ NOT NULL      # created_at + OTP_EXPIRE_MINUTES
is_used       BOOLEAN DEFAULT false
attempts      INT DEFAULT 0             # invalidated at OTP_MAX_ATTEMPTS
created_at    TIMESTAMPTZ
```

### `auth_sessions`
```
session_id    UUID PK
user_id       VARCHAR NOT NULL (indexed)
jti           VARCHAR UNIQUE            # JWT ID for revocation
expires_at    TIMESTAMPTZ
created_at    TIMESTAMPTZ
```

---

## Authentication Flow

### Step 1 — Send OTP
```
POST /api/v1/auth/send-otp
Body: { "email": "user@example.com" }

1. Lookup user by email → 404 if not found
2. Generate 6-digit OTP via secrets.randbelow
3. Hash OTP with bcrypt → store in otp_log (expires_at = now + OTP_EXPIRE_MINUTES)
4. Send raw OTP via SMTP email
5. Return: { "message": "OTP sent" }
```

### Step 2 — Verify OTP → Issue Tokens
```
POST /api/v1/auth/verify-otp
Body: { "email": "user@example.com", "otp": "482910" }

1. Find latest unused, unexpired otp_log row for email
2. If not found → 401
3. otp_log.attempts += 1 → if attempts >= OTP_MAX_ATTEMPTS → mark is_used=True → 401
4. bcrypt.verify(otp, otp_log.otp_code) → fail → save attempts → 401
5. Mark otp_log.is_used = True
6. Load user + roles
7. Build JWE payload: { sub, email, user_type, roles, jti, exp }
8. Encrypt with JWE (dir + A256GCM using JWE_SECRET_KEY)
9. Create refresh token (JWE, REFRESH_TOKEN_EXPIRE_SECONDS TTL)
10. Store auth_sessions row (session_id, user_id, jti, expires_at)
11. Set HttpOnly cookies: access_token, refresh_token
12. Return: { access_token, refresh_token, token_type: "bearer" }
```

### Refresh
```
POST /api/v1/auth/refresh
1. Decrypt JWE refresh token → extract sub + jti
2. Verify session exists and not expired
3. Issue new access token (rotate jti, update session)
4. Return new access_token
```

### Logout
```
POST /api/v1/auth/logout
1. Decrypt token → get jti
2. Delete auth_sessions row
3. Clear cookies
4. Return: { "message": "Logged out" }
```

---

## Middleware Stack

Registered in `create_application()`, outermost-first:

```
1. CORSMiddleware              allow_origins from CORS_ORIGINS setting
2. GZipMiddleware              compress responses > 1000 bytes (FastAPI built-in)
3. SecurityHeadersMiddleware   X-Frame-Options, X-Content-Type-Options,
                               Referrer-Policy, Permissions-Policy,
                               HSTS (PROD only), CSP
4. TimeoutMiddleware           REQUEST_TIMEOUT_SECONDS (default 30) → 504
5. JWTMiddleware               excluded_paths → pass through
                               x_api_key_paths → validate X-API-Key header
                               all other paths → decrypt JWE, verify jti in auth_sessions
                               sets request.state.user on success
                               clears cookies + 401 on failure
6. PermissionsMiddleware       reads request.state.user.roles
                               checks route against ROUTE_PERMISSIONS map
                               returns 403 if role not sufficient
7. RateLimitMiddleware         in-memory sliding window (no Redis)
                               IP-based: API_RATE_LIMIT req / API_RATE_PERIOD sec
                               returns 429 when exceeded
8. LoggingMiddleware           logs method, path, status, process_time_ms
```

---

## Settings & Environments

```
MODE env var → DEV (default) | TEST | PROD
```

| Setting | Type | Default | Notes |
|---|---|---|---|
| `PROJECT_NAME` | str | `"EasyClaims"` | |
| `DEBUG` | bool | `False` | True in DEV |
| `API_STR` | str | `"/api/v1"` | |
| `POSTGRES_SERVER/USER/PASSWORD/DB/PORT` | str | — | assembled into `SQLALCHEMY_DATABASE_URI` |
| `POSTGRES_SSL_MODE` | str | `"disable"` | |
| `JWE_SECRET_KEY` | str | — | 32-byte hex, required |
| `ACCESS_TOKEN_EXPIRE_SECONDS` | int | `1800` | 30 min |
| `REFRESH_TOKEN_EXPIRE_SECONDS` | int | `86400` | 24 hr |
| `API_KEY` | str | — | for X-API-Key header auth |
| `X_API_KEY_PATHS` | list | `[]` | path prefixes accepting X-API-Key |
| `OTP_EXPIRE_MINUTES` | int | `10` | |
| `OTP_MAX_ATTEMPTS` | int | `3` | |
| `SMTP_HOST/PORT/USER/PASSWORD/FROM_EMAIL/TLS` | — | — | email delivery |
| `REQUEST_TIMEOUT_SECONDS` | int | `30` | |
| `API_RATE_LIMIT` | int | `60` | requests per period |
| `API_RATE_PERIOD` | int | `60` | seconds |
| `RATE_LIMIT_EXCLUDED_PATHS` | list | `[]` | |
| `ROUTE_PERMISSIONS` | dict | `{}` | `{ "/api/v1/users": ["SUPERADMIN"] }` |
| `CORS_ORIGINS` | list | `[]` | |
| `COOKIE_DOMAIN` | str | `None` | |
| `COOKIE_SECURE` | bool | `True` | False in DEV |
| `SAMESITE_MODE` | str | `"lax"` | `"none"` in PROD |
| `SECURITY_HEADERS_ENABLED` | bool | `True` | |
| `HSTS_ENABLED` | bool | `False` | True in PROD |

**Environment overrides:**
- `SettingsDev`: `DEBUG=True`, `COOKIE_SECURE=False`, `HSTS_ENABLED=False`
- `SettingsTest`: `DEBUG=True`, `OTP_EXPIRE_MINUTES=1`, separate test DB
- `SettingsProd`: `DEBUG=False`, `COOKIE_SECURE=True`, `HSTS_ENABLED=True`, `SAMESITE_MODE="none"`

---

## API Endpoints

### Auth (`/api/v1/auth`) — no JWT required
```
POST /auth/send-otp          Body: { email }              → 200 { message }
POST /auth/verify-otp        Body: { email, otp }         → 200 TokenResponse
POST /auth/refresh            Cookie/Header: refresh_token → 200 TokenResponse
POST /auth/logout             Cookie/Header: access_token  → 200 { message }
```

### Users (`/api/v1/users`) — JWT required
```
GET    /users/me              Any authenticated user        → UserResponse
GET    /users                 SUPERADMIN only               → list[UserResponse]
POST   /users                 SUPERADMIN only               → UserResponse
GET    /users/{id}            SUPERADMIN only               → UserResponse
PATCH  /users/{id}            SUPERADMIN only               → UserResponse
DELETE /users/{id}            SUPERADMIN only (soft delete) → { message }
```

### Roles (`/api/v1/roles`) — SUPERADMIN only
```
GET    /roles                 → list[RoleResponse]
POST   /roles                 → RoleResponse
POST   /users/{id}/roles      → assign role to user
DELETE /users/{id}/roles/{role_id} → remove role from user
```

### Health
```
GET    /health                No auth → { status: "ok", mode: "DEV" }
```

---

## Session Management

- DB: `session_scope()` context manager (auto-commit/rollback/close)
- All DB operations use `with session_scope() as session:`
- Query layer classes (`UserQuery`, `RoleQuery`) wrap all queries in `session_scope`
- `GenericRepository` base class provides `create_or_update` pattern

---

## Error Handling

Standardized `ResponseModel` for all responses:
```json
{
  "success": false,
  "data": null,
  "error": {
    "detail": "OTP expired",
    "error_code": "OTP_EXPIRED",
    "errors": []
  }
}
```

Handlers registered in `create_application()`:
- `HTTPException` → structured error response
- `RequestValidationError` → 422 with field-level errors
- Generic `Exception` → 500 (detail hidden in PROD)

---

## Seeding

Initial roles seeded on startup from `seeders/roles.json`:
```json
[
  { "role_name": "SUPERADMIN", "role_type": "ADMIN" },
  { "role_name": "CLAIMS_AGENT", "role_type": "ADMIN" },
  { "role_name": "CUSTOMER", "role_type": "CUSTOMER" },
  { "role_name": "READ_ONLY", "role_type": "CUSTOMER" }
]
```

---

## Out of Scope (Phase 1)

- Claims management CRUD (next phase)
- Redis-backed rate limiting (in-memory is sufficient for Phase 1)
- SMS OTP delivery
- OAuth / social login
- Multi-tenancy / organizations
