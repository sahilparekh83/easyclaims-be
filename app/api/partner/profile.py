from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...schemas.base import ResponseModel
from ...schemas.partner import PartnerUpdate
from ...services.partner_service import PartnerService
from ...db.queries.user_query import UserQuery
from ...db.queries.partner_query import PartnerQuery
from ..deps import _require_partner

partner_profile_router = APIRouter()


def _partner_dict(p, user=None) -> dict:
    return {
        "id":                        str(p.id),
        "user_id":                   str(p.user_id),
        "name":                      p.name,
        "partner_type":              p.partner_type,
        "city":                      p.city,
        "state":                     getattr(p, "state", None),
        "legal_company_name":        getattr(p, "legal_company_name", None),
        "trade_name":                getattr(p, "trade_name", None),
        "registered_address":        getattr(p, "registered_address", None),
        "pin_code":                  getattr(p, "pin_code", None),
        "gstin":                     getattr(p, "gstin", None),
        "pan":                       getattr(p, "pan", None),
        "authorized_signatory_name": getattr(p, "authorized_signatory_name", None),
        "designation":               getattr(p, "designation", None),
        "data_1":                    getattr(p, "data_1", None),
        "data_2":                    getattr(p, "data_2", None),
        "data_3":                    getattr(p, "data_3", None),
        "email":                     str(user.email) if user else None,
        "mobile_no":                 user.mobile_no if user else None,
        "status":                    p.status,
        "allow_member_upload":       getattr(p, "allow_member_upload", True),
        "api_rate_limit":            p.api_rate_limit,
        "float_balance":             getattr(p, "float_balance", 0) or 0,
        "is_low_float":              (getattr(p, "float_balance", 0) or 0) <= (getattr(p, "low_float_threshold", 0) or 0),
        "card_color":                getattr(p, "card_color", None),
        "card_logo_key":             getattr(p, "card_logo_key", None),
    }


def _cr_dict(cr) -> dict:
    return {
        "id":               str(cr.id),
        "requested_fields": cr.requested_fields,
        "reason":           cr.reason,
        "status":           cr.status,
        "admin_note":       cr.admin_note,
        "reviewed_at":      cr.reviewed_at.isoformat() if cr.reviewed_at else None,
        "created_at":       cr.created_at.isoformat() if cr.created_at else None,
    }


class ChangeRequestCreate(BaseModel):
    requested_fields: dict
    reason: Optional[str] = None


class PartnerBrandingUpdate(BaseModel):
    card_color: Optional[str] = None


@partner_profile_router.get("", response_model=ResponseModel)
async def get_profile(request: Request, partner=Depends(_require_partner)):
    user = UserQuery().get_user_by_id(str(partner.user_id))
    return ResponseModel.ok(data=_partner_dict(partner, user))


@partner_profile_router.patch("", response_model=ResponseModel)
async def update_partner_branding(body: PartnerBrandingUpdate, partner=Depends(_require_partner)):
    updates = {}
    if body.card_color is not None:
        import re
        if not re.match(r"^#[0-9a-fA-F]{6}$", body.card_color):
            raise HTTPException(status_code=422, detail="card_color must be a valid hex color like #0050b0")
        updates["card_color"] = body.card_color
    if not updates:
        raise HTTPException(status_code=422, detail="No updatable fields provided")
    updated = PartnerQuery().update(str(partner.id), **updates)
    user = UserQuery().get_user_by_id(str(partner.user_id))
    return ResponseModel.ok(data=_partner_dict(updated, user))


@partner_profile_router.post("/change-request", response_model=ResponseModel, status_code=201)
async def submit_change_request(body: ChangeRequestCreate, request: Request, partner=Depends(_require_partner)):
    if not body.requested_fields:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="requested_fields cannot be empty")
    cr = PartnerService().create_change_request(
        partner_id=str(partner.id),
        requested_fields=body.requested_fields,
        reason=body.reason,
    )
    return ResponseModel.ok(data=_cr_dict(cr))


@partner_profile_router.get("/change-requests", response_model=ResponseModel)
async def list_my_change_requests(request: Request, skip: int = 0, limit: int = 20,
                                  partner=Depends(_require_partner)):
    total, rows = PartnerQuery().list_change_requests(
        partner_id=str(partner.id), skip=skip, limit=limit
    )
    return ResponseModel.ok(data={
        "data": [_cr_dict(cr) for cr in rows],
        "total": total,
        "skip": skip,
        "limit": limit,
    })


@partner_profile_router.post("/card-logo", response_model=ResponseModel, status_code=201)
async def upload_card_logo(partner=Depends(_require_partner), file: UploadFile = File(...)):
    from ...storage import get_storage
    if file.content_type not in ("image/png", "image/jpeg", "image/jpg", "image/webp"):
        raise HTTPException(status_code=422, detail="Logo must be a PNG, JPEG, or WEBP image")
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="Logo must be under 2MB")
    ext = (file.filename or "logo.png").rsplit(".", 1)[-1].lower()
    key = f"partners/{partner.id}/card-logo.{ext}"
    get_storage().upload(key, contents, content_type=file.content_type)
    PartnerQuery().update(str(partner.id), card_logo_key=key)
    return ResponseModel.ok(data={"card_logo_key": key})


@partner_profile_router.get("/card-logo/view")
async def view_card_logo(partner=Depends(_require_partner)):
    from fastapi import Response
    from ...storage import get_storage
    if not partner.card_logo_key:
        raise HTTPException(status_code=404, detail="No logo uploaded yet")
    data = get_storage().download(partner.card_logo_key)
    ext = partner.card_logo_key.rsplit(".", 1)[-1].lower()
    media_type = "image/png" if ext == "png" else "image/webp" if ext == "webp" else "image/jpeg"
    return Response(content=data, media_type=media_type)


@partner_profile_router.get("/card-preview")
async def preview_membership_card(partner=Depends(_require_partner)):
    from fastapi import Response
    from datetime import date, timedelta
    from ...storage import get_storage
    from ...services.pdf_service import PdfService
    logo_bytes = None
    if partner.card_logo_key:
        try:
            logo_bytes = get_storage().download(partner.card_logo_key)
        except Exception:
            logo_bytes = None

    class _DummyPlan:
        benefit_family = 4
        benefit_slots = 3
        benefit_claim = "Priority"
        benefit_aiqa = True
        benefit_teleconsult_sessions = 2
        benefit_hospital_cash = True
        benefit_wellness_sessions = 1
        benefit_emergency_assist = True

    today = date.today()
    pdf_bytes = PdfService().generate_membership_card_pdf(
        member_name="John Doe",
        member_email="john.doe@example.com",
        partner_name=partner.name,
        partner_type=partner.partner_type,
        plan_name="Sample Plan",
        plan=_DummyPlan(),
        membership_number="MEM-SAMPLE1",
        start_date=str(today),
        end_date=str(today + timedelta(days=365)),
        partner_address=partner.registered_address,
        partner_logo_bytes=logo_bytes,
        partner_color=partner.card_color,
    )
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="membership_card_preview.pdf"'},
    )
