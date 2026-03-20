from collections.abc import Iterable
import logging
import math

from sqlalchemy import Select, and_, desc, select
from sqlalchemy.orm import Session

from app.core.scoring import GRADE_THRESHOLDS
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
from app.services.strategy_schema_service import normalize_strategy_config
from app.utils.datetime_utils import utcnow
from app.utils.indicators import bollinger, is_nan, rsi, sma

logger = logging.getLogger(__name__)



def _safe_last(values: list[float], offset: int = 1) -> float:
    if len(values) < offset:
        return math.nan
    return values[-offset]


def _rsi_cross_within_lookback(rsi_values: list[float], signal_values: list[float], lookback_bars: int) -> bool:
    if len(rsi_values) < 2 or len(signal_values) < 2:
        return False

    max_lookback = max(int(lookback_bars), 0)
    last_idx = len(rsi_values) - 1

    for bars_ago in range(0, max_lookback + 1):
        idx = last_idx - bars_ago
        if idx <= 0:
            break
        crossed = rsi_values[idx - 1] <= signal_values[idx - 1] and rsi_values[idx] > signal_values[idx]
        if crossed and all(rsi_values[j] >= signal_values[j] for j in range(idx, last_idx + 1)):
            return True
    return False



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



def _evaluate_stock(strategy: Strategy, strategy_config: dict, stock: StockMeta, bars: list[DailyBar], foreign_data: dict) -> dict:
    closes = [float(item.close_price) for item in bars]
    latest_price = closes[-1]
    latest_trading_value = int(bars[-1].trading_value)

    categories = strategy_config['categories']
    target_market = str(strategy_config.get('market') or strategy.market or 'KOSPI').upper()
    rsi_cfg = categories['rsi']
    bb_cfg = categories['bollinger']
    ma_cfg = categories['ma']
    foreign_cfg = categories['foreign']
    market_cap_cfg = categories['market_cap']
    trading_value_cfg = categories['trading_value']

    ma5_series = sma(closes, 5)
    ma20_series = sma(closes, 20)
    ma60_series = sma(closes, 60)
    bb_upper_series, bb_mid_series, bb_lower_series = bollinger(
        closes,
        int(bb_cfg['period']),
        float(bb_cfg['std']),
    )

    rsi_series = rsi(closes, int(rsi_cfg['period']))
    valid_rsi = [value for value in rsi_series if not is_nan(value)]
    if len(valid_rsi) < int(rsi_cfg['signal_period']) + int(rsi_cfg['cross_lookback_bars']) + 2:
        raise ValueError('Insufficient RSI history for signal calculation')

    rsi_signal_series = sma(valid_rsi, int(rsi_cfg['signal_period']))
    rsi_with_signal = [(r, s) for r, s in zip(valid_rsi, rsi_signal_series, strict=False) if not is_nan(s)]
    if len(rsi_with_signal) < int(rsi_cfg['cross_lookback_bars']) + 2:
        raise ValueError('Insufficient RSI signal pairs for crossover evaluation')
    rsi_values = [pair[0] for pair in rsi_with_signal]
    signal_values = [pair[1] for pair in rsi_with_signal]

    current_rsi = float(rsi_values[-1])
    current_signal = float(signal_values[-1])

    ma5 = float(_safe_last(ma5_series))
    ma20 = float(_safe_last(ma20_series))
    ma60 = float(_safe_last(ma60_series))
    bb_upper = float(_safe_last(bb_upper_series))
    bb_mid = float(_safe_last(bb_mid_series))
    bb_lower = float(_safe_last(bb_lower_series))

    if any(is_nan(v) for v in [ma5, ma20, ma60, bb_upper, bb_mid, bb_lower]):
        raise ValueError('Insufficient history for MA/Bollinger calculation')

    rsi_cross_ok = _rsi_cross_within_lookback(
        rsi_values,
        signal_values,
        int(rsi_cfg['cross_lookback_bars']),
    )

    rsi_in_range = float(rsi_cfg['min']) <= current_rsi <= float(rsi_cfg['max'])

    bb_distance_ratio = abs(latest_price - bb_lower) / bb_lower if bb_lower > 0 else 999
    bb_lower_near = bb_distance_ratio <= float(bb_cfg['lower_proximity_pct'])

    price_vs_ma20_cfg = ma_cfg['price_vs_ma20']
    ma5_vs_ma20_cfg = ma_cfg['ma5_vs_ma20']
    ma20_vs_ma60_cfg = ma_cfg['ma20_vs_ma60']

    price_above_ma20 = latest_price >= ma20 if ma20 > 0 else False
    price_vs_ma20_mode = str(price_vs_ma20_cfg['mode'])
    price_vs_ma20_tolerance = float(price_vs_ma20_cfg.get('tolerance_pct', 0.02))
    if price_vs_ma20_mode == 'above_only':
        price_vs_ma20_ok = price_above_ma20
    else:
        price_vs_ma20_ok = price_above_ma20 or (ma20 > 0 and ((ma20 - latest_price) / ma20 <= price_vs_ma20_tolerance))

    ma5_vs_ma20_mode = str(ma5_vs_ma20_cfg['mode'])
    if ma5_vs_ma20_mode == 'ma5_above_ma20':
        ma5_vs_ma20_ok = ma5 > ma20
    else:
        ma5_vs_ma20_ok = ma5 >= ma20

    ma20_vs_ma60_mode = str(ma20_vs_ma60_cfg['mode'])
    if ma20_vs_ma60_mode == 'ma20_above_ma60':
        ma20_vs_ma60_ok = ma20 > ma60
    else:
        ma20_vs_ma60_ok = ma20 >= ma60

    foreign_confirmed_value = foreign_data.get('confirmed_aggregate_value')
    foreign_snapshot_value = foreign_data.get('snapshot_value')
    foreign_status = str(foreign_data.get('status') or 'unavailable')
    foreign_source = str(foreign_data.get('source') or 'unknown')
    foreign_confirmed_row_source = foreign_data.get('confirmed_row_source')
    foreign_snapshot_source = str(foreign_data.get('snapshot_source') or 'unknown')
    confirmed_source_label = str(foreign_confirmed_row_source or foreign_source)
    foreign_net_buy_positive = (foreign_confirmed_value is not None) and (foreign_confirmed_value > 0)

    trading_value_pass = latest_trading_value >= int(trading_value_cfg['min_trading_value'])
    market_cap_pass = stock.market_cap >= int(market_cap_cfg['min_market_cap'])
    market_pass = stock.market.upper() == target_market

    matched: list[str] = []
    failed: list[str] = []

    total_enabled_weight = 0.0
    matched_weight = 0.0
    mandatory_ok = True

    def apply_condition(
        *,
        enabled: bool,
        mandatory: bool,
        weight: float,
        passed: bool,
        success_reason: str,
        fail_reason: str,
        neutral: bool = False,
    ) -> None:
        nonlocal total_enabled_weight, matched_weight, mandatory_ok
        if not enabled:
            return

        if neutral:
            matched.append(success_reason)
            return

        normalized_weight = max(float(weight), 0.0)
        total_enabled_weight += normalized_weight

        if passed:
            matched_weight += normalized_weight
            matched.append(success_reason)
            return

        failed.append(fail_reason)
        if mandatory:
            mandatory_ok = False

    rsi_pass = rsi_cross_ok and rsi_in_range
    apply_condition(
        enabled=bool(rsi_cfg['enabled']),
        mandatory=bool(rsi_cfg['mandatory']),
        weight=float(rsi_cfg['weight']),
        passed=rsi_pass,
        success_reason=f"RSI 상향 돌파 + 목표구간({rsi_cfg['min']}~{rsi_cfg['max']}) 충족",
        fail_reason='RSI 조건 미충족',
    )

    apply_condition(
        enabled=bool(bb_cfg['enabled']),
        mandatory=bool(bb_cfg['mandatory']),
        weight=float(bb_cfg['weight']),
        passed=bb_lower_near,
        success_reason='볼린저 하단 근접',
        fail_reason='볼린저 하단 근접 미충족',
    )

    apply_condition(
        enabled=bool(price_vs_ma20_cfg['enabled']),
        mandatory=bool(price_vs_ma20_cfg['mandatory']),
        weight=float(price_vs_ma20_cfg['weight']),
        passed=price_vs_ma20_ok,
        success_reason='가격 vs MA20 충족',
        fail_reason='가격 vs MA20 미충족',
    )

    apply_condition(
        enabled=bool(ma5_vs_ma20_cfg['enabled']),
        mandatory=bool(ma5_vs_ma20_cfg['mandatory']),
        weight=float(ma5_vs_ma20_cfg['weight']),
        passed=ma5_vs_ma20_ok,
        success_reason='MA5 vs MA20 충족',
        fail_reason='MA5 vs MA20 미충족',
    )

    apply_condition(
        enabled=bool(ma20_vs_ma60_cfg['enabled']),
        mandatory=bool(ma20_vs_ma60_cfg['mandatory']),
        weight=float(ma20_vs_ma60_cfg['weight']),
        passed=ma20_vs_ma60_ok,
        success_reason='MA20 vs MA60 충족',
        fail_reason='MA20 vs MA60 미충족',
    )

    foreign_enabled = bool(foreign_cfg['enabled'])
    foreign_mandatory = bool(foreign_cfg['mandatory'])
    foreign_weight = float(foreign_cfg['weight'])
    foreign_policy = str(foreign_cfg.get('unavailable_policy', 'neutral'))

    if foreign_enabled:
        if foreign_confirmed_value is None:
            if foreign_policy == 'neutral':
                apply_condition(
                    enabled=True,
                    mandatory=False,
                    weight=foreign_weight,
                    passed=False,
                    neutral=True,
                    success_reason='외인 확정 데이터 없음(중립 처리)',
                    fail_reason='',
                )
            elif foreign_policy == 'pass':
                apply_condition(
                    enabled=True,
                    mandatory=foreign_mandatory,
                    weight=foreign_weight,
                    passed=True,
                    success_reason='외인 데이터 미확보지만 정책상 통과',
                    fail_reason='',
                )
            else:
                apply_condition(
                    enabled=True,
                    mandatory=foreign_mandatory,
                    weight=foreign_weight,
                    passed=False,
                    success_reason='',
                    fail_reason='외인 데이터 미확보(실패 정책)',
                )
        else:
            apply_condition(
                enabled=True,
                mandatory=foreign_mandatory,
                weight=foreign_weight,
                passed=foreign_net_buy_positive,
                success_reason=f"외국인 최근 {foreign_cfg['days']}일 확정 순매수 우위",
                fail_reason='외국인 확정 순매수 조건 미충족',
            )

    apply_condition(
        enabled=bool(market_cap_cfg['enabled']),
        mandatory=bool(market_cap_cfg['mandatory']),
        weight=float(market_cap_cfg['weight']),
        passed=market_cap_pass,
        success_reason='시가총액 기준 통과',
        fail_reason='시가총액 조건 미충족',
    )

    apply_condition(
        enabled=bool(trading_value_cfg['enabled']),
        mandatory=bool(trading_value_cfg['mandatory']),
        weight=float(trading_value_cfg['weight']),
        passed=trading_value_pass,
        success_reason='거래대금 기준 통과',
        fail_reason='거래대금 기준 미달',
    )

    if not market_pass:
        mandatory_ok = False
        failed.append('시장 필터 미충족(KOSPI only)')

    score = int(round((matched_weight / total_enabled_weight) * 100)) if total_enabled_weight > 0 else 0

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
        'foreign_data_source': f'confirmed:{confirmed_source_label}|snapshot:{foreign_snapshot_source}',
        'trading_value': latest_trading_value,
        'score': score,
        'grade': grade,
        'matched_reasons_json': matched,
        'failed_reasons_json': failed,
    }



def run_scan(db: Session, strategy: Strategy, run_type: str = 'manual') -> ScanRun:
    provider = get_market_data_provider()
    strategy_config = normalize_strategy_config(strategy.strategy_config, legacy_source=strategy)
    target_market = str(strategy_config.get('market') or strategy.market or 'KOSPI').upper()
    categories = strategy_config['categories']
    rsi_cfg = categories['rsi']
    bb_cfg = categories['bollinger']
    foreign_cfg = categories['foreign']

    required_days = max(
        120,
        int(rsi_cfg['period']) + int(rsi_cfg['signal_period']) + int(rsi_cfg['cross_lookback_bars']) + 10,
        int(bb_cfg['period']) + 70,
    )
    foreign_days = max(int(foreign_cfg['days']), 1)

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
        stocks = provider.list_stocks(target_market)
        for stock in stocks:
            run.total_scanned += 1
            try:
                bars = provider.get_daily_bars(stock.code, required_days)
                foreign_data = get_foreign_investor_context(
                    db,
                    provider,
                    stock.code,
                    foreign_days,
                )
                evaluated = _evaluate_stock(strategy, strategy_config, stock, bars, foreign_data)

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
