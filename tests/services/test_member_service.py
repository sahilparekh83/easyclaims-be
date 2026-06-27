from unittest.mock import patch, MagicMock
import pytest


@patch("app.services.member_service.MemberService._send_welcome_email")
@patch("app.services.member_service.MemberService._send_welcome_whatsapp")
@patch("app.services.member_service.MemberService._send_membership_card_email")
@patch("app.services.member_service.MemberService._send_membership_card_whatsapp")
@patch("app.services.member_service.MemberService._notify_admins_new_member")
def test_new_user_gets_welcome_and_card(mock_admin, mock_card_wa, mock_card_email,
                                         mock_wa, mock_email, monkeypatch):
    svc = _make_service(monkeypatch, is_new_user=True)
    svc.create_member(_make_member_create())
    mock_email.assert_called_once()
    mock_wa.assert_called_once()
    mock_card_email.assert_called_once()
    mock_card_wa.assert_called_once()


@patch("app.services.member_service.MemberService._send_new_partner_email")
@patch("app.services.member_service.MemberService._send_new_partner_whatsapp")
@patch("app.services.member_service.MemberService._send_membership_card_email")
@patch("app.services.member_service.MemberService._send_membership_card_whatsapp")
@patch("app.services.member_service.MemberService._notify_admins_new_member")
def test_existing_user_gets_new_partner_and_card(mock_admin, mock_card_wa, mock_card_email,
                                                   mock_wa, mock_email, monkeypatch):
    svc = _make_service(monkeypatch, is_new_user=False)
    svc.create_member(_make_member_create())
    mock_email.assert_called_once()
    mock_wa.assert_called_once()
    mock_card_email.assert_called_once()
    mock_card_wa.assert_called_once()


def _make_member_create():
    from app.schemas.member import MemberCreate
    return MemberCreate(
        email="test@example.com", name="Alice", mobile_no="9876543210",
        partner_id="00000000-0000-0000-0000-000000000001",
        plan_id="00000000-0000-0000-0000-000000000002",
    )


def _make_service(monkeypatch, is_new_user: bool):
    from app.services.member_service import MemberService
    svc = MemberService.__new__(MemberService)

    fake_user = MagicMock(id="uid-1", email="test@example.com", name="Alice", mobile_no="9876543210")
    fake_partner = MagicMock(id="pid-1", name="Acme", partner_type="Broker")
    fake_plan = MagicMock(
        id="plan-1", name="Gold", status="Active",
        benefit_family=4, benefit_slots=3, benefit_claim="Premium",
        benefit_aiqa=True, benefit_teleconsult_sessions=2,
        benefit_hospital_cash=False, benefit_wellness_sessions=1,
        benefit_emergency_assist=True,
    )
    fake_enrollment = MagicMock(id="enr-1", plan_id="plan-1")

    user_q = MagicMock()
    user_q.get_user_by_email.return_value = None if is_new_user else fake_user
    user_q.create_user.return_value = fake_user

    member_q = MagicMock()
    member_q.get_enrollment.return_value = None
    member_q.create_enrollment.return_value = fake_enrollment

    partner_q = MagicMock()
    partner_q.get_by_id.return_value = fake_partner

    plan_q = MagicMock()
    plan_q.get_by_id.return_value = fake_plan
    plan_q.list_for_partner.return_value = [fake_plan]

    svc.q = member_q
    svc.user_q = user_q
    svc.plan_q = plan_q
    svc.partner_q = partner_q
    return svc
