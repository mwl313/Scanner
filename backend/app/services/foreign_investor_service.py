from __future__ import annotations

from datetime import timedelta
import logging

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.models.foreign_investor_daily import ForeignInvestorDaily
from app.providers import (
    ForeignInvestorDailyConfirmed,
    ForeignInvestorIntradaySnapshot,
    MarketDataProvider,
    get_market_data_provider,
)
from app.utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)


def upsert_foreign_investor_daily_rows(
    db: Session,
    rows: list[ForeignInvestorDailyConfirmed],
    *,
    commit: bool = False,
) -> int:
    saved = 0
    for row in rows:
        if row.net_buy_value is None:
            continue
        existing = db.scalar(
            select(ForeignInvestorDaily).where(
                and_(
                    ForeignInvestorDaily.stock_code == row.stock_code,
                    ForeignInvestorDaily.trade_date == row.trade_date,
                )
            )
        )
        if existing:
            existing.net_buy_value = int(row.net_buy_value)
            existing.source = row.source
            existing.is_confirmed = bool(row.is_confirmed)
            db.add(existing)
        else:
            db.add(
                ForeignInvestorDaily(
                    stock_code=row.stock_code,
                    trade_date=row.trade_date,
                    net_buy_value=int(row.net_buy_value),
                    source=row.source,
                    is_confirmed=bool(row.is_confirmed),
                )
            )
        saved += 1
    if saved > 0 and commit:
        db.commit()
    elif saved > 0:
        db.flush()
    return saved


def sync_confirmed_foreign_for_stock(
    db: Session,
    provider: MarketDataProvider,
    stock_code: str,
    start_date,
    end_date,
    *,
    commit: bool = False,
) -> int:
    try:
        rows = provider.get_foreign_investor_daily_confirmed(stock_code, start_date, end_date)
    except Exception as exc:
        logger.warning('Failed to sync confirmed foreign investor rows for %s: %s', stock_code, exc)
        return 0
    return upsert_foreign_investor_daily_rows(db, rows, commit=commit)


def get_recent_confirmed_foreign_aggregate(
    db: Session,
    stock_code: str,
    days: int,
    *,
    min_required_days: int | None = None,
) -> tuple[int | None, str, str]:
    target_days = max(days, 1)
    required_days = min_required_days or target_days

    rows = list(
        db.scalars(
            select(ForeignInvestorDaily)
            .where(ForeignInvestorDaily.stock_code == stock_code, ForeignInvestorDaily.is_confirmed.is_(True))
            .order_by(desc(ForeignInvestorDaily.trade_date))
            .limit(target_days)
        ).all()
    )
    if len(rows) < required_days:
        return None, 'unavailable', 'confirmed_daily_unavailable'

    aggregate = int(sum(int(row.net_buy_value) for row in rows))
    return aggregate, 'confirmed', 'confirmed_daily_db'


def get_foreign_investor_context(
    db: Session,
    provider: MarketDataProvider,
    stock_code: str,
    days: int,
) -> dict:
    snapshot_value: int | None = None
    snapshot_source = 'snapshot_unavailable'
    try:
        snapshot: ForeignInvestorIntradaySnapshot = provider.get_foreign_investor_intraday_snapshot(stock_code)
        snapshot_value = snapshot.net_buy_value
        snapshot_source = snapshot.source
    except Exception as exc:
        logger.warning('Failed to fetch intraday snapshot for %s: %s', stock_code, exc)

    today = utcnow().date()
    sync_start = today - timedelta(days=max(days * 4, 14))
    sync_confirmed_foreign_for_stock(db, provider, stock_code, sync_start, today, commit=False)

    confirmed_value, status, source = get_recent_confirmed_foreign_aggregate(db, stock_code, days)

    return {
        'confirmed_aggregate_value': confirmed_value,
        'snapshot_value': snapshot_value,
        'status': status,
        'source': source,
        'snapshot_source': snapshot_source,
    }


def sync_confirmed_foreign_for_market(
    db: Session,
    market: str,
    lookback_days: int = 10,
    stock_limit: int | None = None,
) -> tuple[int, int]:
    provider = get_market_data_provider()
    stocks = provider.list_stocks(market)
    if stock_limit is not None and stock_limit > 0:
        stocks = stocks[:stock_limit]

    today = utcnow().date()
    start_date = today - timedelta(days=max(lookback_days, 1))

    scanned = 0
    saved = 0
    for stock in stocks:
        scanned += 1
        saved += sync_confirmed_foreign_for_stock(db, provider, stock.code, start_date, today, commit=True)
    return scanned, saved
