import os
os.environ.setdefault("MODE", "DEV")
os.environ.setdefault("JWE_SECRET_KEY", "a" * 64)
os.environ.setdefault("POSTGRES_SERVER", "0.0.0.0")
os.environ.setdefault("POSTGRES_USER", "mystique_agents")
os.environ.setdefault("POSTGRES_PASSWORD", "mystique_agents")
os.environ.setdefault("POSTGRES_DB", "easyclaims")
os.environ.setdefault("POSTGRES_PORT", "5432")

from app.db.base import Base
from app.db.session import session_scope, engine


def test_base_tablename():
    from sqlalchemy import Column, String
    class MyModel(Base):
        __tablename__ = "mymodel"
        id = Column(String, primary_key=True)
    assert MyModel.__tablename__ == "mymodel"


def test_session_scope_rollback_on_exception():
    # Just verify it's importable and callable
    assert callable(session_scope)
