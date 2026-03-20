from collections.abc import Iterable
import logging
import math

from sqlalchemy import Select, and_, desc, select
from sqlalchemy.orm import Session

from app.core.scoring import (
    BOLLINGER_LOWER_PROXIMITY,
    GRADE_THRESHOLDS,
    PRICE_NEAR_MA20_TOLERANCE,
    SCORE_WEIGHTS,
)
from app.models.scan_result import ScanResult
from app.models.scan_run import ScanRun
from app.models.strategy import Strategy
from app.models.user import User
from app.models.watchlist_item import WatchlistItem
from app.providers import DailyBar, StockMeta, get_market_data_provider
from app.services.foreign_investor_service import (
    get_foreign_investor_context,
    sync_confirmed_foreign_for_market,
)
from app.utils.datetime_utils import utcnow
from app.utils.indicators import bollinger, is_nan, rsi, sma

logger = logging.getLogger(__name__)



def _safe_last(values: list[float], offset: int = 1) -> float:
    if len(values) < offset:
        return math.nan
    return values[-offset]



def _grade_from_score(score: int, mandatory_ok: bool) -> str:
    if not mandatory_ok:
        return 'EXCLUDED'
    if score >= GRADE_THRESHOLDS['A']:
        return 'A'
    if score >= GRADE_THRESHOLDS['B']:
        return 'B'
    if score >= GRADE_THRESHOLDS['C']:
        return 'C'
    return 'EXCLUDED'



