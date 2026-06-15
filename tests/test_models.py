import os
os.environ.setdefault("MODE", "DEV")
os.environ.setdefault("JWE_SECRET_KEY", "a" * 64)
os.environ.setdefault("POSTGRES_SERVER", "0.0.0.0")
os.environ.setdefault("POSTGRES_USER", "mystique_agents")
os.environ.setdefault("POSTGRES_PASSWORD", "mystique_agents")
os.environ.setdefault("POSTGRES_DB", "easyclaims")
os.environ.setdefault("POSTGRES_PORT", "5432")

from app.db.models.user import User, OTPLog, AuthSession
from app.db.models.roles import Role, UserRole
from app.constants import UserType, RoleType


def test_user_model_defaults():
    user = User(email="test@example.com", user_type=UserType.CUSTOMER)
    assert user.is_active is True
    assert user.is_deleted is False


def test_role_model_fields():
    role = Role(role_name="SUPERADMIN", role_type=RoleType.ADMIN)
    assert role.role_name == "SUPERADMIN"
    assert role.is_active is True


def test_otp_log_defaults():
    from datetime import datetime, timezone
    otp = OTPLog(
        email="test@example.com",
        otp_code="hashed",
        expires_at=datetime.now(timezone.utc),
    )
    assert otp.is_used is False
    assert otp.attempts == 0
