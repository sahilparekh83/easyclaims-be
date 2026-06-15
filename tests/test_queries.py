import os
os.environ.setdefault("MODE", "DEV")
os.environ.setdefault("JWE_SECRET_KEY", "a" * 64)
os.environ.setdefault("POSTGRES_SERVER", "0.0.0.0")
os.environ.setdefault("POSTGRES_USER", "mystique_agents")
os.environ.setdefault("POSTGRES_PASSWORD", "mystique_agents")
os.environ.setdefault("POSTGRES_DB", "easyclaims")
os.environ.setdefault("POSTGRES_PORT", "5432")

from app.db.queries.generic_repository import GenericRepository
from app.db.queries.user_query import UserQuery
from app.db.queries.role_query import RoleQuery


def test_generic_repository_instantiates():
    repo = GenericRepository()
    assert repo is not None


def test_user_query_instantiates():
    uq = UserQuery()
    assert uq is not None


def test_role_query_instantiates():
    rq = RoleQuery()
    assert rq is not None
