import logging
from datetime import datetime, timezone

from app.tasks.scheduler import SchedulerManager
from app.utils.datetime_utils import as_kst, is_korean_trading_day


def test_is_korean_trading_day_uses_asia_seoul_date():
    friday_utc = datetime(2026, 3, 20, 5, 0, tzinfo=timezone.utc)  # 2026-03-20 14:00 KST (Fri)
    saturday_utc = datetime(2026, 3, 20, 18, 0, tzinfo=timezone.utc)  # 2026-03-21 03:00 KST (Sat)

    assert as_kst(friday_utc).weekday() == 4
    assert is_korean_trading_day(friday_utc) is True
    assert as_kst(saturday_utc).weekday() == 5
    assert is_korean_trading_day(saturday_utc) is False


def test_scheduler_skips_weekend(monkeypatch, caplog):
    import app.tasks.scheduler as scheduler_module

    monkeypatch.setattr(scheduler_module, 'is_korean_trading_day', lambda: False)
    monkeypatch.setattr(
        scheduler_module,
        'as_kst',
        lambda now=None: datetime(2026, 3, 21, 10, 0, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(scheduler_module, 'SessionLocal', lambda: (_ for _ in ()).throw(AssertionError('no db on weekend')))
    monkeypatch.setattr(scheduler_module, 'run_scheduled_scans', lambda db: (_ for _ in ()).throw(AssertionError('no run')))

    with caplog.at_level(logging.INFO):
        SchedulerManager._run_eod_job()

    assert 'Skipping scheduled scan: non-trading day (weekend)' in caplog.text


def test_scheduler_runs_weekday(monkeypatch):
    import app.tasks.scheduler as scheduler_module

    class DummyDB:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    holder = {'db': None}
    db = DummyDB()

    monkeypatch.setattr(scheduler_module, 'is_korean_trading_day', lambda: True)
    monkeypatch.setattr(scheduler_module, 'SessionLocal', lambda: db)
    monkeypatch.setattr(scheduler_module, 'run_scheduled_scans', lambda sess: holder.update(db=sess))

    SchedulerManager._run_eod_job()

    assert holder['db'] is db
    assert db.closed is True