def _evaluate_stock(strategy: Strategy, stock: StockMeta, bars: list[DailyBar], foreign_data: dict) -> dict:
    closes = [float(item.close_price) for item in bars]
    latest_price = closes[-1]
    latest_trading_value = int(bars[-1].trading_value)

    ma5_series = sma(closes, 5)
    ma20_series = sma(closes, 20)
    ma60_series = sma(closes, 60)
    bb_upper_series, bb_mid_series, bb_lower_series = bollinger(closes, strategy.bb_period, strategy.bb_std)

    rsi_series = rsi(closes, strategy.rsi_period)
    valid_rsi = [value for value in rsi_series if not is_nan(value)]
    if len(valid_rsi) < strategy.rsi_signal_period + 3:
        raise ValueError('Insufficient RSI history for signal calculation')

    rsi_signal_series = sma(valid_rsi, strategy.rsi_signal_period)

    current_rsi = float(valid_rsi[-1])
    prev_rsi = float(valid_rsi[-2])
    prev2_rsi = float(valid_rsi[-3])

    current_signal = float(rsi_signal_series[-1])
    prev_signal = float(rsi_signal_series[-2])
    prev2_signal = float(rsi_signal_series[-3])

    ma5 = float(_safe_last(ma5_series))
    ma20 = float(_safe_last(ma20_series))
    ma60 = float(_safe_last(ma60_series))
    bb_upper = float(_safe_last(bb_upper_series))
    bb_mid = float(_safe_last(bb_mid_series))
    bb_lower = float(_safe_last(bb_lower_series))

    if any(is_nan(v) for v in [ma5, ma20, ma60, bb_upper, bb_mid, bb_lower]):
        raise ValueError('Insufficient history for MA/Bollinger calculation')

    rsi_cross_up = prev_rsi <= prev_signal and current_rsi > current_signal
    rsi_cross_recent = prev2_rsi <= prev2_signal and prev_rsi > prev_signal and current_rsi >= current_signal
    rsi_cross_ok = rsi_cross_up or rsi_cross_recent

    rsi_in_range = strategy.rsi_min <= current_rsi <= strategy.rsi_max

    bb_distance_ratio = abs(latest_price - bb_lower) / bb_lower if bb_lower > 0 else 999
    bb_lower_near = bb_distance_ratio <= BOLLINGER_LOWER_PROXIMITY

    price_above_ma20 = latest_price >= ma20
    price_near_ma20 = price_above_ma20 or ((ma20 - latest_price) / ma20 <= PRICE_NEAR_MA20_TOLERANCE)

    ma5_above_ma20 = ma5 >= ma20

    foreign_confirmed_value = foreign_data.get('confirmed_aggregate_value')
    foreign_snapshot_value = foreign_data.get('snapshot_value')
    foreign_status = str(foreign_data.get('status') or 'unavailable')
    foreign_source = str(foreign_data.get('source') or 'unknown')
    foreign_snapshot_source = str(foreign_data.get('snapshot_source') or 'unknown')
    foreign_net_buy_positive = (foreign_confirmed_value is not None) and (foreign_confirmed_value > 0)

    trading_value_pass = latest_trading_value >= strategy.min_trading_value
    market_cap_pass = stock.market_cap >= strategy.min_market_cap
    market_pass = stock.market.upper() == strategy.market.upper()

    matched: list[str] = []
    failed: list[str] = []

    score = 0

    if rsi_cross_ok:
        score += SCORE_WEIGHTS['rsi_crossover']
        matched.append('RSI(14) vs RSI signal 상향 돌파 확인')
    else:
        failed.append('RSI 상향 돌파 조건 미충족')

    if rsi_in_range:
        score += SCORE_WEIGHTS['rsi_target_range']
        matched.append(f'RSI가 목표 구간({strategy.rsi_min}~{strategy.rsi_max})에 위치')
    else:
        failed.append('RSI 목표 구간 미충족')

    if bb_lower_near:
        score += SCORE_WEIGHTS['bollinger_lower_proximity']
        matched.append('볼린저 하단 근접 구간')
    else:
        failed.append('볼린저 하단 근접 조건 미충족')

    if price_above_ma20:
        score += SCORE_WEIGHTS['price_above_ma20']
        matched.append('가격이 MA20 위')
    elif price_near_ma20:
        matched.append('가격이 MA20 근처에서 유지')
    else:
        failed.append('MA20 기준 과도한 이탈')

    if strategy.use_ma5_filter:
        if ma5_above_ma20:
            score += SCORE_WEIGHTS['ma5_above_ma20']
            matched.append('MA5가 MA20 위')
        else:
            failed.append('MA5 > MA20 미충족')

    if foreign_confirmed_value is None:
        matched.append('외인 확정 데이터 없음(중립 처리)')
    elif foreign_net_buy_positive:
        score += SCORE_WEIGHTS['foreign_net_buy']
        matched.append(f'외국인 최근 {strategy.foreign_net_buy_days}일 확정 순매수 우위')
    else:
        failed.append('외국인 확정 순매수 조건 미충족')

    if trading_value_pass:
        score += SCORE_WEIGHTS['trading_value_pass']
        matched.append('거래대금 기준 통과')
    else:
        failed.append('거래대금 기준 미달')

    mandatory_ok = all(
        [
            market_pass,
            market_cap_pass,
            trading_value_pass,
            rsi_cross_ok,
            (price_near_ma20 if strategy.use_ma20_filter else True),
        ]
    )

    if not market_pass:
        failed.append('시장 필터 미충족')
    if not market_cap_pass:
        failed.append('시가총액 조건 미충족')

    grade = _grade_from_score(score, mandatory_ok)

    return {
        'stock_code': stock.code,
        'stock_name': stock.name,
        'market': stock.market,
        'price': latest_price,
        'ma5': ma5,
        'ma20': ma20,
        'ma60': ma60,
        'bb_upper': bb_upper,
        'bb_mid': bb_mid,
        'bb_lower': bb_lower,
        'rsi': current_rsi,
        'rsi_signal': current_signal,
        'foreign_net_buy_value': int(foreign_confirmed_value or 0),
        'foreign_net_buy_confirmed_value': (int(foreign_confirmed_value) if foreign_confirmed_value is not None else None),
        'foreign_net_buy_snapshot_value': (int(foreign_snapshot_value) if foreign_snapshot_value is not None else None),
        'foreign_data_status': foreign_status,
        'foreign_data_source': f'{foreign_source}|{foreign_snapshot_source}',
        'trading_value': latest_trading_value,
        'score': int(score),
        'grade': grade,
        'matched_reasons_json': matched,
        'failed_reasons_json': failed,
    }



