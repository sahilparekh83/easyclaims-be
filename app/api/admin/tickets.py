from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from ...schemas.base import ResponseModel
from ...db.queries.ticket_query import TicketQuery
from ...db.queries.user_query import UserQuery
from ...db.queries.partner_query import PartnerQuery
from ..users import _require_superadmin

admin_tickets_router = APIRouter()

_VALID_STATUSES = ("open", "in_progress", "resolved")


def _ticket_dict(t, member_name=None, member_email=None, partner_name=None) -> dict:
    return {
        "id": str(t.id),
        "channel": t.channel,
        "category": t.category,
        "priority": t.priority,
        "status": t.status,
        "summary": t.summary,
        "member_id": str(t.user_id) if t.user_id else None,
        "member_name": member_name,
        "member_email": member_email,
        "partner_id": str(t.partner_id) if t.partner_id else None,
        "partner_name": partner_name,
        "ref_policy_id": str(t.ref_policy_id) if t.ref_policy_id else None,
        "is_duplicate": t.is_duplicate,
        "duplicate_of_ticket_id": str(t.duplicate_of_ticket_id) if t.duplicate_of_ticket_id else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@admin_tickets_router.get("", response_model=ResponseModel)
async def list_tickets(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    category: str = None,
    _=Depends(_require_superadmin),
):
    """AI Review Queue — list tickets raised via Claim Assistant / WhatsApp / Email."""
    tq = TicketQuery()
    uq = UserQuery()
    pq = PartnerQuery()

    tickets = tq.list_all(skip=skip, limit=limit)
    if status:
        tickets = [t for t in tickets if t.status == status]
    if category:
        tickets = [t for t in tickets if t.category == category]

    result = []
    for t in tickets:
        member = uq.get_user_by_id(str(t.user_id)) if t.user_id else None
        partner = pq.get_by_id(str(t.partner_id)) if t.partner_id else None
        result.append(_ticket_dict(
            t,
            member_name=member.name if member else None,
            member_email=member.email if member else None,
            partner_name=partner.name if partner else None,
        ))

    return ResponseModel.ok(data={
        "data": result,
        "open_count": tq.count_open(),
        "skip": skip,
        "limit": limit,
    })


@admin_tickets_router.patch("/{ticket_id}/status", response_model=ResponseModel)
async def update_ticket_status(ticket_id: UUID, status: str, request: Request,
                               _=Depends(_require_superadmin)):
    if status not in _VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {_VALID_STATUSES}")
    if not TicketQuery().update_status(str(ticket_id), status):
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ResponseModel.ok(data={"message": "Ticket status updated"})
