from fastapi import APIRouter, Depends, Request
from datetime import date
from ...schemas.base import ResponseModel
from ...db.queries.member_query import MemberQuery
from ...db.queries.policy_query import PolicyQuery
from ...db.session import session_scope
from ...db.models.activity import Notification
from ...agents import DashboardInsightsAgent
from ..deps import _require_partner

partner_ai_router = APIRouter()


@partner_ai_router.get("/insights", response_model=ResponseModel)
async def dashboard_insights(request: Request, partner=Depends(_require_partner)):
    """AI-generated insights for the partner dashboard."""
    partner_id = str(partner.id)
    mq = MemberQuery()
    pq = PolicyQuery()

    enrollments = mq.list_by_partner(partner_id)
    today = date.today()

    total = len(enrollments)
    active = sum(1 for e in enrollments if e.status == "Active")
    expiring_soon = sum(
        1 for e in enrollments
        if e.status == "Active" and e.end_date and 0 <= (e.end_date - today).days <= 30
    )

    policies = pq.list_by_partner(partner_id, skip=0, limit=1000)
    claims_count = sum(1 for p in policies if p.status == "rejected")

    with session_scope() as session:
        open_tickets = session.query(Notification).filter(
            Notification.recipient_user_id == partner.user_id,
            Notification.is_read == False,
        ).count()

    insights = DashboardInsightsAgent().generate(
        partner_name=partner.name,
        period=today.strftime("%B %Y"),
        total_members=total,
        active_members=active,
        expiring_soon=expiring_soon,
        renewals_done=0,
        float_balance=0.0,
        claims_count=claims_count,
        open_tickets=open_tickets,
        partner_id=partner_id,
    )
    return ResponseModel.ok(data=insights.model_dump())
