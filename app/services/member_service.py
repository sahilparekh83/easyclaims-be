import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException
from ..db.queries.member_query import MemberQuery
from ..db.queries.user_query import UserQuery
from ..db.queries.plan_query import PlanQuery
from ..db.queries.partner_query import PartnerQuery
from ..db.queries.activity_query import ActivityQuery
from ..db.models.member import MemberEnrollment, MemberProfile, FamilyMember, Nominee, DpdpConsent
from ..schemas.member import (
    MemberCreate, ProfileUpdate,
    FamilyMemberCreate, FamilyMemberUpdate,
    NomineeCreate, NomineeUpdate,
    ConsentCreate,
)
from ..constants import UserType

logger = logging.getLogger(__name__)


class MemberService:
    def __init__(self):
        self.q = MemberQuery()
        self.user_q = UserQuery()
        self.plan_q = PlanQuery()
        self.partner_q = PartnerQuery()

    def create_member(self, data: MemberCreate) -> dict:
        is_new_user = False
        existing = self.user_q.get_user_by_email(str(data.email))
        if existing:
            # Block re-enrollment under the same partner
            if data.partner_id and self.q.get_enrollment(str(existing.id), data.partner_id):
                raise HTTPException(
                    status_code=409,
                    detail=f"This member ({data.email}) is already enrolled under this partner.",
                )
            user = existing
        else:
            is_new_user = True
            user = self.user_q.create_user(
                email=str(data.email), name=data.name,
                user_type=UserType.CUSTOMER, mobile_no=data.mobile_no,
            )

        partner = self.partner_q.get_by_id(data.partner_id)
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")

        if data.plan_id:
            plan = self.plan_q.get_by_id(data.plan_id)
            if not plan or plan.status != "Active":
                raise HTTPException(status_code=404, detail="Plan not found or not active")
            plan_id = data.plan_id
        else:
            available = self.plan_q.list_for_partner(data.partner_id)
            if not available:
                raise HTTPException(status_code=422, detail="No active plans available for this partner")
            plan_id = str(available[0].id)

        enrollment = self.q.create_enrollment(str(user.id), data.partner_id, plan_id)
        self.q.upsert_profile(str(user.id))

        if is_new_user:
            self._send_welcome_email(user, partner)

        return {"user": user, "enrollment": enrollment}

    def _send_welcome_email(self, user, partner) -> None:
        try:
            from .email_service import EmailService
            from ..configs.common import get_settings
            settings = get_settings()
            login_url = f"{settings.FRONTEND_URL}/login"
            EmailService().send_welcome_member(
                to_email=user.email,
                member_name=user.name or user.email,
                partner_name=partner.name,
                login_url=login_url,
            )
        except Exception:
            logger.exception("Failed to send welcome email to %s", user.email)

    def list_enrollments(self, user_id: str) -> List[MemberEnrollment]:
        return self.q.list_enrollments(user_id)

    def get_enrollment(self, user_id: str, partner_id: str) -> MemberEnrollment:
        e = self.q.get_enrollment(user_id, partner_id)
        if not e:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        return e

    def get_active_enrollment(self, user_id: str, partner_id: Optional[str]) -> MemberEnrollment:
        if partner_id:
            e = self.q.get_enrollment(user_id, partner_id)
            if not e:
                raise HTTPException(status_code=403, detail="No enrollment found for this partner")
            return e
        e = self.q.get_first_active_enrollment(user_id)
        if not e:
            raise HTTPException(status_code=404, detail="No active enrollment found")
        return e

    def switch_plan(self, user_id: str, partner_id: str, plan_id: str,
                    changed_by: str = "system") -> MemberEnrollment:
        available = self.plan_q.list_for_partner(partner_id)
        available_ids = [str(p.id) for p in available]
        if plan_id not in available_ids:
            raise HTTPException(status_code=404, detail="Plan not available for this partner")

        # Get current plan before switching (for history)
        old_enrollment = self.q.get_enrollment(user_id, partner_id)
        old_plan_id = str(old_enrollment.plan_id) if old_enrollment else None

        e = self.q.update_enrollment(user_id, partner_id, plan_id=plan_id)
        if not e:
            raise HTTPException(status_code=404, detail="Enrollment not found")

        # Log history
        try:
            from ..db.queries.enrollment_history_query import EnrollmentHistoryQuery
            EnrollmentHistoryQuery().create(
                enrollment_id=str(e.id),
                user_id=user_id,
                partner_id=partner_id,
                to_plan_id=plan_id,
                from_plan_id=old_plan_id,
                action="plan_changed",
                changed_by=changed_by,
            )
        except Exception:
            logger.exception("Failed to log enrollment history for user %s", user_id)

        # Send email notification to member
        try:
            member = self.user_q.get_user_by_id(user_id)
            old_plan = self.plan_q.get_by_id(old_plan_id) if old_plan_id else None
            new_plan = self.plan_q.get_by_id(plan_id)
            if member and new_plan:
                from .email_service import EmailService
                EmailService().send_plan_changed(
                    to_email=member.email,
                    member_name=member.name or member.email,
                    old_plan=old_plan.name if old_plan else "—",
                    new_plan=new_plan.name,
                    changed_by=changed_by,
                )
        except Exception:
            logger.exception("Failed to send plan-changed email for user %s", user_id)

        return e

    def renew_enrollment(self, user_id: str, partner_id: str,
                         changed_by: str = "system") -> MemberEnrollment:
        """Extend enrollment by 1 year from today and set status=Active."""
        from datetime import date, timedelta
        e = self.q.get_enrollment(user_id, partner_id)
        if not e:
            raise HTTPException(status_code=404, detail="Enrollment not found")

        new_start = date.today()
        new_end = new_start + timedelta(days=365)
        updated = self.q.update_enrollment(
            user_id, partner_id,
            status="Active",
            start_date=new_start,
            end_date=new_end,
        )
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to renew enrollment")

        # Log history
        try:
            from ..db.queries.enrollment_history_query import EnrollmentHistoryQuery
            EnrollmentHistoryQuery().create(
                enrollment_id=str(updated.id),
                user_id=user_id,
                partner_id=partner_id,
                to_plan_id=str(updated.plan_id),
                from_plan_id=str(updated.plan_id),
                action="renewed",
                changed_by=changed_by,
                note=f"Renewed until {new_end.isoformat()}",
            )
        except Exception:
            logger.exception("Failed to log renewal history for user %s", user_id)

        # Send email notification to member
        try:
            member = self.user_q.get_user_by_id(user_id)
            plan = self.plan_q.get_by_id(str(updated.plan_id))
            if member and plan:
                from .email_service import EmailService
                EmailService().send_from_template(
                    to_email=member.email,
                    slug="enrollment_renewed",
                    context={
                        "member_name": member.name or member.email,
                        "plan_name": plan.name,
                        "end_date": str(new_end),
                    },
                )
                # In-app notification
                from ..db.queries.activity_query import NotificationQuery
                NotificationQuery().create(
                    recipient_user_id=user_id,
                    type="plan_renewed",
                    title="Your plan has been renewed",
                    body=f"Your plan '{plan.name}' has been renewed until {new_end.isoformat()}.",
                    ref_id=str(updated.plan_id),
                    ref_type="plan",
                )
        except Exception:
            logger.exception("Failed to send renewal email for user %s", user_id)

        return updated

    def get_profile(self, user_id: str) -> dict:
        user = self.user_q.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        profile = self.q.get_profile(user_id)
        return {"user": user, "profile": profile}

    def update_profile(self, user_id: str, data: ProfileUpdate) -> dict:
        user_field_names = {"name", "mobile_no"}
        user_fields, profile_fields = {}, {}
        for field, value in data.model_dump(exclude_none=True).items():
            if field in user_field_names:
                user_fields[field] = value
            else:
                profile_fields[field] = value
        if user_fields:
            self.user_q.update_user(user_id, **user_fields)
        if profile_fields:
            self.q.upsert_profile(user_id, **profile_fields)
        return self.get_profile(user_id)

    def list_family(self, user_id: str) -> List[FamilyMember]:
        return self.q.list_family(user_id)

    def add_family_member(self, user_id: str, data: FamilyMemberCreate) -> FamilyMember:
        return self.q.create_family_member(user_id, **data.model_dump())

    def update_family_member(self, user_id: str, member_id: str, data: FamilyMemberUpdate) -> FamilyMember:
        m = self.q.update_family_member(member_id, user_id, **data.model_dump(exclude_none=True))
        if not m:
            raise HTTPException(status_code=404, detail="Family member not found")
        return m

    def delete_family_member(self, user_id: str, member_id: str) -> None:
        if not self.q.delete_family_member(member_id, user_id):
            raise HTTPException(status_code=404, detail="Family member not found")

    def list_nominees(self, user_id: str) -> List[Nominee]:
        return self.q.list_nominees(user_id)

    def add_nominee(self, user_id: str, data: NomineeCreate) -> Nominee:
        current = self.q.total_share(user_id)
        if current + data.share_percent > 100:
            raise HTTPException(status_code=422,
                                detail=f"Total share would exceed 100% (current: {current}%)")
        return self.q.create_nominee(user_id, **data.model_dump())

    def update_nominee(self, user_id: str, nominee_id: str, data: NomineeUpdate) -> Nominee:
        kwargs = data.model_dump(exclude_none=True)
        if "share_percent" in kwargs:
            current = self.q.total_share(user_id, exclude_id=nominee_id)
            if current + kwargs["share_percent"] > 100:
                raise HTTPException(status_code=422, detail="Total share would exceed 100%")
        n = self.q.update_nominee(nominee_id, user_id, **kwargs)
        if not n:
            raise HTTPException(status_code=404, detail="Nominee not found")
        return n

    def delete_nominee(self, user_id: str, nominee_id: str) -> None:
        if not self.q.delete_nominee(nominee_id, user_id):
            raise HTTPException(status_code=404, detail="Nominee not found")

    def get_consent(self, user_id: str) -> DpdpConsent:
        c = self.q.get_latest_consent(user_id)
        if not c:
            raise HTTPException(status_code=404, detail="No consent record found")
        return c

    def record_consent(self, user_id: str, data: ConsentCreate) -> DpdpConsent:
        return self.q.create_consent(
            user_id, consented_at=datetime.now(timezone.utc),
            version=data.version, source=data.source,
        )
