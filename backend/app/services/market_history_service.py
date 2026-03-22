from __future__ import annotations

from datetime import date, timedelta
import logging

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.stock_daily_bar import StockDailyBar
from app.providers.base import DailyBar, MarketDataProvider
from app.services.foreign_investor_service import (
    ConfirmedForeignAggregateContext,
    get_recent_confirmed_foreign_context,
    sync_confirmed_foreign_for_stock_with_meta,
)
from app.utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)


def list_stock_daily_bar_rows(
    db: Session,
    stock_code: str,
    *,
    limit: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    descending: bool = False,
) -> list[StockDailyBar]:
    stmt = select(StockDailyBar).where(StockDailyBar.stock_code == stock_code)

    if start_date:
        stmt = stmt.where(StockDailyBar.trade_date >= start_date)
    if end_date:
        stmt = stmt.where(StockDailyBar.trade_date <= end_date)

    order_col = desc(StockDailyBar.trade_date) if descending else StockDailyBar.trade_date
    stmt = stmt.order_by(order_col)

    if limit is not None and limit > 0:
        stmt = stmt.limit(limit)

    return list(db.scalars(stmt).all())


def _rows_to_daily_bars(rows: list[StockDailyBar]) -> list[DailyBar]:
    return [
        DailyBar(
            trade_date=row.trade_date,
            open_price=float(row.open_price),
            high_price=float(row.high_price),
            low_price=float(row.low_price),
            close_price=float(row.close_price),
            volume=int(row.volume),
            trading_value=int(row.trading_value),
        )
        for row in rows
    ]


def get_cached_daily_bars(db: Session, stock_code: str, days: int) -> list[DailyBar]:
    target_days = max(int(days), 1)
    rows_desc = list_stock_daily_bar_rows(db, stock_code, limit=target_days, descending=True)
    rows = list(reversed(rows_desc))
    return _rows_to_daily_bars(rows)


def upsert_stock_daily_bars(
    db: Session,
    stock_code: str,
    bars: list[DailyBar],
    *,
    source: str,
    is_confirmed: bool = True,
    commit: bool = False,
) -> int:
    if not bars:
        return 0

    trade_dates = [bar.trade_date for bar in bars]
    existing_rows = list(
        db.scalars(
            select(StockDailyBar).where(
                and_(
                    StockDailyBar.stock_code == stock_code,
                    StockDailyBar.trade_date.in_(trade_dates),
                )
            )
        ).all()
    )
    existing_by_date = {row.trade_date: row for row in existing_rows}

    saved = 0
    for bar in bars:
        existing = existing_by_date.get(bar.trade_date)
        if existing:
            existing.open_price = float(bar.open_price)
            existing.high_price = float(bar.high_price)
            existing.low_price = float(bar.low_price)
            existing.close_price = float(bar.close_price)
            existing.volume = int(bar.volume)
            existing.trading_value = int(bar.trading_value)
            existing.source = source
            existing.is_confirmed = bool(is_confirmed)
            db.add(existing)
        else:
            db.add(
                StockDailyBar(
                    stock_code=stock_code,
                    trade_date=bar.trade_date,
                    open_price=float(bar.open_price),
                    high_price=float(bar.high_price),
                    low_price=float(bar.low_price),
                    close_price=float(bar.close_price),
                    volume=int(bar.volume),
                    trading_value=int(bar.trading_value),
                    source=source,
                    is_confirmed=bool(is_confirmed),
                )
            )
        saved += 1

    if saved > 0 and commit:
        db.commit()
    elif saved > 0:
        db.flush()
    return saved


def _default_fetch_days(required_days: int) -> int:
    # Include weekend/holiday buffer while keeping request size bounded.
    return min(max(required_days * 2, required_days + 30, 120), 720)


def ensure_daily_bars_cached(
    db: Session,
    provider: MarketDataProvider,
    stock_code: str,
    required_days: int,
    *,
    fetch_buffer_days: int | None = None,
    source_label: str | None = None,
    max_fetch_days: int = 720,
    commit: bool = False,
) -> list[DailyBar]:
    target_days = max(int(required_days), 1)
    cached = get_cached_daily_bars(db, stock_code, target_days)
    if len(cached) >= target_days:
        logger.debug('Daily bar cache hit stock=%s days=%s', stock_code, target_days)
        return cached

    provider_source = source_label or f'{provider.__class__.__name__}:daily_bars'
    fetch_days = min(
        max_fetch_days,
        max(int(fetch_buffer_days or _default_fetch_days(target_days)), target_days),
    )

    logger.debug(
        'Daily bar cache miss stock=%s required=%s cached=%s fetch_days=%s',
        stock_code,
        target_days,
        len(cached),
        fetch_days,
    )

    attempts = 0
    while len(cached) < target_days and attempts < 3:
        fetched = provider.get_daily_bars(stock_code, fetch_days)
        if fetched:
            upsert_stock_daily_bars(
                db,
                stock_code,
                fetched,
                source=provider_source,
                is_confirmed=True,
                commit=commit,
            )
        cached = get_cached_daily_bars(db, stock_code, target_days)
        if len(cached) >= target_days or fetch_days >= max_fetch_days:
            break
        fetch_days = min(max_fetch_days, int(fetch_days * 1.7))
        attempts += 1

    if len(cached) < target_days:
        raise AppError(
            code='daily_bars_insufficient',
            message='Not enough daily bars after cache backfill',
            status_code=502,
            details={
                'stock_code': stock_code,
                'required_days': target_days,
                'cached_days': len(cached),
            },
        )
    return cached


def ensure_foreign_daily_cached(
    db: Session,
    provider: MarketDataProvider,
    stock_code: str,
    required_days: int,
    *,
    lookback_days: int | None = None,
    sync_if_missing: bool = True,
) -> ConfirmedForeignAggregateContext:
    target_days = max(int(required_days), 1)
    context = get_recent_confirmed_foreign_context(
        db,
        stock_code,
        days=target_days,
        min_required_days=target_days,
    )
    if context.status == 'confirmed' or not sync_if_missing:
        return context

    today = utcnow().date()
    start_date = today - timedelta(days=max(int(lookback_days or target_days * 4), target_days))
    sync_confirmed_foreign_for_stock_with_meta(
        db,
        provider,
        stock_code,
        start_date,
        today,
        commit=False,
    )
    return get_recent_confirmed_foreign_context(
        db,
        stock_code,
        days=target_days,
        min_required_days=target_days,
    )
