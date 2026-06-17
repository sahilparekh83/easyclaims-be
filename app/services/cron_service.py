"""
Daily cron jobs for plan expiry:
  - Warn members 2 days before plan expiry
  - Mark expired enrollments + notify member, partner, admin
"""
import logging
from datetime import date, timedelta

from ..db.session import session_scope
from ..db.models.member import MemberEnrollment
from ..db.models.partner import Partner
from ..db.models.plan import MembershipPlan
from ..db.models.user import User
from ..db.queries.activity_query import NotificationQuery
from ..db.queries.enrollment_history_query import EnrollmentHistoryQuery
from ..services.email_service import EmailService

logger = logging.getLogger(__name__)


def _get_partner_contacts(session, partner_id) -> list[str]:
    """Return email addresses of users with partner-level access for a given partner."""
    partner = session.query(Partner).filter(Partner.id == partner_id).first()
    if partner:
        u = session.query(User).filter(User.id == partner.user_id).first()
        if u and u.email:
            return [u.email]
    return []


def run_expiry_check() -> dict:
    """
    Check enrollments:
      1. Expiring in exactly 2 days → send warning email + in-app notification
      2. Already expired (end_date < today, status=Active) → mark Expired, send emails

    Returns summary dict for the API trigger endpoint.
    """
    email_svc = EmailService()
    nq = NotificationQuery()
    hist_q = EnrollmentHistoryQuery()

    today = date.today()
    warning_date = today + timedelta(days=2)

    warned = 0
    expired = 0
    errors = 0

    # ── 1. Expiry warning (2 days out) ─────────────────────────────────────────
    try:
        with session_scope() as session:
            expiring = (
                session.query(MemberEnrollment)
                .filter(
                    MemberEnrollment.end_date == warning_date,
                    MemberEnrollment.status == "Active",
                )
                .all()
            )
            expiring_data = [
                {
                    "id": str(e.id),
                    "user_id": str(e.user_id),
                    "partner_id": str(e.partner_id),
                    "plan_id": str(e.plan_id),
                    "end_date": str(e.end_date),
                }
                for e in expiring
            ]
    except Exception as exc:
        logger.exception("Failed to query expiring enrollments: %s", exc)
        expiring_data = []
        errors += 1

    for e in expiring_data:
        try:
            with session_scope() as session:
                member = session.query(User).filter(User.id == e["user_id"]).first()
                plan = session.query(MembershipPlan).filter(MembershipPlan.id == e["plan_id"]).first()
                if not member or not plan:
                    continue

                # In-app notification
                nq.create(
                    recipient_user_id=e["user_id"],
                    type="plan_expiry_warning",
                    title="Your plan expires in 2 days",
                    body=f"Your plan '{plan.name}' expires on {e['end_date']}. Contact your partner to renew.",
                    ref_id=e["plan_id"],
                    ref_type="plan",
                )

                # Email
                email_svc.send_plan_expiry_warning(
                    to_email=member.email,
                    member_name=member.name or member.email,
                    plan_name=plan.name,
                    end_date=e["end_date"],
                    days_left=2,
                )
                warned += 1
        except Exception as exc:
            logger.exception("Error processing expiry warning for enrollment %s: %s", e["id"], exc)
            errors += 1

    # ── 2. Mark expired + notify ────────────────────────────────────────────────
    try:
        with session_scope() as session:
            expired_rows = (
                session.query(MemberEnrollment)
                .filter(
                    MemberEnrollment.end_date < today,
                    MemberEnrollment.status == "Active",
                )
                .all()
            )
            expired_data = [
                {
                    "id": str(e.id),
                    "user_id": str(e.user_id),
                    "partner_id": str(e.partner_id),
                    "plan_id": str(e.plan_id),
                    "end_date": str(e.end_date),
                }
                for e in expired_rows
            ]
    except Exception as exc:
        logger.exception("Failed to query expired enrollments: %s", exc)
        expired_data = []
        errors += 1

    for e in expired_data:
        try:
            # Mark as expired
            with session_scope() as session:
                enrollment = session.query(MemberEnrollment).filter(
                    MemberEnrollment.id == e["id"]
                ).first()
                if enrollment:
                    enrollment.status = "Expired"
                    session.flush()

            # Log history
            hist_q.create(
                enrollment_id=e["id"],
                user_id=e["user_id"],
                partner_id=e["partner_id"],
                to_plan_id=e["plan_id"],
                from_plan_id=e["plan_id"],
                action="expired",
                changed_by="system",
                note=f"Auto-expired on {date.today().isoformat()}",
            )

            with session_scope() as session:
                member = session.query(User).filter(User.id == e["user_id"]).first()
                plan = session.query(MembershipPlan).filter(MembershipPlan.id == e["plan_id"]).first()
                partner = session.query(Partner).filter(Partner.id == e["partner_id"]).first()
                partner_user = (
                    session.query(User).filter(User.id == partner.user_id).first()
                    if partner and hasattr(partner, "user_id")
                    else None
                )
                if not member or not plan:
                    continue

                member_name = member.name or member.email
                plan_name = plan.name
                end_date = e["end_date"]

                # In-app: member
                nq.create(
                    recipient_user_id=e["user_id"],
                    type="plan_expired",
                    title="Your plan has expired",
                    body=f"Your plan '{plan_name}' expired on {end_date}. Contact your partner to renew.",
                    ref_id=e["plan_id"],
                    ref_type="plan",
                )

                # Email: member
                email_svc.send_plan_expired(
                    to_email=member.email,
                    member_name=member_name,
                    plan_name=plan_name,
                    end_date=end_date,
                )

                # Email: partner
                if partner_user and partner_user.email:
                    email_svc.send_plan_expired_partner(
                        to_email=partner_user.email,
                        partner_name=partner.name,
                        member_name=member_name,
                        member_email=member.email,
                        plan_name=plan_name,
                        end_date=end_date,
                    )

            expired += 1
        except Exception as exc:
            logger.exception("Error processing expired enrollment %s: %s", e["id"], exc)
            errors += 1

    logger.info("Expiry check: warned=%d, expired=%d, errors=%d", warned, expired, errors)
    return {"warned": warned, "expired": expired, "errors": errors}
