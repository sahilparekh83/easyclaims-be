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
        # Onboarding fields (read-only for member)
        "sale_date": str(profile.sale_date) if profile and profile.sale_date else None,
        "sales_channel": profile.sales_channel if profile else None,
        "branch_code": profile.branch_code if profile else None,
        "salesperson_name": profile.salesperson_name if profile else None,
        "employee_code": profile.employee_code if profile else None,
        "data1": profile.data1 if profile else None,
        "data2": profile.data2 if profile else None,
        "data3": profile.data3 if profile else None,
    }


@member_profile_router.get("", response_model=ResponseModel)
async def get_profile(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    result = MemberService().get_profile(user_id)
    return ResponseModel.ok(data=_build_profile(result["user"], result["profile"]))


# PATCH /member/profile is disabled — members must raise a change request.
# Admin updates member data via PATCH /admin/members/{member_id}.
