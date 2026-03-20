from datetime import date

from app.models.foreign_investor_daily import ForeignInvestorDaily
from app.providers.base import ForeignInvestorDailyConfirmed
from app.services.foreign_investor_service import (
    get_recent_confirmed_foreign_aggregate,
    upsert_foreign_investor_daily_rows,
)


def test_upsert_foreign_investor_daily_is_idempotent(db_session):
    rows = [
        ForeignInvestorDailyConfirmed(
            stock_code='005930',
            trade_date=date(2026, 3, 18),
            net_buy_value=100,
            source='test_source',
            is_confirmed=True,
        )
    ]

    saved_first = upsert_foreign_investor_daily_rows(db_session, rows, commit=True)
    saved_second = upsert_foreign_investor_daily_rows(db_session, rows, commit=True)

    assert saved_first == 1
    assert saved_second == 1

    persisted = db_session.query(ForeignInvestorDaily).filter_by(stock_code='005930').all()
    assert len(persisted) == 1
    assert persisted[0].net_buy_value == 100


def test_recent_confirmed_aggregate_requires_enough_days(db_session):
    rows = [
        ForeignInvestorDailyConfirmed(
            stock_code='000660',
            trade_date=date(2026, 3, 18),
            net_buy_value=300,
            source='test_source',
            is_confirmed=True,
        )
    ]
    upsert_foreign_investor_daily_rows(db_session, rows, commit=True)

    aggregate, status, source = get_recent_confirmed_foreign_aggregate(db_session, '000660', days=3)

    assert aggregate is None
    assert status == 'unavailable'
    assert source == 'confirmed_daily_unavailable'


def test_recent_confirmed_aggregate_sums_latest_days(db_session):
    rows = [
        ForeignInvestorDailyConfirmed(
            stock_code='035420',
            trade_date=date(2026, 3, 17),
            net_buy_value=100,
            source='test_source',
            is_confirmed=True,
        ),
        ForeignInvestorDailyConfirmed(
            stock_code='035420',
            trade_date=date(2026, 3, 18),
            net_buy_value=-20,
            source='test_source',
            is_confirmed=True,
        ),
        ForeignInvestorDailyConfirmed(
            stock_code='035420',
            trade_date=date(2026, 3, 19),
            net_buy_value=300,
            source='test_source',
            is_confirmed=True,
        ),
    ]
    upsert_foreign_investor_daily_rows(db_session, rows, commit=True)

    aggregate, status, source = get_recent_confirmed_foreign_aggregate(db_session, '035420', days=2)

    assert aggregate == 280
    assert status == 'confirmed'
    assert source == 'confirmed_daily_db'
