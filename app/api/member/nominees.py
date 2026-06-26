from uuid import UUID
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.member import NomineeCreate, NomineeUpdate
from ...services.member_service import MemberService
from ..deps import _require_customer

member_nominees_router = APIRouter()


def _nominee_dict(n) -> dict:
    return {"id": str(n.id), "name": n.name, "relation": n.relation,
            "share_percent": n.share_percent}


@member_nominees_router.get("", response_model=ResponseModel)
async def list_nominees(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    return ResponseModel.ok(data=[_nominee_dict(n) for n in MemberService().list_nominees(user_id)])


@member_nominees_router.post("", response_model=ResponseModel, status_code=201)
async def add_nominee(body: NomineeCreate, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    return ResponseModel.ok(data=_nominee_dict(MemberService().add_nominee(user_id, body)))


@member_nominees_router.patch("/{nominee_id}", response_model=ResponseModel)
async def update_nominee(nominee_id: UUID, body: NomineeUpdate, request: Request,
                         _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    return ResponseModel.ok(data=_nominee_dict(MemberService().update_nominee(user_id, str(nominee_id), body)))


@member_nominees_router.delete("/{nominee_id}", response_model=ResponseModel)
async def delete_nominee(nominee_id: UUID, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    MemberService().delete_nominee(user_id, str(nominee_id))
    return ResponseModel.ok(data={"message": "Nominee removed"})
