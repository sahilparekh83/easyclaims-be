import json
import logging
import os

logger = logging.getLogger(__name__)


def seed_roles():
    from app.db.queries.role_query import RoleQuery
    roles_path = os.path.join(os.path.dirname(__file__), "roles.json")
    with open(roles_path) as f:
        roles_data = json.load(f)
    rq = RoleQuery()
    rq.seed_roles(roles_data)
    logger.info("Roles seeded: %d entries", len(roles_data))


def run_seed():
    try:
        seed_roles()
        logger.info("Seeding complete")
    except Exception as exc:
        logger.warning("Seeding failed (DB may not be ready): %s", exc)
