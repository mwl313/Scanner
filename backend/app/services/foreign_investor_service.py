from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import threading

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models.foreign_investor_daily import ForeignInvestorDaily
from app.providers import (
    ForeignInvestorDailyConfirmed,
    ForeignInvestorIntradaySnapshot,
    MarketDataProvider,
    get_market_data_provider,
)
from app.services.confirmed_foreign_source import (
    ConfirmedForeignInvestorSource,
    resolve_confirmed_foreign_source,
)
from app.utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)


@dataclass
class ConfirmedForeignSyncOutcome:
    saved_rows: int
    fetched_rows: int
    attempted: bool
    unavailable_reason: str | None
    source_label: str | None = None


@dataclass
class ConfirmedForeignAggregateContext:
    aggregate_value: int | None
    status: str
    source: str
    coverage_days: int
    required_days: int
    unavailable_reason: str | None
    latest_row_source: str | None = None


_SYNC_BACKOFF_LOCK = threading.Lock()
_SYNC_BACKOFF_UNTIL: datetime | None = None
_SYNC_BACKOFF_REASON: str | None = None


def _activate_sync_backoff(reason: str) -> None:
    settings = get_settings()
    with _SYNC_BACKOFF_LOCK:
        global _SYNC_BACKOFF_UNTIL, _SYNC_BACKOFF_REASON
        _SYNC_BACKOFF_UNTIL = utcnow() + timedelta(seconds=max(int(settings.foreign_sync_backoff_seconds), 1))
        _SYNC_BACKOFF_REASON = reason


def _active_sync_backoff() -> tuple[str | None, int]:
    with _SYNC_BACKOFF_LOCK:
        global _SYNC_BACKOFF_UNTIL, _SYNC_BACKOFF_REASON
        if _SYNC_BACKOFF_UNTIL is None:
            return None, 0
        now = utcnow()
        if now >= _SYNC_BACKOFF_UNTIL:
            _SYNC_BACKOFF_UNTIL = None
            _SYNC_BACKOFF_REASON = None
            return None, 0
        remaining = max(int((_SYNC_BACKOFF_UNTIL - now).total_seconds()), 1)
        return _SYNC_BACKOFF_REASON or 'unknown', remaining


def _classify_sync_exception(exc: Exception) -> str:
    if isinstance(exc, AppError):
        code = (exc.code or '').lower()
        detail_blob = f'{exc.message} {exc.details}'.lower()
        if (
            'rate_limited' in code
            or 'cooldown' in code
            or 'egw00133' in detail_blob
            or ('1분당 1회' in str(exc.message))
        ):
            return 'token_rate_limited'
        if (
            'kis_' in code
            or code in {'provider_error', 'http_error', 'http_status_error', 'api_error'}
            or exc.status_code >= 500
        ):
            return 'provider_error'
        return 'unknown'
    return 'provider_error'


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


def sync_confirmed_foreign_for_stock_with_meta(
    db: Session,
    provider: MarketDataProvider,
    stock_code: str,
    start_date,
    end_date,
    *,
    confirmed_source: ConfirmedForeignInvestorSource | None = None,
    commit: bool = False,
) -> ConfirmedForeignSyncOutcome:
    backoff_reason, backoff_remaining = _active_sync_backoff()
    if backoff_reason:
        logger.info(
            'Skipping confirmed foreign sync for %s due to backoff (reason=%s, remaining=%ss)',
            stock_code,
            backoff_reason,
            backoff_remaining,
        )
        return ConfirmedForeignSyncOutcome(
            saved_rows=0,
            fetched_rows=0,
            attempted=False,
            unavailable_reason=backoff_reason,
            source_label='sync_backoff',
        )

    source = confirmed_source or resolve_confirmed_foreign_source(provider)
    try:
        rows = source.fetch_daily_confirmed(stock_code, start_date, end_date)
    except Exception as exc:
        reason = _classify_sync_exception(exc)
        if reason in {'token_rate_limited', 'provider_error'}:
            _activate_sync_backoff(reason)
        logger.warning('Failed to sync confirmed foreign investor rows for %s: %s (%s)', stock_code, exc, reason)
        return ConfirmedForeignSyncOutcome(
            saved_rows=0,
            fetched_rows=0,
            attempted=True,
            unavailable_reason=reason,
            source_label=source.__class__.__name__,
        )

    fetched_rows = len(rows)
    if fetched_rows == 0:
        return ConfirmedForeignSyncOutcome(
            saved_rows=0,
            fetched_rows=0,
            attempted=True,
            unavailable_reason='api_empty',
            source_label=source.__class__.__name__,
        )

    has_money_value = any(row.net_buy_value is not None for row in rows)
    if not has_money_value:
        return ConfirmedForeignSyncOutcome(
            saved_rows=0,
            fetched_rows=fetched_rows,
            attempted=True,
            unavailable_reason='parse_none',
            source_label=(rows[0].source if rows else source.__class__.__name__),
        )

    saved = upsert_foreign_investor_daily_rows(db, rows, commit=commit)
    return ConfirmedForeignSyncOutcome(
        saved_rows=saved,
        fetched_rows=fetched_rows,
        attempted=True,
        unavailable_reason=None,
        source_label=(rows[0].source if rows else source.__class__.__name__),
    )


