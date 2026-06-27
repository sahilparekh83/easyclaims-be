from unittest.mock import patch, MagicMock
import pytest
import sys


@patch("app.services.email_service.EmailTemplateQuery")
@patch("app.services.email_service.EmailService._send")
def test_send_new_partner_welcome_calls_template(mock_send, mock_tq_cls):
    mock_tq = MagicMock()
    mock_tq_cls.return_value = mock_tq
    mock_tq.get_by_slug.return_value = MagicMock(
        subject="You've Been Enrolled with {{ partner_name }} on EasyClaims",
        html_body="<p>{{ member_name }} / {{ partner_name }}</p>",
    )
    mock_send.return_value = True
    from app.services.email_service import EmailService
    svc = EmailService()
    result = svc.send_new_partner_welcome(
        to_email="test@example.com",
        member_name="Alice",
        partner_name="Acme Corp",
        login_url="https://app.easyclaims.in/login",
    )
    mock_tq.get_by_slug.assert_called_once_with("welcome_member_new_partner")
    assert result is True


def test_send_membership_card_attaches_pdf():
    with patch("app.services.email_service.EmailTemplateQuery") as mock_tq_cls, \
         patch("app.services.email_service.EmailService._send") as mock_send, \
         patch("app.services.pdf_service.PdfService") as mock_pdf_cls:
        mock_tq = MagicMock()
        mock_tq_cls.return_value = mock_tq
        mock_tq.get_by_slug.return_value = MagicMock(
            subject="Your EasyClaims Membership Card — {{ plan_name }}",
            html_body="<p>{{ member_name }}</p>",
        )
        mock_pdf = MagicMock()
        mock_pdf_cls.return_value = mock_pdf
        mock_pdf.generate_membership_card_pdf.return_value = b"%PDF-fake"
        mock_send.return_value = True

        plan = MagicMock(
            benefit_family=4, benefit_slots=3, benefit_claim="Premium",
            benefit_aiqa=True, benefit_teleconsult_sessions=2,
            benefit_hospital_cash=False, benefit_wellness_sessions=1,
            benefit_emergency_assist=True,
        )
        from app.services.email_service import EmailService
        svc = EmailService()
        result = svc.send_membership_card(
            to_email="test@example.com",
            member_name="Alice",
            member_email="alice@example.com",
            partner_name="Acme Corp",
            partner_type="Broker",
            plan_name="Gold Plan",
            plan=plan,
            login_url="https://app.easyclaims.in/login",
        )
        mock_tq.get_by_slug.assert_called_once_with("membership_card")
        mock_pdf.generate_membership_card_pdf.assert_called_once()
        # _send called with attachment bytes
        call_kwargs = mock_send.call_args
        assert call_kwargs.kwargs.get("attachment_bytes") == b"%PDF-fake"
        assert call_kwargs.kwargs.get("attachment_filename") == "easyclaims_membership_card.pdf"
        assert result is True
