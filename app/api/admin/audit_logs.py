from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...db.queries.audit_log_query import AuditLogQuery
from ..deps import require_permission

admin_audit_router = APIRouter()


@admin_audit_router.get("", response_model=ResponseModel)
async def list_audit_logs(
    request: Request,
    entity_type: str = None,
    entity_id: str = None,
    actor_id: str = None,
    skip: int = 0,
    limit: int = 50,
    _=Depends(require_permission("audit_logs", "view")),
):
    total, rows = AuditLogQuery().list_paginated(
        entity_type=entity_type, entity_id=entity_id, actor_id=actor_id, skip=skip, limit=limit
    )
    return ResponseModel.ok(data={
        "data": [
            {
                "id": str(r.id),
                "actor_id": r.actor_id,
                "actor_type": r.actor_type,
                "action": r.action,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "old_value": r.old_value,
                "new_value": r.new_value,
                "ip_address": r.ip_address,
                "note": r.note,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    })
