import os
os.environ.setdefault("MODE", "DEV")
os.environ.setdefault("JWE_SECRET_KEY", "a" * 64)
os.environ.setdefault("POSTGRES_SERVER", "0.0.0.0")
os.environ.setdefault("POSTGRES_USER", "mystique_agents")
os.environ.setdefault("POSTGRES_PASSWORD", "mystique_agents")
os.environ.setdefault("POSTGRES_DB", "easyclaims")
os.environ.setdefault("POSTGRES_PORT", "5432")

from app.schemas.base import ResponseModel


def test_response_model_structure():
    r = ResponseModel.ok(data={"test": 1})
    assert r.success is True
    assert r.data == {"test": 1}
    assert r.error is None


def test_response_model_fail_structure():
    r = ResponseModel.fail("not found", error_code="NOT_FOUND")
    assert r.success is False
    assert r.error.error_code == "NOT_FOUND"
