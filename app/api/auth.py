import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Response, Request
from ..schemas.auth import SendOTPRequest, VerifyOTPRequest, TokenResponse
from ..schemas.base import ResponseModel
from ..services.auth_service import AuthService
from ..services.otp_service import OTPService
from ..services.email_service import EmailService
from ..services.user_service import UserService
from ..db.queries.user_query import UserQuery
from ..db.queries.role_query import RoleQuery
from ..configs.common import get_settings

auth_router = APIRouter()
logger = logging.getLogger(__name__)


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    settings = get_settings()
    cookie_kwargs = dict(
        path="/",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.SAMESITE_MODE,
    )
    if settings.COOKIE_DOMAIN:
        cookie_kwargs["domain"] = settings.COOKIE_DOMAIN
    response.set_cookie(key="access_token", value=access_token,
                        max_age=settings.ACCESS_TOKEN_EXPIRE_SECONDS, **cookie_kwargs)
    response.set_cookie(key="refresh_token", value=refresh_token,
                        max_age=settings.REFRESH_TOKEN_EXPIRE_SECONDS, **cookie_kwargs)


@auth_router.post("/send-otp", response_model=ResponseModel)
async def send_otp(body: SendOTPRequest):
    user_service = UserService()
    otp_service = OTPService()
    email_service = EmailService()

    user = user_service.get_user_by_email(str(body.email))
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email")

    settings = get_settings()
    raw_otp = otp_service.create_otp_for_user(str(user.id), str(body.email))
    sent = email_service.send_otp_email(str(body.email), raw_otp)

    if not sent:
        if settings.DEBUG:
            logger.warning("SMTP not configured — OTP for %s: %s", body.email, raw_otp)
            return ResponseModel.ok(data={"message": "OTP sent (dev mode)", "otp": raw_otp})
        raise HTTPException(status_code=500, detail="Failed to send OTP email. Please contact support.")

    return ResponseModel.ok(data={"message": "OTP sent to your email"})


@auth_router.post("/verify-otp", response_model=ResponseModel)
async def verify_otp(body: VerifyOTPRequest, response: Response):
    user_service = UserService()
    otp_service = OTPService()
    auth_service = AuthService()
    role_query = RoleQuery()
    user_query = UserQuery()

    user = user_service.get_user_by_email(str(body.email))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    otp_log = otp_service.validate_otp(str(body.email), body.otp)
    if not otp_log:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    roles = role_query.get_user_roles(str(user.id))
    access_token, jti = auth_service.create_access_token(
        user_id=str(user.id),
        email=str(user.email),
        user_type=user.user_type.value,
        roles=roles,
    )
    refresh_token = auth_service.create_refresh_token(user_id=str(user.id), jti=jti)

    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    user_query.create_auth_session(str(user.id), jti, expires_at)

    default_partner_id = None
    if user.user_type.value == "CUSTOMER":
        from ..db.queries.member_query import MemberQuery
        first_enrollment = MemberQuery().get_first_active_enrollment(str(user.id))
        if first_enrollment:
            default_partner_id = str(first_enrollment.partner_id)

    try:
        from ..db.queries.activity_query import ActivityQuery
        ActivityQuery().record_login(str(user.id))
    except Exception:
        logger.warning("Failed to record login activity for user %s", user.id)

    _set_auth_cookies(response, access_token, refresh_token)

    return ResponseModel.ok(data={
        **TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        ).model_dump(),
        "user_type": user.user_type.value,
        "user_id": str(user.id),
        "email": str(user.email),
        "default_partner_id": default_partner_id,
    })


@auth_router.post("/refresh", response_model=ResponseModel)
async def refresh_token(request: Request, response: Response):
    auth_service = AuthService()
    user_query = UserQuery()
    settings = get_settings()

    token = request.cookies.get("refresh_token") or (
        request.headers.get("Authorization", "").replace("Bearer ", "") or None
    )
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    payload = auth_service.decode_token(token)
    auth_service.validate_token_expiry(payload)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    old_jti = payload.get("jti")
    user_id = payload.get("sub")

    session = user_query.get_auth_session_by_jti(old_jti)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or revoked")

    user = user_query.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    roles = RoleQuery().get_user_roles(str(user.id))

    new_access_token, new_jti = auth_service.create_access_token(
        user_id=str(user.id),
        email=str(user.email),
        user_type=user.user_type.value,
        roles=roles,
    )
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    user_query.update_auth_session_jti(old_jti, new_jti, expires_at)

    new_refresh_token = auth_service.create_refresh_token(user_id, new_jti)
    _set_auth_cookies(response, new_access_token, new_refresh_token)

    return ResponseModel.ok(data={
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    })


@auth_router.post("/logout", response_model=ResponseModel)
async def logout(request: Request, response: Response):
    auth_service = AuthService()
    user_query = UserQuery()

    token = request.cookies.get("access_token") or (
        request.headers.get("Authorization", "").replace("Bearer ", "") or None
    )
    if token:
        try:
            payload = auth_service.decode_token(token)
            jti = payload.get("jti")
            if jti:
                user_query.delete_auth_session_by_jti(jti)
        except Exception:
            pass

    settings = get_settings()
    cookie_kwargs = dict(path="/", httponly=True, secure=settings.COOKIE_SECURE, samesite=settings.SAMESITE_MODE)
    if settings.COOKIE_DOMAIN:
        cookie_kwargs["domain"] = settings.COOKIE_DOMAIN
    response.delete_cookie(key="access_token", **cookie_kwargs)
    response.delete_cookie(key="refresh_token", **cookie_kwargs)

    return ResponseModel.ok(data={"message": "Logged out successfully"})
