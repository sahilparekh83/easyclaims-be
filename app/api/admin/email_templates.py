from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from ...schemas.base import ResponseModel
from ...db.queries.email_template_query import EmailTemplateQuery
from ...db.queries.partner_query import PartnerQuery
from ..deps import require_permission

admin_email_templates_router = APIRouter()


class TemplateUpdate(BaseModel):
    subject: Optional[str] = None
    html_body: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class OverrideCreate(BaseModel):
    partner_id: str
    subject: str
    html_body: str
    description: Optional[str] = ""


def _tpl_dict(t, partner_name: str = None) -> dict:
    return {
        "id": str(t.id),
        "slug": t.slug,
        "partner_id": str(t.partner_id) if t.partner_id else None,
        "partner_name": partner_name,
        "is_partner_override": t.partner_id is not None,
        "channel_type": getattr(t, "channel_type", "email") or "email",
        "description": t.description,
        "subject": t.subject,
        "html_body": t.html_body,
        "is_active": t.is_active,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


@admin_email_templates_router.get("", response_model=ResponseModel)
async def list_templates(request: Request, _=Depends(require_permission("email_templates", "view"))):
    """Lists system default templates only. Use /{slug}/overrides for a slug's partner overrides."""
    tq = EmailTemplateQuery()
    templates = tq.list_all()
    return ResponseModel.ok(data=[_tpl_dict(t) for t in templates])


@admin_email_templates_router.get("/{template_id}", response_model=ResponseModel)
async def get_template(template_id: str, request: Request, _=Depends(require_permission("email_templates", "view"))):
    tq = EmailTemplateQuery()
    t = tq.get_by_id(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    partner_name = None
    if t.partner_id:
        p = PartnerQuery().get_by_id(str(t.partner_id))
        partner_name = p.name if p else None
    return ResponseModel.ok(data=_tpl_dict(t, partner_name))


@admin_email_templates_router.patch("/{template_id}", response_model=ResponseModel)
async def update_template(template_id: str, body: TemplateUpdate,
                          request: Request, _=Depends(require_permission("email_templates", "edit"))):
    tq = EmailTemplateQuery()
    kwargs = body.model_dump(exclude_none=True)
    if not kwargs:
        raise HTTPException(status_code=422, detail="No fields to update")
    t = tq.update(template_id, **kwargs)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return ResponseModel.ok(data=_tpl_dict(t))


# ── Partner overrides (E6, 4th MOM) ──────────────────────────────────────────
# A partner-specific override takes priority over the system default when sending
# that email slug to that partner's members. No override = system default is used.

@admin_email_templates_router.get("/{slug}/overrides", response_model=ResponseModel)
async def list_overrides(slug: str, request: Request, _=Depends(require_permission("email_templates", "view"))):
    tq = EmailTemplateQuery()
    pq = PartnerQuery()
    overrides = tq.list_overrides_for_slug(slug)
    result = []
    for o in overrides:
        p = pq.get_by_id(str(o.partner_id))
        result.append(_tpl_dict(o, partner_name=p.name if p else None))
    return ResponseModel.ok(data=result)


@admin_email_templates_router.post("/{slug}/overrides", response_model=ResponseModel, status_code=201)
async def create_override(slug: str, body: OverrideCreate, request: Request, _=Depends(require_permission("email_templates", "add"))):
    pq = PartnerQuery()
    partner = pq.get_by_id(body.partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    tq = EmailTemplateQuery()
    try:
        t = tq.create_override(
            slug=slug, partner_id=body.partner_id,
            subject=body.subject, html_body=body.html_body,
            description=body.description or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return ResponseModel.ok(data=_tpl_dict(t, partner_name=partner.name))


@admin_email_templates_router.delete("/overrides/{template_id}", response_model=ResponseModel)
async def delete_override(template_id: str, request: Request, _=Depends(require_permission("email_templates", "delete"))):
    tq = EmailTemplateQuery()
    if not tq.delete_override(template_id):
        raise HTTPException(status_code=404, detail="Override not found (or this is a system default template, which cannot be deleted)")
    return ResponseModel.ok(data={"message": "Override removed — this partner now uses the system default"})
