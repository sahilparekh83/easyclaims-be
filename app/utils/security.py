import logging
from typing import Dict, Any
from jose import jwe, JWTError
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def decode_jwe_token(token: str, secret_key: str) -> Dict[str, Any]:
    import json
    try:
        key_bytes = bytes.fromhex(secret_key)
        payload_bytes = jwe.decrypt(token, key_bytes)
        return json.loads(payload_bytes.decode("utf-8"))
    except JWTError as exc:
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid or expired token", "error_code": "AUTH_INVALID_TOKEN"},
        ) from exc
    except Exception as exc:
        logger.exception("Token decode error: %s", exc)
        raise HTTPException(
            status_code=401,
            detail={"message": "Token decode failed", "error_code": "AUTH_INVALID_TOKEN"},
        ) from exc
