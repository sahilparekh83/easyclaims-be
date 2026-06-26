import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_expiry_check_job():
    try:
        from ..services.cron_service import run_expiry_check
        result = run_expiry_check()
        logger.info("Scheduled expiry check result: %s", result)
    except Exception as exc:
        logger.exception("Scheduled expiry check failed: %s", exc)


def _run_document_upload_reminder_job():
    try:
        from ..services.cron_service import run_document_upload_reminder
        result = run_document_upload_reminder()
        logger.info("Document upload reminder result: %s", result)
    except Exception as exc:
        logger.exception("Document upload reminder failed: %s", exc)


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    _scheduler.add_job(
        _run_expiry_check_job,
        trigger=CronTrigger(hour=8, minute=0),
        id="plan_expiry_check",
        replace_existing=True,
    )
    _scheduler.add_job(
        _run_document_upload_reminder_job,
        trigger=IntervalTrigger(minutes=1),
        id="document_upload_reminder",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("APScheduler started — expiry check 08:00 IST, upload reminder every 2 min")


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
    _scheduler = None