def run_scan(db: Session, strategy: Strategy, run_type: str = 'manual') -> ScanRun:
    provider = get_market_data_provider()

    run = ScanRun(
        strategy_id=strategy.id,
        run_type=run_type,
        started_at=utcnow(),
        status='running',
        total_scanned=0,
        total_matched=0,
        failed_count=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        stocks = provider.list_stocks(strategy.market)
        for stock in stocks:
            run.total_scanned += 1
            try:
                bars = provider.get_daily_bars(stock.code, max(120, strategy.bb_period + 60, strategy.rsi_period + 30))
                foreign_data = get_foreign_investor_context(
                    db,
                    provider,
                    stock.code,
                    strategy.foreign_net_buy_days,
                )
                evaluated = _evaluate_stock(strategy, stock, bars, foreign_data)

                result = ScanResult(scan_run_id=run.id, strategy_id=strategy.id, **evaluated)
                db.add(result)

                if result.grade != 'EXCLUDED':
                    run.total_matched += 1
            except Exception as exc:
                run.failed_count += 1
                logger.exception('Failed to scan %s (%s): %s', stock.code, stock.name, exc)

        run.status = 'partial_failed' if run.failed_count > 0 else 'completed'
        run.finished_at = utcnow()
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    except Exception:
        run.status = 'failed'
        run.finished_at = utcnow()
        db.add(run)
        db.commit()
        raise



def list_scan_runs(db: Session, user: User) -> list[ScanRun]:
    stmt = (
        select(ScanRun)
        .join(Strategy, Strategy.id == ScanRun.strategy_id)
        .where(Strategy.user_id == user.id)
        .order_by(desc(ScanRun.started_at))
    )
    return list(db.scalars(stmt).all())



def get_scan_run_or_404(db: Session, user: User, run_id: int) -> ScanRun:
    stmt = select(ScanRun).join(Strategy).where(and_(ScanRun.id == run_id, Strategy.user_id == user.id))
    run = db.scalar(stmt)
    if not run:
        raise ValueError('Scan run not found')
    return run



def _apply_sort(stmt: Select[tuple[ScanResult]], sort_by: str, sort_order: str) -> Select[tuple[ScanResult]]:
    mapping = {
        'score': ScanResult.score,
        'trading_value': ScanResult.trading_value,
        'rsi': ScanResult.rsi,
        'foreign_net_buy': ScanResult.foreign_net_buy_value,
        'created_at': ScanResult.created_at,
    }
    target = mapping.get(sort_by, ScanResult.score)
    return stmt.order_by(target.desc() if sort_order == 'desc' else target.asc())



def list_scan_results(
    db: Session,
    user: User,
    run_id: int,
    grade: str | None,
    sort_by: str,
    sort_order: str,
    watchlist_only: bool,
) -> list[ScanResult]:
    _ = get_scan_run_or_404(db, user, run_id)

    stmt = (
        select(ScanResult)
        .join(Strategy, Strategy.id == ScanResult.strategy_id)
        .where(and_(ScanResult.scan_run_id == run_id, Strategy.user_id == user.id))
    )

    if grade:
        normalized_grade = grade.upper()
        if normalized_grade == 'AB':
            stmt = stmt.where(ScanResult.grade.in_(['A', 'B']))
        else:
            stmt = stmt.where(ScanResult.grade == normalized_grade)

    if watchlist_only:
        stmt = stmt.join(
            WatchlistItem,
            and_(
                WatchlistItem.stock_code == ScanResult.stock_code,
                WatchlistItem.user_id == user.id,
            ),
        )

    stmt = _apply_sort(stmt, sort_by, sort_order)
    return list(db.scalars(stmt).all())



def get_latest_stock_result(db: Session, user: User, stock_code: str) -> ScanResult | None:
    stmt = (
        select(ScanResult)
        .join(Strategy, Strategy.id == ScanResult.strategy_id)
        .where(and_(Strategy.user_id == user.id, ScanResult.stock_code == stock_code))
        .order_by(ScanResult.created_at.desc())
    )
    return db.scalar(stmt)



def run_scheduled_scans(db: Session) -> None:
    try:
        scanned, saved = sync_confirmed_foreign_for_market(db, market='KOSPI', lookback_days=10)
        logger.info('Confirmed foreign investor sync finished before EOD scan (stocks=%s, rows=%s)', scanned, saved)
    except Exception as exc:
        logger.exception('Confirmed foreign investor sync failed before EOD scan: %s', exc)

    strategies: Iterable[Strategy] = db.scalars(
        select(Strategy).where(Strategy.is_active.is_(True), Strategy.scan_interval_type == 'eod')
    ).all()
    for strategy in strategies:
        try:
            run_scan(db, strategy, run_type='scheduled')
        except Exception as exc:
            logger.exception('Scheduled scan failed for strategy=%s: %s', strategy.id, exc)
