import os
os.environ.setdefault("MODE", "DEV")
os.environ.setdefault("JWE_SECRET_KEY", "a" * 64)
os.environ.setdefault("POSTGRES_SERVER", "0.0.0.0")
os.environ.setdefault("POSTGRES_USER", "mystique_agents")
os.environ.setdefault("POSTGRES_PASSWORD", "mystique_agents")
os.environ.setdefault("POSTGRES_DB", "easyclaims")
os.environ.setdefault("POSTGRES_PORT", "5432")

from app.services.otp_service import OTPService
from app.services.auth_service import AuthService


def test_otp_generate_is_6_digits():
    svc = OTPService()
    otp = svc.generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()


def test_otp_hash_and_verify():
    svc = OTPService()
    otp = "482910"
    hashed = svc.hash_otp(otp)
    assert svc.verify_otp(otp, hashed) is True
    assert svc.verify_otp("000000", hashed) is False


def test_auth_service_create_and_decode_access_token():
    svc = AuthService()
    token, jti = svc.create_access_token(
        user_id="user-123",
        email="test@example.com",
        user_type="CUSTOMER",
        roles=["CUSTOMER"],
    )
    payload = svc.decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["email"] == "test@example.com"
    assert payload["jti"] == jti


def test_auth_service_create_refresh_token():
    svc = AuthService()
    token = svc.create_refresh_token(user_id="user-123", jti="test-jti")
    payload = svc.decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "refresh"
