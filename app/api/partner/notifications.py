from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from ...schemas.base import ResponseModel
from ...db.queries.activity_query import NotificationQuery
from ..deps import _require_partner

partner_notifications_router = APIRouter()


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


@partner_notifications_router.get("/badge-counts", response_model=ResponseModel)
async def badge_counts(request: Request, partner=Depends(_require_partner)):
    """Return per-section unread badge counts for the partner sidebar."""
    nq = NotificationQuery()
    user_id = str(partner.user_id)
    members_count = nq.count_by_type(user_id, ["new_member"])
    total = nq.unread_count(user_id)
    return ResponseModel.ok(data={"members": members_count, "total": total})


@partner_notifications_router.patch("/mark-read-by-type", response_model=ResponseModel)
async def mark_read_by_type(type: str, request: Request, partner=Depends(_require_partner)):
    """Mark all unread notifications of a given type as read."""
    nq = NotificationQuery()
    count = nq.mark_read_by_type(str(partner.user_id), type)
    return ResponseModel.ok(data={"marked_read": count})


@partner_notifications_router.get("", response_model=ResponseModel)
async def list_notifications(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    partner=Depends(_require_partner),
):
    """List notifications for this partner. Unread shown first."""
    nq = NotificationQuery()
    total, notifs = nq.list_for_user(str(partner.user_id), unread_only=unread_only,
                                     skip=skip, limit=limit)
    unread_count = nq.unread_count(str(partner.user_id))
    return ResponseModel.ok(data={
        "data": [_notif_dict(n) for n in notifs],
        "total": total,
        "unread_count": unread_count,
        "skip": skip,
        "limit": limit,
    })


@partner_notifications_router.patch("/{notification_id}/read", response_model=ResponseModel)
async def mark_read(notification_id: UUID, request: Request, partner=Depends(_require_partner)):
    nq = NotificationQuery()
    if not nq.mark_read(str(notification_id), str(partner.user_id)):
        raise HTTPException(status_code=404, detail="Notification not found")
    return ResponseModel.ok(data={"message": "Notification marked as read"})


@partner_notifications_router.patch("/read-all", response_model=ResponseModel)
async def mark_all_read(request: Request, partner=Depends(_require_partner)):
    nq = NotificationQuery()
    count = nq.mark_all_read(str(partner.user_id))
    return ResponseModel.ok(data={"marked_read": count})


@partner_notifications_router.delete("/{notification_id}", response_model=ResponseModel)
async def delete_notification(notification_id: UUID, request: Request,
                               partner=Depends(_require_partner)):
    nq = NotificationQuery()
    if not nq.delete(str(notification_id), str(partner.user_id)):
        raise HTTPException(status_code=404, detail="Notification not found")
    return ResponseModel.ok(data={"message": "Notification removed"})
