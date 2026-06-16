from uuid import UUID
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.member import FamilyMemberCreate, FamilyMemberUpdate
from ...services.member_service import MemberService
from ..deps import _require_customer

me_family_router = APIRouter()


def _family_dict(f) -> dict:
    return {"id": str(f.id), "name": f.name, "relation": f.relation,
            "gender": f.gender, "dob": str(f.dob) if f.dob else None,
            "coverage_type": f.coverage_type}


@me_family_router.get("", response_model=ResponseModel)
async def list_family(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    return ResponseModel.ok(data=[_family_dict(m) for m in MemberService().list_family(user_id)])


@me_family_router.post("", response_model=ResponseModel, status_code=201)
async def add_family(body: FamilyMemberCreate, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    return ResponseModel.ok(data=_family_dict(MemberService().add_family_member(user_id, body)))


@me_family_router.patch("/{member_id}", response_model=ResponseModel)
async def update_family(member_id: UUID, body: FamilyMemberUpdate, request: Request,
                        _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    return ResponseModel.ok(data=_family_dict(MemberService().update_family_member(user_id, str(member_id), body)))


@me_family_router.delete("/{member_id}", response_model=ResponseModel)
async def delete_family(member_id: UUID, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    MemberService().delete_family_member(user_id, str(member_id))
    return ResponseModel.ok(data={"message": "Family member removed"})
