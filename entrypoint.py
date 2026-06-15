import os
import logging
import uvicorn
from alembic.config import Config as AlembicConfig
from alembic import command

logger = logging.getLogger(__name__)


def run_migrations():
    alembic_ini = os.path.join(os.path.dirname(__file__), "alembic.ini")
    cfg = AlembicConfig(alembic_ini)
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "alembic"))
    logger.info("Running Alembic migrations...")
    command.upgrade(cfg, "head")
    logger.info("Migrations complete")


if __name__ == "__main__":
    run_migrations()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=2,
    )
