import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None

DEFAULT_UPLOAD_REMINDER_RUN_HOUR = 9


def _get_upload_reminder_run_hour() -> int:
    try:
        from ..db.queries.system_setting_query import SystemSettingQuery
        val = SystemSettingQuery().get("upload_reminder_run_hour_ist")
        if val is not None:
            hour = int(val)
            if 0 <= hour <= 23:
                return hour
    except Exception as exc:
        logger.exception("Failed to read upload_reminder_run_hour_ist setting: %s", exc)
    return DEFAULT_UPLOAD_REMINDER_RUN_HOUR


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


def _run_policy_expiry_check_job():
    try:
        from ..services.cron_service import run_policy_expiry_check
        result = run_policy_expiry_check()
        logger.info("Policy expiry check result: %s", result)
    except Exception as exc:
        logger.exception("Policy expiry check failed: %s", exc)


def _run_policy_status_update_job():
    try:
        from ..services.cron_service import run_policy_status_update
        result = run_policy_status_update()
        logger.info("Policy status update result: %s", result)
    except Exception as exc:
        logger.exception("Policy status update failed: %s", exc)


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
    upload_reminder_hour = _get_upload_reminder_run_hour()
    _scheduler.add_job(
        _run_document_upload_reminder_job,
        trigger=CronTrigger(hour=upload_reminder_hour, minute=0),
        id="document_upload_reminder",
        replace_existing=True,
    )
    _scheduler.add_job(
        _run_policy_expiry_check_job,
        trigger=CronTrigger(hour=8, minute=0),
        id="policy_expiry_check",
        replace_existing=True,
    )
    _scheduler.add_job(
        _run_policy_status_update_job,
        trigger=CronTrigger(hour=0, minute=30),
        id="policy_status_update",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "APScheduler started — plan/policy expiry 08:00 IST, status update 00:30 IST, upload reminder %02d:00 IST",
        upload_reminder_hour,
    )


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
    _scheduler = None
