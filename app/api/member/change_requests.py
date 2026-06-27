from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.member import ChangeRequestCreate
from ...services.member_service import MemberService
from ...db.queries.member_query import MemberQuery
from ..deps import _require_customer

member_change_requests_router = APIRouter()


@member_change_requests_router.post("", response_model=ResponseModel, status_code=201)
async def create_change_request(body: ChangeRequestCreate, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    cr = MemberService().create_change_request(user_id, body)
    return ResponseModel.ok(data={
        "id": str(cr.id),
        "status": cr.status,
        "requested_fields": cr.requested_fields,
        "reason": cr.reason,
        "created_at": cr.created_at.isoformat() if cr.created_at else None,
    })


@member_change_requests_router.get("", response_model=ResponseModel)
async def list_my_change_requests(request: Request, skip: int = 0, limit: int = 20, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    total, rows = MemberQuery().list_change_requests(user_id=user_id, skip=skip, limit=limit)
    items = []
    for cr in rows:
        family_member_name = None
        if cr.entity_type == "family_member" and cr.entity_id:
            fm = MemberQuery().get_family_member(str(cr.entity_id))
            family_member_name = fm.name if fm else None
        items.append({
            "id": str(cr.id),
            "requested_fields": cr.requested_fields,
            "reason": cr.reason,
            "status": cr.status,
            "admin_note": cr.admin_note,
            "reviewed_at": cr.reviewed_at.isoformat() if cr.reviewed_at else None,
            "created_at": cr.created_at.isoformat() if cr.created_at else None,
            "entity_type": cr.entity_type,
            "entity_id": str(cr.entity_id) if cr.entity_id else None,
            "family_member_name": family_member_name,
        })
    return ResponseModel.ok(data={
        "data": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    })
