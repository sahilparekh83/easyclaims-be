import pytest


def test_generate_membership_card_pdf_returns_bytes():
    from unittest.mock import MagicMock
    from app.services.pdf_service import PdfService

    plan = MagicMock(
        benefit_family=4, benefit_slots=3, benefit_claim="Premium",
        benefit_aiqa=True, benefit_teleconsult_sessions=2,
        benefit_hospital_cash=False, benefit_wellness_sessions=1,
        benefit_emergency_assist=True,
    )

    pdf_bytes = PdfService().generate_membership_card_pdf(
        member_name="Alice Kumar",
        member_email="alice@example.com",
        partner_name="Acme Corp",
        partner_type="Broker",
        plan_name="Gold Plan",
        plan=plan,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF magic bytes
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_membership_card_pdf_handles_missing_name():
    from unittest.mock import MagicMock
    from app.services.pdf_service import PdfService

    plan = MagicMock(
        benefit_family=2, benefit_slots=2, benefit_claim="Standard",
        benefit_aiqa=False, benefit_teleconsult_sessions=0,
        benefit_hospital_cash=False, benefit_wellness_sessions=0,
        benefit_emergency_assist=False,
    )
    pdf_bytes = PdfService().generate_membership_card_pdf(
        member_name="",
        member_email="bob@example.com",
        partner_name="Beta Partners",
        partner_type="Corporate",
        plan_name="Silver Plan",
        plan=plan,
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
