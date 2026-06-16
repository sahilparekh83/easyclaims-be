from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...db.session import session_scope
from ...db.models.user import User
from ...db.models.plan import MembershipPlan
from ...db.models.partner import Partner
from ...db.models.member import MemberEnrollment
from ...constants import UserType
from ..users import _require_superadmin

admin_dashboard_router = APIRouter()


@admin_dashboard_router.get("", response_model=ResponseModel)
async def get_dashboard(request: Request, _=Depends(_require_superadmin)):
    with session_scope() as session:
        total_members = session.query(User).filter(
            User.user_type == UserType.CUSTOMER, User.is_deleted == False).count()
        active_plans = session.query(MembershipPlan).filter(
            MembershipPlan.status == "Active", MembershipPlan.is_deleted == False).count()
        total_partners = session.query(Partner).filter(Partner.is_deleted == False).count()
        active_enrollments = session.query(MemberEnrollment).filter(
            MemberEnrollment.status == "active").count()
    return ResponseModel.ok(data={
        "total_members": total_members, "active_plans": active_plans,
        "total_partners": total_partners, "active_enrollments": active_enrollments,
    })
