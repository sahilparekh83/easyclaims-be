from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException
from ..db.queries.member_query import MemberQuery
from ..db.queries.user_query import UserQuery
from ..db.queries.plan_query import PlanQuery
from ..db.queries.partner_query import PartnerQuery
from ..db.models.member import MemberEnrollment, MemberProfile, FamilyMember, Nominee, DpdpConsent
from ..schemas.member import (
    MemberCreate, ProfileUpdate,
    FamilyMemberCreate, FamilyMemberUpdate,
    NomineeCreate, NomineeUpdate,
    ConsentCreate,
)
from ..constants import UserType


class MemberService:
    def __init__(self):
        self.q = MemberQuery()
        self.user_q = UserQuery()
        self.plan_q = PlanQuery()
        self.partner_q = PartnerQuery()

    def create_member(self, data: MemberCreate) -> dict:
        existing = self.user_q.get_user_by_email(str(data.email))
        if existing:
            user = existing
        else:
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
        return {"user": user, "enrollment": enrollment}

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

    def switch_plan(self, user_id: str, partner_id: str, plan_id: str) -> MemberEnrollment:
        available = self.plan_q.list_for_partner(partner_id)
        available_ids = [str(p.id) for p in available]
        if plan_id not in available_ids:
            raise HTTPException(status_code=404, detail="Plan not available for this partner")
        e = self.q.update_enrollment(user_id, partner_id, plan_id=plan_id)
        if not e:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        return e

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
