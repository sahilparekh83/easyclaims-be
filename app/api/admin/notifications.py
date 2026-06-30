from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from ...schemas.base import ResponseModel
from ...db.queries.activity_query import NotificationQuery
from ..users import _require_superadmin

admin_notifications_router = APIRouter()


def _notif_dict(n) -> dict:
    return {
        "id": str(n.id),
        "type": n.type,
        "title": n.title,
        "body": n.body,
        "ref_id": n.ref_id,
        "ref_type": n.ref_type,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


@admin_notifications_router.get("/badge-counts", response_model=ResponseModel)
async def badge_counts(request: Request, payload=Depends(_require_superadmin)):
    """Return total unread count for the admin sidebar bell badge."""
    user_id = request.state.user_payload["sub"]
    nq = NotificationQuery()
    total = nq.unread_count(user_id)
    return ResponseModel.ok(data={"total": total})


@admin_notifications_router.get("", response_model=ResponseModel)
async def list_notifications(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    payload=Depends(_require_superadmin),
):
    """List notifications for this admin. Unread shown first."""
    user_id = request.state.user_payload["sub"]
    nq = NotificationQuery()
    total, notifs = nq.list_for_user(user_id, unread_only=unread_only, skip=skip, limit=limit)
    unread_count = nq.unread_count(user_id)
    return ResponseModel.ok(data={
        "data": [_notif_dict(n) for n in notifs],
        "total": total,
        "unread_count": unread_count,
        "skip": skip,
        "limit": limit,
    })


@admin_notifications_router.patch("/{notification_id}/read", response_model=ResponseModel)
async def mark_read(notification_id: UUID, request: Request, _=Depends(_require_superadmin)):
    user_id = request.state.user_payload["sub"]
    nq = NotificationQuery()
    if not nq.mark_read(str(notification_id), user_id):
        raise HTTPException(status_code=404, detail="Notification not found")
    return ResponseModel.ok(data={"message": "Notification marked as read"})


@admin_notifications_router.patch("/read-all", response_model=ResponseModel)
async def mark_all_read(request: Request, _=Depends(_require_superadmin)):
    user_id = request.state.user_payload["sub"]
    nq = NotificationQuery()
    count = nq.mark_all_read(user_id)
    return ResponseModel.ok(data={"marked_read": count})


@admin_notifications_router.delete("/{notification_id}", response_model=ResponseModel)
async def delete_notification(notification_id: UUID, request: Request,
                               _=Depends(_require_superadmin)):
    user_id = request.state.user_payload["sub"]
    nq = NotificationQuery()
    if not nq.delete(str(notification_id), user_id):
        raise HTTPException(status_code=404, detail="Notification not found")
    return ResponseModel.ok(data={"message": "Notification removed"})
