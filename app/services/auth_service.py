import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from jose import jwe
from fastapi import HTTPException
from ..configs.common import get_settings
from ..db.queries.user_query import UserQuery

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.settings = get_settings()
        self.user_query = UserQuery()

    def _get_key_bytes(self) -> bytes:
        return bytes.fromhex(self.settings.JWE_SECRET_KEY)

    def create_access_token(self, user_id: str, email: str, user_type: str, roles: list,
                            permissions: list = None) -> tuple:
        jti = str(uuid.uuid4())
        exp = datetime.now(timezone.utc) + timedelta(seconds=self.settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        payload = {
            "sub": str(user_id),
            "email": email,
            "user_type": user_type,
            "roles": roles,
            "permissions": permissions or [],
            "jti": jti,
            "exp": exp.timestamp(),
            "type": "access",
        }
        token = jwe.encrypt(
            json.dumps(payload).encode(),
            self._get_key_bytes(),
            algorithm=self.settings.ALGORITHM,
            encryption=self.settings.ENCRYPTION,
        ).decode()
        return token, jti

    def create_refresh_token(self, user_id: str, jti: str) -> str:
        exp = datetime.now(timezone.utc) + timedelta(seconds=self.settings.REFRESH_TOKEN_EXPIRE_SECONDS)
        payload = {
            "sub": str(user_id),
            "jti": jti,
            "exp": exp.timestamp(),
            "type": "refresh",
        }
        token = jwe.encrypt(
            json.dumps(payload).encode(),
            self._get_key_bytes(),
            algorithm=self.settings.ALGORITHM,
            encryption=self.settings.ENCRYPTION,
        ).decode()
        return token

    def decode_token(self, token: str) -> Dict[str, Any]:
        from ..utils.security import decode_jwe_token
        return decode_jwe_token(token, self.settings.JWE_SECRET_KEY)

    def validate_token_expiry(self, payload: Dict[str, Any]) -> None:
        exp = payload.get("exp")
        if not exp:
            raise HTTPException(status_code=401, detail={"message": "Token missing expiry", "error_code": "AUTH_INVALID_TOKEN"})
        if datetime.now(timezone.utc).timestamp() > float(exp):
            raise HTTPException(status_code=401, detail={"message": "Token expired", "error_code": "AUTH_TOKEN_EXPIRED"})
