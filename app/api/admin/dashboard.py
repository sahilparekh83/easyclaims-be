from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, extract
from ...schemas.base import ResponseModel
from ...db.session import session_scope
from ...db.models.user import User
from ...db.models.plan import MembershipPlan
from ...db.models.partner import Partner
from ...db.models.member import MemberEnrollment
from ...db.models.policy import Policy
from ...constants import UserType
from ..deps import require_permission

admin_dashboard_router = APIRouter()

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@admin_dashboard_router.get("", response_model=ResponseModel)
async def get_dashboard(
    request: Request,
    year: Optional[int] = Query(default=None),
    _=Depends(require_permission("dashboard", "view")),
):
    now = datetime.now(timezone.utc)
    target_year = year or now.year

    with session_scope() as session:
        # ── KPI counts ────────────────────────────────────────────────────────
        total_members = session.query(User).filter(
            User.user_type == UserType.CUSTOMER, User.is_deleted == False).count()
        active_members = session.query(User).filter(
            User.user_type == UserType.CUSTOMER, User.is_deleted == False, User.is_active == True).count()
        inactive_members = session.query(User).filter(
            User.user_type == UserType.CUSTOMER, User.is_deleted == False, User.is_active == False).count()
        members_without_policy = session.query(User).filter(
            User.user_type == UserType.CUSTOMER, User.is_deleted == False,
            ~session.query(Policy).filter(
                Policy.user_id == User.id, Policy.is_deleted == False
            ).exists()
        ).count()
        active_plans = session.query(MembershipPlan).filter(
            MembershipPlan.status == "Active", MembershipPlan.is_deleted == False).count()
        total_partners = session.query(Partner).filter(Partner.is_deleted == False).count()
        total_policies = session.query(Policy).filter(Policy.is_deleted == False).count()

        # ── Members growth — all 12 months of target_year ─────────────────────
        months_growth = []
        for m in range(1, 13):
            rows = (
                session.query(User, Partner.name.label("partner_name"))
                .outerjoin(MemberEnrollment, MemberEnrollment.user_id == User.id)
                .outerjoin(Partner, Partner.id == MemberEnrollment.partner_id)
                .filter(
                    User.user_type == UserType.CUSTOMER,
                    User.is_deleted == False,
                    extract("month", User.created_at) == m,
                    extract("year",  User.created_at) == target_year,
                )
                .all()
            )
            months_growth.append({
                "month": MONTH_NAMES[m - 1],
                "year": target_year,
                "month_num": m,
                "members": len(rows),
                "member_list": [
                    {
                        "id": str(u.id),
                        "name": u.name or u.email,
                        "email": u.email,
                        "partner_name": partner_name,
                        "joined": u.created_at.strftime("%d %b %Y") if u.created_at else None,
                    }
                    for u, partner_name in rows
                ],
            })

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
        "total_members":          total_members,
        "active_members":         active_members,
        "inactive_members":       inactive_members,
        "members_without_policy": members_without_policy,
        "active_plans":           active_plans,
        "total_partners":         total_partners,
        "total_policies":         total_policies,
        "members_growth":         months_growth,
        "policies_by_status":     policies_by_status,
        "members_by_partner":     members_by_partner,
        "review_queue":           review_queue,
        "review_queue_total":     review_total,
    })
