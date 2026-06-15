import logging
from ..db.session import engine

logger = logging.getLogger(__name__)


async def startup_handler() -> None:
    logger.info("EasyClaims API starting up")
    from ..seeders import run_seed
    run_seed()


async def shutdown_handler() -> None:
    logger.info("EasyClaims API shutting down")
    engine.dispose()
