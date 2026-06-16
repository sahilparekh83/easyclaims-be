from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from ...schemas.base import ResponseModel
from ...schemas.member import MemberCreate
from ...services.member_service import MemberService
from ...db.queries.user_query import UserQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.policy_query import PolicyQuery
from ...db.session import session_scope
from ...db.models.user import User
from ...constants import UserType
from ..users import _require_superadmin

admin_members_router = APIRouter()


def _enrollment_dict(e) -> dict:
    return {"partner_id": str(e.partner_id), "plan_id": str(e.plan_id),
            "status": e.status, "end_date": str(e.end_date)}


@admin_members_router.get("", response_model=ResponseModel)
async def list_members(request: Request, skip: int = 0, limit: int = 100,
                       partner_id: str = None, _=Depends(_require_superadmin)):
    mq = MemberQuery()
    with session_scope() as session:
        q = session.query(User).filter(
            User.user_type == UserType.CUSTOMER, User.is_deleted == False
        )
        users = q.offset(skip).limit(limit).all()
        for u in users:
            session.expunge(u)
    result = []
    for u in users:
        enrollments = mq.list_enrollments(str(u.id))
        if partner_id and not any(str(e.partner_id) == partner_id for e in enrollments):
            continue
        result.append({
            "id": str(u.id), "email": u.email, "name": u.name,
            "mobile_no": u.mobile_no, "is_active": u.is_active,
            "enrollments": [_enrollment_dict(e) for e in enrollments],
        })
    return ResponseModel.ok(data=result)


@admin_members_router.post("", response_model=ResponseModel, status_code=201)
async def create_member(body: MemberCreate, request: Request, _=Depends(_require_superadmin)):
    svc = MemberService()
    result = svc.create_member(body)
    user = result["user"]
    enrollment = result["enrollment"]
    return ResponseModel.ok(data={
        "id": str(user.id), "email": user.email, "name": user.name,
        "enrollment": _enrollment_dict(enrollment),
    })


@admin_members_router.get("/{member_id}", response_model=ResponseModel)
async def get_member(member_id: UUID, request: Request, _=Depends(_require_superadmin)):
    uq = UserQuery()
    mq = MemberQuery()
    user = uq.get_user_by_id(str(member_id))
    if not user:
        raise HTTPException(status_code=404, detail="Member not found")
    enrollments = mq.list_enrollments(str(member_id))
    profile = mq.get_profile(str(member_id))
    family = mq.list_family(str(member_id))
    policies = PolicyQuery().list_by_user(str(member_id))
    return ResponseModel.ok(data={
        "id": str(user.id), "email": user.email, "name": user.name,
        "mobile_no": user.mobile_no, "is_active": user.is_active,
        "enrollments": [_enrollment_dict(e) for e in enrollments],
        "profile": {
            "gender": profile.gender if profile else None,
            "dob": str(profile.dob) if profile and profile.dob else None,
            "address_city": profile.address_city if profile else None,
        },
        "family_count": len(family),
        "policy_count": len(policies),
    })
