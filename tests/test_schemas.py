import os
os.environ.setdefault("MODE", "DEV")
os.environ.setdefault("JWE_SECRET_KEY", "a" * 64)
os.environ.setdefault("POSTGRES_SERVER", "0.0.0.0")
os.environ.setdefault("POSTGRES_USER", "mystique_agents")
os.environ.setdefault("POSTGRES_PASSWORD", "mystique_agents")
os.environ.setdefault("POSTGRES_DB", "easyclaims")
os.environ.setdefault("POSTGRES_PORT", "5432")

from app.schemas.base import ResponseModel
from app.schemas.auth import SendOTPRequest, VerifyOTPRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.constants import UserType


def test_response_model_ok():
    r = ResponseModel.ok(data={"key": "value"})
    assert r.success is True
    assert r.error is None


def test_response_model_fail():
    r = ResponseModel.fail("OTP expired", error_code="OTP_EXPIRED")
    assert r.success is False
    assert r.error.error_code == "OTP_EXPIRED"


def test_send_otp_request_validates_email():
    req = SendOTPRequest(email="user@example.com")
    assert req.email == "user@example.com"


def test_user_create_defaults():
    u = UserCreate(email="test@example.com")
    assert u.user_type == UserType.CUSTOMER