def sync_confirmed_foreign_for_stock(
    db: Session,
    provider: MarketDataProvider,
    stock_code: str,
    start_date,
    end_date,
    *,
    confirmed_source: ConfirmedForeignInvestorSource | None = None,
    commit: bool = False,
) -> int:
    outcome = sync_confirmed_foreign_for_stock_with_meta(
        db,
        provider,
        stock_code,
        start_date,
        end_date,
        confirmed_source=confirmed_source,
        commit=commit,
    )
    return outcome.saved_rows


def get_recent_confirmed_foreign_context(
    db: Session,
    stock_code: str,
    days: int,
    *,
    min_required_days: int | None = None,
) -> ConfirmedForeignAggregateContext:
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
    coverage_days = len(rows)
    latest_row_source = str(rows[0].source) if rows else None
    if coverage_days < required_days:
        return ConfirmedForeignAggregateContext(
            aggregate_value=None,
            status='unavailable',
            source='confirmed_daily_unavailable',
            coverage_days=coverage_days,
            required_days=required_days,
            unavailable_reason='insufficient_days',
            latest_row_source=latest_row_source,
        )

    aggregate = int(sum(int(row.net_buy_value) for row in rows))
    return ConfirmedForeignAggregateContext(
        aggregate_value=aggregate,
        status='confirmed',
        source='confirmed_daily_db',
        coverage_days=coverage_days,
        required_days=required_days,
        unavailable_reason=None,
        latest_row_source=latest_row_source,
    )


def get_recent_confirmed_foreign_aggregate(
    db: Session,
    stock_code: str,
    days: int,
    *,
    min_required_days: int | None = None,
) -> tuple[int | None, str, str]:
    context = get_recent_confirmed_foreign_context(
        db,
        stock_code,
        days,
        min_required_days=min_required_days,
    )
    return context.aggregate_value, context.status, context.source


def get_foreign_investor_context(
    db: Session,
    provider: MarketDataProvider,
    stock_code: str,
    days: int,
    *,
    sync_if_missing: bool = False,
    confirmed_source: ConfirmedForeignInvestorSource | None = None,
) -> dict:
    snapshot_value: int | None = None
    snapshot_source = 'snapshot_unavailable'
    try:
        snapshot: ForeignInvestorIntradaySnapshot = provider.get_foreign_investor_intraday_snapshot(stock_code)
        snapshot_value = snapshot.net_buy_value
        snapshot_source = snapshot.source
    except Exception as exc:
        logger.warning('Failed to fetch intraday snapshot for %s: %s', stock_code, exc)

    aggregate_context = get_recent_confirmed_foreign_context(db, stock_code, days)
    sync_outcome: ConfirmedForeignSyncOutcome | None = None
    if aggregate_context.status != 'confirmed' and sync_if_missing:
        today = utcnow().date()
        sync_start = today - timedelta(days=max(days * 4, 14))
        sync_outcome = sync_confirmed_foreign_for_stock_with_meta(
            db,
            provider,
            stock_code,
            sync_start,
            today,
            confirmed_source=confirmed_source,
            commit=False,
        )
        if sync_outcome.saved_rows > 0:
            aggregate_context = get_recent_confirmed_foreign_context(db, stock_code, days)

    unavailable_reason: str | None = None
    if aggregate_context.status != 'confirmed':
        if sync_outcome and sync_outcome.unavailable_reason:
            unavailable_reason = sync_outcome.unavailable_reason
        else:
            unavailable_reason = aggregate_context.unavailable_reason or 'unknown'

    return {
        'confirmed_aggregate_value': aggregate_context.aggregate_value,
        'snapshot_value': snapshot_value,
        'status': aggregate_context.status,
        'source': aggregate_context.source,
        'confirmed_row_source': aggregate_context.latest_row_source,
        'snapshot_source': snapshot_source,
        'unavailable_reason': unavailable_reason,
        'coverage_days': aggregate_context.coverage_days,
        'required_days': aggregate_context.required_days,
    }


def sync_confirmed_foreign_for_codes(
    db: Session,
    provider: MarketDataProvider,
    stock_codes: list[str],
    *,
    lookback_days: int,
    required_days: int | None = None,
    commit: bool = False,
) -> tuple[int, int, int]:
    unique_codes = list(dict.fromkeys(stock_codes))
    if not unique_codes:
        return 0, 0, 0

    confirmed_source = resolve_confirmed_foreign_source(provider)
    today = utcnow().date()
    start_date = today - timedelta(days=max(lookback_days, 1))

    scanned = 0
    saved = 0
    skipped = 0
    for code in unique_codes:
        if required_days and required_days > 0:
            coverage = get_recent_confirmed_foreign_context(
                db,
                code,
                days=required_days,
                min_required_days=required_days,
            )
            if coverage.status == 'confirmed':
                skipped += 1
                continue
        scanned += 1
        outcome = sync_confirmed_foreign_for_stock_with_meta(
            db,
            provider,
            code,
            start_date,
            today,
            confirmed_source=confirmed_source,
            commit=False,
        )
        saved += outcome.saved_rows

    if saved > 0 and commit:
        db.commit()
    elif saved > 0:
        db.flush()

    return scanned, saved, skipped


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

    scanned, saved, _skipped = sync_confirmed_foreign_for_codes(
        db,
        provider,
        [stock.code for stock in stocks],
        lookback_days=lookback_days,
        required_days=None,
        commit=True,
    )
    return scanned, saved
