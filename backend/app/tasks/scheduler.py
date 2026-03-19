import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.scan_service import run_scheduled_scans

logger = logging.getLogger(__name__)


class SchedulerManager:
    def __init__(self) -> None:
        self._scheduler: BackgroundScheduler | None = None

    def start(self) -> None:
        settings = get_settings()
        if not settings.scheduler_enabled:
            return
        if self._scheduler:
            return

        scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)
        scheduler.add_job(
            self._run_eod_job,
            'cron',
            hour=settings.scheduler_eod_hour,
            minute=settings.scheduler_eod_minute,
            id='eod_scan_job',
            replace_existing=True,
        )
        scheduler.start()
        self._scheduler = scheduler
        logger.info('Scheduler started (EOD %02d:%02d)', settings.scheduler_eod_hour, settings.scheduler_eod_minute)

    def stop(self) -> None:
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info('Scheduler stopped')

    @staticmethod
    def _run_eod_job() -> None:
        db = SessionLocal()
        try:
            run_scheduled_scans(db)
        finally:
            db.close()


scheduler_manager = SchedulerManager()
