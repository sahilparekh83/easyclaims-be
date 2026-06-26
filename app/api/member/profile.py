from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.member import ProfileUpdate
from ...services.member_service import MemberService
from ..deps import _require_customer

member_profile_router = APIRouter()


def _build_profile(user, profile) -> dict:
    return {
        "id": str(user.id), "email": user.email, "name": user.name,
        "mobile_no": user.mobile_no,
        "gender": profile.gender if profile else None,
        "dob": str(profile.dob) if profile and profile.dob else None,
        "address_line": profile.address_line if profile else None,
        "address_city": profile.address_city if profile else None,
        "address_state": profile.address_state if profile else None,
        "address_pin": profile.address_pin if profile else None,
        "preferred_language": profile.preferred_language if profile else "English",
        "channel_email": profile.channel_email if profile else True,
        "channel_whatsapp": profile.channel_whatsapp if profile else False,
        "channel_voice": profile.channel_voice if profile else False,
    }


@member_profile_router.get("", response_model=ResponseModel)
async def get_profile(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    result = MemberService().get_profile(user_id)
    return ResponseModel.ok(data=_build_profile(result["user"], result["profile"]))


@member_profile_router.patch("", response_model=ResponseModel)
async def update_profile(body: ProfileUpdate, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    result = MemberService().update_profile(user_id, body)
    return ResponseModel.ok(data=_build_profile(result["user"], result["profile"]))
