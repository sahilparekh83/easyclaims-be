import logging
from ..db.session import engine

logger = logging.getLogger(__name__)


async def startup_handler() -> None:
    logger.info("EasyClaims API starting up")
    from ..seeders import run_seed
    run_seed()
    from ..core.scheduler import start_scheduler
    start_scheduler()


async def shutdown_handler() -> None:
    logger.info("EasyClaims API shutting down")
    from ..core.scheduler import stop_scheduler
    stop_scheduler()
    engine.dispose()
