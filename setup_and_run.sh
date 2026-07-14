#!/usr/bin/env bash
# EasyClaims backend — one-shot setup + run script.
# Usage: ./setup_and_run.sh
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python}"
PORT="${PORT:-8000}"

echo "==> Creating virtual environment (.venv)"
if [ ! -d ".venv" ]; then
    "$PYTHON_BIN" -m venv .venv
fi

VENV_PY=".venv/Scripts/python.exe"
[ -f "$VENV_PY" ] || VENV_PY=".venv/bin/python"

echo "==> Installing dependencies"
"$VENV_PY" -m pip install --upgrade pip -q
"$VENV_PY" -m pip install -r requirements.txt -q

echo "==> Writing .env"
if [ -f .env ]; then
    echo "    .env already exists — leaving it as-is (delete it first to regenerate from env.yaml)"
elif [ -f env.yaml ]; then
    "$VENV_PY" - <<'PYCONV'
import re
with open("env.yaml") as f:
    lines = f.readlines()
with open(".env", "w") as out:
    for line in lines:
        m = re.match(r"^([A-Z0-9_]+):\s*'(.*)'\s*$", line.rstrip("\n"))
        if m:
            out.write(f"{m.group(1)}={m.group(2)}\n")
        elif line.strip().startswith("#") or not line.strip():
            out.write(line)
print("Generated .env from env.yaml")
PYCONV
else
    echo "    No .env or env.yaml found. Copy .env.sample to .env and fill in real values first:"
    echo "      cp .env.sample .env"
    exit 1
fi

echo "==> Checking database connectivity"
db_ok=0
"$VENV_PY" - <<'PYCHECK' || db_ok=1
import sys
from dotenv import dotenv_values
import psycopg

vals = dotenv_values(".env")
try:
    conn = psycopg.connect(
        host=vals["POSTGRES_SERVER"], port=int(vals["POSTGRES_PORT"]),
        user=vals["POSTGRES_USER"], password=vals["POSTGRES_PASSWORD"],
        dbname=vals["POSTGRES_DB"], sslmode=vals["POSTGRES_SSL_MODE"], connect_timeout=10,
    )
    conn.close()
    print("DB reachable — running migrations")
    sys.exit(0)
except Exception as e:
    print(f"DB NOT reachable ({e}) — skipping migrations, server will still start")
    sys.exit(1)
PYCHECK

if [ "$db_ok" -eq 0 ]; then
    echo "==> Running alembic migrations"
    "$VENV_PY" -m alembic upgrade head
fi

echo "==> Starting server on port $PORT"
exec "$VENV_PY" -m uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload
