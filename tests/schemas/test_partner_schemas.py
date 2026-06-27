import pytest
from pydantic import ValidationError
from app.schemas.partner import PartnerCreate, PartnerUpdate

VALID_BASE = {
    "name": "Test Partner",
    "email": "partner@test.com",
    "mobile_no": "9876543210",
    "legal_company_name": "Test Co Ltd",
    "trade_name": "TestBrand",
    "registered_address": "123 Main St",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pin_code": "400001",
    "gstin": "27AAPFU0939F1ZV",
    "pan": "AAPFU0939F",
    "authorized_signatory_name": "John Doe",
    "designation": "Director",
}


def test_partner_create_valid():
    p = PartnerCreate(**VALID_BASE)
    assert p.legal_company_name == "Test Co Ltd"
    assert p.gstin == "27AAPFU0939F1ZV"
    assert p.pan == "AAPFU0939F"


def test_gstin_invalid():
    data = {**VALID_BASE, "gstin": "INVALID123"}
    with pytest.raises(ValidationError) as exc:
        PartnerCreate(**data)
    assert "GSTIN" in str(exc.value)


def test_pan_invalid():
    data = {**VALID_BASE, "pan": "invalid"}
    with pytest.raises(ValidationError) as exc:
        PartnerCreate(**data)
    assert "PAN" in str(exc.value)


def test_pin_code_invalid():
    data = {**VALID_BASE, "pin_code": "12345"}  # only 5 digits
    with pytest.raises(ValidationError) as exc:
        PartnerCreate(**data)
    assert "pin" in str(exc.value).lower()


def test_mandatory_field_missing():
    data = {**VALID_BASE}
    del data["legal_company_name"]
    with pytest.raises(ValidationError):
        PartnerCreate(**data)


def test_partner_update_partial():
    p = PartnerUpdate(city="Delhi", state="Delhi")
    assert p.city == "Delhi"
    assert p.legal_company_name is None
