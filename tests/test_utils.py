import os
os.environ.setdefault("MODE", "DEV")
os.environ.setdefault("JWE_SECRET_KEY", "a" * 64)
os.environ.setdefault("POSTGRES_SERVER", "0.0.0.0")
os.environ.setdefault("POSTGRES_USER", "mystique_agents")
os.environ.setdefault("POSTGRES_PASSWORD", "mystique_agents")
os.environ.setdefault("POSTGRES_DB", "easyclaims")
os.environ.setdefault("POSTGRES_PORT", "5432")

import json
import secrets
from jose import jwe
from app.utils.security import decode_jwe_token
from fastapi import HTTPException
import pytest


def test_decode_jwe_token_valid():
    key_hex = secrets.token_hex(32)
    key_bytes = bytes.fromhex(key_hex)
    payload = json.dumps({"sub": "user-123", "email": "test@example.com"}).encode()
    token = jwe.encrypt(payload, key_bytes, algorithm="dir", encryption="A256GCM").decode()
    result = decode_jwe_token(token, key_hex)
    assert result["sub"] == "user-123"


def test_decode_jwe_token_invalid():
    with pytest.raises(HTTPException) as exc_info:
        decode_jwe_token("invalid.token.value.here.x", "a" * 64)
    assert exc_info.value.status_code == 401
