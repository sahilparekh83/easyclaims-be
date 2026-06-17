from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from ...schemas.base import ResponseModel
from ...db.queries.email_template_query import EmailTemplateQuery
from ..users import _require_superadmin

admin_email_templates_router = APIRouter()


class TemplateUpdate(BaseModel):
    subject: Optional[str] = None
    html_body: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


def _tpl_dict(t) -> dict:
    return {
        "id": str(t.id),
        "slug": t.slug,
        "description": t.description,
        "subject": t.subject,
        "html_body": t.html_body,
        "is_active": t.is_active,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


@admin_email_templates_router.get("", response_model=ResponseModel)
async def list_templates(request: Request, _=Depends(_require_superadmin)):
    tq = EmailTemplateQuery()
    templates = tq.list_all()
    return ResponseModel.ok(data=[_tpl_dict(t) for t in templates])


@admin_email_templates_router.get("/{template_id}", response_model=ResponseModel)
async def get_template(template_id: str, request: Request, _=Depends(_require_superadmin)):
    tq = EmailTemplateQuery()
    t = tq.get_by_id(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return ResponseModel.ok(data=_tpl_dict(t))


@admin_email_templates_router.patch("/{template_id}", response_model=ResponseModel)
async def update_template(template_id: str, body: TemplateUpdate,
                          request: Request, _=Depends(_require_superadmin)):
    tq = EmailTemplateQuery()
    kwargs = body.model_dump(exclude_none=True)
    if not kwargs:
        raise HTTPException(status_code=422, detail="No fields to update")
    t = tq.update(template_id, **kwargs)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return ResponseModel.ok(data=_tpl_dict(t))
