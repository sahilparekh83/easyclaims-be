# EasyClaims Backend

FastAPI backend for the EasyClaims Membership CRM — handles authentication, member/partner/policy management, OTP-based login, and policy document storage.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.111.1 + Uvicorn 0.30.1 |
| Database | PostgreSQL 16 via SQLAlchemy 2.0 + psycopg3 |
| Migrations | Alembic 1.13.2 |
| Config | Pydantic Settings 2.10 (reads `.env`) |
| Auth | JWE tokens (python-jose), OTP via email — no passwords |
| Validation | Pydantic 2.11 |
| Linting | Ruff |

## Prerequisites

- Python 3.12+
- PostgreSQL 16
- pip (or uv / pipx)

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/sahilparekh83/easyclaims-be.git
cd easyclaims-be
git checkout dev
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -e .
# Dev extras (pytest, ruff, httpx):
pip install -e ".[dev]"
```

### 4. Configure environment

```bash
cp .env.sample .env
# Open .env and fill in the required values (see table below)
```

### 5. Set up PostgreSQL

```bash
# Connect as superuser and create the role + database
psql -U postgres -c "CREATE USER mystique_agents WITH PASSWORD 'mystique_agents';"
psql -U postgres -c "CREATE DATABASE easyclaims OWNER mystique_agents;"
```

### 6. Run database migrations

```bash
alembic upgrade head
```

This creates all 21 tables in the `easyclaims` database.

### 7. (Optional) Restore from backup

If you have the SQL dump file, restore it instead of running migrations:

```bash
psql -U mystique_agents -d easyclaims < easyclaims_backup_20260618_001611.sql
# or the generic alias:
psql -U mystique_agents -d easyclaims < easyclaims_db.sql
```

### 8. Start the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API is now running at **http://localhost:8000**

---

## API Documentation

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI (interactive) |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/api/v1/health | Health check endpoint |

---

## Environment Variables

Copy `.env.sample` to `.env` and edit these values:

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_SERVER` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_USER` | DB username | `mystique_agents` |
| `POSTGRES_PASSWORD` | DB password | `mystique_agents` |
| `POSTGRES_DB` | Database name | `easyclaims` |
| `JWE_SECRET_KEY` | 32-byte hex key for JWE tokens | see below |
| `SMTP_USER` | Gmail address for OTP emails | `your@gmail.com` |
| `SMTP_PASSWORD` | Gmail App Password (not account password) | `xxxx xxxx xxxx xxxx` |

Generate a `JWE_SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Optional (with defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `MODE` | `DEV` | `DEV`, `TEST`, or `PROD` |
| `DEBUG` | `false` | Enable debug output |
| `ACCESS_TOKEN_EXPIRE_SECONDS` | `1800` | 30 min |
| `REFRESH_TOKEN_EXPIRE_SECONDS` | `86400` | 24 h |
| `OTP_EXPIRE_MINUTES` | `10` | OTP validity window |
| `OTP_MAX_ATTEMPTS` | `3` | Max OTP retries |
| `STORAGE_BACKEND` | `local` | `local`, `gcs`, or `azure` |
| `UPLOAD_DIR` | `uploads` | Local file storage path |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Comma-separated allowed origins |
| `COOKIE_SECURE` | `false` | Set `true` in production (HTTPS) |
| `LOG_LEVEL` | `DEBUG` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `API_RATE_LIMIT` | `60` | Requests per rate period |
| `API_RATE_PERIOD` | `60` | Rate period in seconds |

### SMTP (Gmail)

To send OTP emails via Gmail, generate an **App Password**:
1. Google Account → Security → 2-Step Verification → App passwords
2. Create one for "Mail" and use it as `SMTP_PASSWORD`

---

## Project Structure

```
easyclaims-be/
├── main.py                  # Uvicorn entrypoint — imports create_application()
├── alembic.ini              # Alembic config (sqlalchemy.url read from env at runtime)
├── pyproject.toml           # Dependencies and build config
├── .env.sample              # Environment variable template
├── easyclaims_db.sql        # DB backup (restore instead of migrations)
│
├── alembic/
│   └── versions/            # Migration scripts
│
├── app/
│   ├── application.py       # FastAPI factory (CORS, middleware, routers)
│   ├── api/                 # Route handlers
│   │   ├── auth/            # OTP send/verify, refresh, logout
│   │   ├── admin/           # Admin endpoints (members, partners, plans, policies)
│   │   ├── partner/         # Partner endpoints
│   │   └── member/          # Member endpoints
│   ├── configs/             # Pydantic Settings (reads .env)
│   ├── core/                # Business logic / use cases
│   ├── db/
│   │   ├── session.py       # create_engine(), session_scope() context manager
│   │   └── models/          # SQLAlchemy ORM models (21 tables)
│   ├── middlewares/         # Auth, rate limiting, timeout, security headers
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Email, OTP, storage services
│   └── utils/               # Helpers (response wrapper, pagination, etc.)
│
├── seeders/                 # DB seed scripts
├── scripts/                 # Admin utilities
├── tests/                   # pytest test suite
└── uploads/                 # Local file uploads (DEV only)
```

---

## Auth Flow

1. `POST /api/v1/auth/send-otp` — send OTP to email
2. `POST /api/v1/auth/verify-otp` — verify OTP → returns JWE access token + refresh cookie
3. All protected routes require `Authorization: Bearer <token>`
4. `POST /api/v1/auth/refresh` — exchange refresh cookie for new access token
5. `POST /api/v1/auth/logout` — invalidate session

---

## Portal Roles

| Role | Access |
|------|--------|
| Admin | Full system: members, partners, plans, policies, reports, notifications |
| Partner | Own members, policies, plans, and profile |
| Member | Own plan, profile, family, nominees, policies, consent |

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Production Notes

- Set `MODE=PROD`, `COOKIE_SECURE=true`, `HSTS_ENABLED=true`
- Use a reverse proxy (nginx) in front of Uvicorn
- Store secrets in environment variables or a secrets manager — never commit `.env`
- Set `CORS_ORIGINS` to your deployed frontend domain
- Use `STORAGE_BACKEND=gcs` or `azure` for policy document storage
