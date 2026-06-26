from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, extract
from ...schemas.base import ResponseModel
from ...db.session import session_scope
from ...db.models.user import User
from ...db.models.plan import MembershipPlan
from ...db.models.partner import Partner
from ...db.models.member import MemberEnrollment
from ...db.models.policy import Policy
from ...constants import UserType
from ..users import _require_superadmin

admin_dashboard_router = APIRouter()

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@admin_dashboard_router.get("", response_model=ResponseModel)
async def get_dashboard(request: Request, _=Depends(_require_superadmin)):
    now = datetime.now(timezone.utc)

    with session_scope() as session:
        # ── KPI counts ────────────────────────────────────────────────────────
        total_members = session.query(User).filter(
            User.user_type == UserType.CUSTOMER, User.is_deleted == False).count()
        active_plans = session.query(MembershipPlan).filter(
            MembershipPlan.status == "Active", MembershipPlan.is_deleted == False).count()
        total_partners = session.query(Partner).filter(Partner.is_deleted == False).count()
        total_policies = session.query(Policy).filter(Policy.is_deleted == False).count()

        # ── Members growth — last 6 months ────────────────────────────────────
        months_growth = []
        for i in range(5, -1, -1):
            d = now - timedelta(days=i * 30)
            m, y = d.month, d.year
            count = session.query(User).filter(
                User.user_type == UserType.CUSTOMER,
                User.is_deleted == False,
                extract("month", User.created_at) == m,
                extract("year",  User.created_at) == y,
            ).count()
            months_growth.append({"month": MONTH_NAMES[m - 1], "members": count})

        # ── Policies by status ────────────────────────────────────────────────
        status_rows = (
            session.query(Policy.status, func.count(Policy.id))
            .filter(Policy.is_deleted == False)
            .group_by(Policy.status)
            .all()
        )
        policies_by_status = [{"status": s, "count": c} for s, c in status_rows]

        # ── Members by partner ────────────────────────────────────────────────
        partner_rows = (
            session.query(Partner.name, func.count(MemberEnrollment.user_id))
            .join(MemberEnrollment, MemberEnrollment.partner_id == Partner.id)
            .filter(Partner.is_deleted == False)
            .group_by(Partner.id, Partner.name)
            .order_by(func.count(MemberEnrollment.user_id).desc())
            .limit(6)
            .all()
        )
        members_by_partner = [{"partner": n, "members": c} for n, c in partner_rows]

        # ── Need-review policies queue ────────────────────────────────────────
        review_total = (
            session.query(Policy)
            .filter(Policy.status == "need_review", Policy.is_deleted == False)
            .count()
        )
        review_policies = (
            session.query(Policy)
            .filter(Policy.status == "need_review", Policy.is_deleted == False)
            .order_by(Policy.created_at.desc())
            .limit(5)
            .all()
        )
        review_queue = [
            {
                "id": str(p.id),
                "policy_number": p.policy_number,
                "file_name": p.file_name,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in review_policies
        ]

    return ResponseModel.ok(data={
        "total_members":       total_members,
        "active_plans":        active_plans,
        "total_partners":      total_partners,
        "total_policies":      total_policies,
        "members_growth":      months_growth,
        "policies_by_status":  policies_by_status,
        "members_by_partner":  members_by_partner,
        "review_queue":        review_queue,
        "review_queue_total":  review_total,
    })
