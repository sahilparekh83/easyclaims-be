from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.member import ConsentCreate
from ...services.member_service import MemberService
from ..deps import _require_customer

me_consent_router = APIRouter()


@me_consent_router.get("", response_model=ResponseModel)
async def get_consent(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    from ...db.queries.member_query import MemberQuery
    consents = MemberQuery().list_consents(user_id)
    return ResponseModel.ok(data=[
        {"id": str(c.id), "consented_at": c.consented_at.isoformat(),
         "version": c.version, "source": c.source, "created_at": c.created_at.isoformat()}
        for c in consents
    ])


@me_consent_router.post("", response_model=ResponseModel, status_code=201)
async def record_consent(body: ConsentCreate, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    c = MemberService().record_consent(user_id, body)
    return ResponseModel.ok(data={"id": str(c.id), "consented_at": c.consented_at.isoformat(),
                                   "version": c.version, "source": c.source})
