from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from ...schemas.base import ResponseModel
from ...db.queries.whatsapp_template_query import WhatsAppTemplateQuery
from ...db.queries.partner_query import PartnerQuery
from ..deps import require_permission

admin_whatsapp_templates_router = APIRouter()


class WhatsAppTemplateUpdate(BaseModel):
    meta_template_name: Optional[str] = None
    meta_template_language: Optional[str] = None
    meta_template_status: Optional[str] = None
    header_type: Optional[str] = None
    variable_order: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class OverrideCreate(BaseModel):
    partner_id: str
    meta_template_name: Optional[str] = None
    meta_template_language: Optional[str] = "en"
    description: Optional[str] = ""


def _tpl_dict(t, partner_name: str = None) -> dict:
    return {
        "id": str(t.id),
        "slug": t.slug,
        "partner_id": str(t.partner_id) if t.partner_id else None,
        "partner_name": partner_name,
        "is_partner_override": t.partner_id is not None,
        "meta_template_name": t.meta_template_name,
        "meta_template_language": t.meta_template_language,
        "meta_template_status": t.meta_template_status,
        "header_type": t.header_type,
        "variable_order": t.variable_order,
        "description": t.description,
        "is_active": t.is_active,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


@admin_whatsapp_templates_router.get("", response_model=ResponseModel)
async def list_templates(request: Request, _=Depends(require_permission("whatsapp_templates", "view"))):
    """Lists system default templates only. Use /{slug}/overrides for a slug's partner overrides."""
    tq = WhatsAppTemplateQuery()
    templates = tq.list_all()
    return ResponseModel.ok(data=[_tpl_dict(t) for t in templates])


@admin_whatsapp_templates_router.get("/{template_id}", response_model=ResponseModel)
async def get_template(template_id: str, request: Request, _=Depends(require_permission("whatsapp_templates", "view"))):
    tq = WhatsAppTemplateQuery()
    t = tq.get_by_id(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    partner_name = None
    if t.partner_id:
        p = PartnerQuery().get_by_id(str(t.partner_id))
        partner_name = p.name if p else None
    return ResponseModel.ok(data=_tpl_dict(t, partner_name))


@admin_whatsapp_templates_router.patch("/{template_id}", response_model=ResponseModel)
async def update_template(template_id: str, body: WhatsAppTemplateUpdate,
                          request: Request, _=Depends(require_permission("whatsapp_templates", "edit"))):
    tq = WhatsAppTemplateQuery()
    kwargs = body.model_dump(exclude_none=True)
    if not kwargs:
        raise HTTPException(status_code=422, detail="No fields to update")
    t = tq.update(template_id, **kwargs)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return ResponseModel.ok(data=_tpl_dict(t))


# ── Partner overrides ────────────────────────────────────────────────────────
# A partner-specific override takes priority over the system default when sending
# that WhatsApp slug to that partner's members. No override = system default is used.

@admin_whatsapp_templates_router.get("/{slug}/overrides", response_model=ResponseModel)
async def list_overrides(slug: str, request: Request, _=Depends(require_permission("whatsapp_templates", "view"))):
    tq = WhatsAppTemplateQuery()
    pq = PartnerQuery()
    overrides = tq.list_overrides_for_slug(slug)
    result = []
    for o in overrides:
        p = pq.get_by_id(str(o.partner_id))
        result.append(_tpl_dict(o, partner_name=p.name if p else None))
    return ResponseModel.ok(data=result)


@admin_whatsapp_templates_router.post("/{slug}/overrides", response_model=ResponseModel, status_code=201)
async def create_override(slug: str, body: OverrideCreate, request: Request, _=Depends(require_permission("whatsapp_templates", "add"))):
    pq = PartnerQuery()
    partner = pq.get_by_id(body.partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    tq = WhatsAppTemplateQuery()
    try:
        t = tq.create_override(
            slug=slug, partner_id=body.partner_id,
            meta_template_name=body.meta_template_name,
            meta_template_language=body.meta_template_language or "en",
            description=body.description or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return ResponseModel.ok(data=_tpl_dict(t, partner_name=partner.name))


@admin_whatsapp_templates_router.delete("/overrides/{template_id}", response_model=ResponseModel)
async def delete_override(template_id: str, request: Request, _=Depends(require_permission("whatsapp_templates", "delete"))):
    tq = WhatsAppTemplateQuery()
    if not tq.delete_override(template_id):
        raise HTTPException(status_code=404, detail="Override not found (or this is a system default template, which cannot be deleted)")
    return ResponseModel.ok(data={"message": "Override removed — this partner now uses the system default"})
