from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
import statistics
import time
from typing import Callable, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.scan_result import ScanResult
from app.models.scan_run import ScanRun
from app.models.strategy import Strategy
from app.providers.factory import create_market_data_provider
from app.services.scan_service import ScanExecutionOptions, run_scan_with_metrics
from app.utils.datetime_utils import as_kst, utcnow

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar('T')


@dataclass(frozen=True)
class TimedValue(Generic[T]):
    value: T
    elapsed_seconds: float


def measure_elapsed_call(func: Callable[..., T], *args, **kwargs) -> TimedValue[T]:
    started = time.perf_counter()
    value = func(*args, **kwargs)
    elapsed = time.perf_counter() - started
    return TimedValue(value=value, elapsed_seconds=elapsed)


@dataclass(frozen=True)
class BenchmarkCase:
    universe_limit: int
    pre_screen_enabled: bool

    @property
    def label(self) -> str:
        limit_label = 'ALL' if self.universe_limit <= 0 else str(self.universe_limit)
        mode = 'ON' if self.pre_screen_enabled else 'OFF'
        return f'limit={limit_label}, pre_screen={mode}'


@dataclass
class BenchmarkSample:
    case_label: str
    universe_limit: int
    pre_screen_enabled: bool
    repeat_index: int
    provider: str
    strategy_id: int
    strategy_name: str
    started_at: datetime
    finished_at: datetime
    total_elapsed_seconds: float
    wrapper_elapsed_seconds: float
    provider_fetch_elapsed_seconds: float
    universe_build_elapsed_seconds: float
    scan_loop_elapsed_seconds: float
    persistence_elapsed_seconds: float
    original_universe_count: int
    limited_universe_count: int
    filtered_universe_count: int
    total_scanned: int
    total_matched: int
    grade_excluded_count: int
    failed_count: int
    success_rate: float
    scanned_per_sec: float
    avg_seconds_per_stock: float
    run_status: str
    grade_a_count: int = 0
    grade_b_count: int = 0
    grade_c_count: int = 0
    run_id: int | None = None
    error_message: str | None = None


@dataclass
class BenchmarkCaseSummary:
    case_label: str
    universe_limit: int
    pre_screen_enabled: bool
    runs: int
    completed_runs: int
    error_runs: int
    avg_total_elapsed_seconds: float
    min_total_elapsed_seconds: float
    max_total_elapsed_seconds: float
    avg_provider_fetch_elapsed_seconds: float
    avg_universe_build_elapsed_seconds: float
    avg_scan_loop_elapsed_seconds: float
    avg_persistence_elapsed_seconds: float
    avg_original_universe_count: float
    avg_filtered_universe_count: float
    avg_total_scanned: float
    avg_total_matched: float
    avg_grade_excluded_count: float
    avg_failed_count: float
    success_rate: float
    avg_scanned_per_sec: float
    avg_seconds_per_stock: float


@dataclass
class ScanBenchmarkReport:
    generated_at: datetime
    provider: str
    strategy_id: int
    strategy_name: str
    market: str
    repeats: int
    universe_limits: list[int]
    pre_screen_modes: list[bool]
    pre_screen_min_market_cap: int | None
    warmup_enabled: bool
    warmup_universe_count: int
    warmup_elapsed_seconds: float
    estimated_stock_scans_upper_bound: int
    samples: list[BenchmarkSample]
    summaries: list[BenchmarkCaseSummary]
    observations: list[str]
    suspicious_findings: list[str]
    recommendation: str


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.mean(values))


def _build_cases(universe_limits: list[int], pre_screen_modes: list[bool]) -> list[BenchmarkCase]:
    unique_limits = sorted({int(item) for item in universe_limits}, key=lambda x: (x <= 0, x if x > 0 else 10**9))
    unique_modes = [mode for mode in [False, True] if bool(mode) in {bool(v) for v in pre_screen_modes}]
    cases: list[BenchmarkCase] = []
    for limit in unique_limits:
        for mode in unique_modes:
            cases.append(BenchmarkCase(universe_limit=limit, pre_screen_enabled=mode))
    return cases


def _build_execution_plan(cases: list[BenchmarkCase], repeats: int) -> list[tuple[int, BenchmarkCase]]:
    limits = sorted({case.universe_limit for case in cases}, key=lambda x: (x <= 0, x if x > 0 else 10**9))
    has_off = any(case.pre_screen_enabled is False for case in cases)
    has_on = any(case.pre_screen_enabled is True for case in cases)
    plan: list[tuple[int, BenchmarkCase]] = []

    case_map = {(case.universe_limit, case.pre_screen_enabled): case for case in cases}

    for repeat_index in range(1, repeats + 1):
        mode_order = [False, True]
        if has_off and has_on and repeat_index % 2 == 0:
            mode_order = [True, False]
        for limit in limits:
            for mode in mode_order:
                target = case_map.get((limit, mode))
                if target is not None:
                    plan.append((repeat_index, target))
    return plan


def _grade_counts_for_run(db: Session, run_id: int) -> dict[str, int]:
    stmt = (
        select(ScanResult.grade, func.count(ScanResult.id))
        .where(ScanResult.scan_run_id == run_id)
        .group_by(ScanResult.grade)
    )
    rows = db.execute(stmt).all()
    counts = {'A': 0, 'B': 0, 'C': 0, 'EXCLUDED': 0}
    for grade, count in rows:
        normalized = str(grade or '').upper()
        if normalized in counts:
            counts[normalized] = int(count)
    return counts


def _estimate_stock_scans_upper_bound(universe_count: int, cases: list[BenchmarkCase], repeats: int) -> int:
    total = 0
    for case in cases:
        if case.universe_limit <= 0:
            total += universe_count
        else:
            total += min(case.universe_limit, universe_count)
    return total * repeats


def _build_case_summaries(samples: list[BenchmarkSample]) -> list[BenchmarkCaseSummary]:
    grouped: dict[tuple[int, bool], list[BenchmarkSample]] = {}
    for sample in samples:
        grouped.setdefault((sample.universe_limit, sample.pre_screen_enabled), []).append(sample)

    summaries: list[BenchmarkCaseSummary] = []
    for (limit, pre_screen_enabled), items in grouped.items():
        completed_items = [item for item in items if item.run_status in {'completed', 'partial_failed'}]
        error_runs = sum(1 for item in items if item.run_status == 'error')
        total_scanned = sum(item.total_scanned for item in completed_items)
        total_matched = sum(item.total_matched for item in completed_items)
        success_rate = ((total_matched / total_scanned) * 100.0) if total_scanned > 0 else 0.0

        summaries.append(
            BenchmarkCaseSummary(
                case_label=f"limit={'ALL' if limit <= 0 else limit}, pre_screen={'ON' if pre_screen_enabled else 'OFF'}",
                universe_limit=limit,
                pre_screen_enabled=pre_screen_enabled,
                runs=len(items),
                completed_runs=len(completed_items),
                error_runs=error_runs,
                avg_total_elapsed_seconds=_mean([item.total_elapsed_seconds for item in items]),
                min_total_elapsed_seconds=min([item.total_elapsed_seconds for item in items]) if items else 0.0,
                max_total_elapsed_seconds=max([item.total_elapsed_seconds for item in items]) if items else 0.0,
                avg_provider_fetch_elapsed_seconds=_mean([item.provider_fetch_elapsed_seconds for item in items]),
                avg_universe_build_elapsed_seconds=_mean([item.universe_build_elapsed_seconds for item in items]),
                avg_scan_loop_elapsed_seconds=_mean([item.scan_loop_elapsed_seconds for item in items]),
                avg_persistence_elapsed_seconds=_mean([item.persistence_elapsed_seconds for item in items]),
                avg_original_universe_count=_mean([float(item.original_universe_count) for item in items]),
                avg_filtered_universe_count=_mean([float(item.filtered_universe_count) for item in items]),
                avg_total_scanned=_mean([float(item.total_scanned) for item in items]),
                avg_total_matched=_mean([float(item.total_matched) for item in items]),
                avg_grade_excluded_count=_mean([float(item.grade_excluded_count) for item in items]),
                avg_failed_count=_mean([float(item.failed_count) for item in items]),
                success_rate=success_rate,
                avg_scanned_per_sec=_mean([item.scanned_per_sec for item in items]),
                avg_seconds_per_stock=_mean([item.avg_seconds_per_stock for item in items]),
            )
        )

    summaries.sort(key=lambda item: (item.pre_screen_enabled, item.universe_limit if item.universe_limit > 0 else 10**9))
    return summaries


def _build_observations(summaries: list[BenchmarkCaseSummary]) -> list[str]:
    observations: list[str] = []
    indexed: dict[tuple[int, bool], BenchmarkCaseSummary] = {
        (item.universe_limit, item.pre_screen_enabled): item for item in summaries
    }
    limits = sorted({item.universe_limit for item in summaries}, key=lambda x: (x <= 0, x if x > 0 else 10**9))

    for limit in limits:
        off_case = indexed.get((limit, False))
        on_case = indexed.get((limit, True))
        if not off_case or not on_case:
            continue
        if off_case.avg_total_elapsed_seconds <= 0:
            continue
        reduction = ((off_case.avg_total_elapsed_seconds - on_case.avg_total_elapsed_seconds) / off_case.avg_total_elapsed_seconds) * 100.0
        observations.append(
            f"- limit={('ALL' if limit <= 0 else limit)}에서 pre-screen ON은 OFF 대비 평균 총시간이 {reduction:+.1f}% 변화했습니다."
        )

    if len(limits) >= 2:
        first = indexed.get((limits[0], False)) or indexed.get((limits[0], True))
        last = indexed.get((limits[-1], False)) or indexed.get((limits[-1], True))
        if first and last and first.avg_total_elapsed_seconds > 0:
            growth = last.avg_total_elapsed_seconds / first.avg_total_elapsed_seconds
            observations.append(
                f"- 최소 limit 대비 최대 limit 평균 총시간은 {growth:.2f}배입니다."
            )

    error_runs = sum(item.error_runs for item in summaries)
    if error_runs > 0:
        observations.append(f'- 에러가 발생한 실행이 {error_runs}회 있습니다. provider 응답 안정성을 점검하세요.')

    if not observations:
        observations.append('- 관찰 가능한 변동이 적어 추가 해석 포인트가 없습니다.')
    return observations


def _build_suspicious_findings(samples: list[BenchmarkSample], summaries: list[BenchmarkCaseSummary]) -> list[str]:
    findings: list[str] = []

    # Same scanned count but large elapsed gap between ON/OFF for same limit+repeat.
    pair_map: dict[tuple[int, int], dict[bool, BenchmarkSample]] = {}
    for sample in samples:
        if sample.run_status not in {'completed', 'partial_failed'}:
            continue
        pair_map.setdefault((sample.universe_limit, sample.repeat_index), {})[sample.pre_screen_enabled] = sample

    for (limit, repeat_index), pair in pair_map.items():
        off_sample = pair.get(False)
        on_sample = pair.get(True)
        if not off_sample or not on_sample:
            continue
        if off_sample.total_scanned != on_sample.total_scanned:
            continue
        base = off_sample.total_elapsed_seconds
        if base <= 0:
            continue
        delta_ratio = abs(on_sample.total_elapsed_seconds - off_sample.total_elapsed_seconds) / base
        if delta_ratio >= 0.40:
            findings.append(
                f"- suspicious: limit={('ALL' if limit <= 0 else limit)}, repeat={repeat_index}에서 scanned 수가 동일({off_sample.total_scanned})한데 ON/OFF 총시간 차이가 {delta_ratio*100:.1f}%입니다."
            )

    # High repeat variance
    grouped: dict[tuple[int, bool], list[BenchmarkSample]] = {}
    for sample in samples:
        if sample.run_status in {'completed', 'partial_failed'}:
            grouped.setdefault((sample.universe_limit, sample.pre_screen_enabled), []).append(sample)

    for (limit, mode), items in grouped.items():
        values = [item.total_elapsed_seconds for item in items]
        if len(values) < 2:
            continue
        mean_value = _mean(values)
        if mean_value <= 0:
            continue
        stdev = float(statistics.stdev(values))
        coeff = stdev / mean_value
        if coeff >= 0.30:
            findings.append(
                f"- suspicious: limit={('ALL' if limit <= 0 else limit)}, pre_screen={'ON' if mode else 'OFF'} 반복 편차(CV)가 {coeff:.2f}로 큽니다."
            )

    for summary in summaries:
        if summary.error_runs > 0:
            findings.append(
                f"- suspicious: {summary.case_label}에서 error_runs={summary.error_runs}/{summary.runs}."
            )

    if not findings:
        findings.append('- suspicious 패턴이 탐지되지 않았습니다.')
    return findings


def _build_recommendation(report: ScanBenchmarkReport) -> str:
    if report.provider.lower() == 'mock':
        return 'Mock provider 결과는 기능 검증용입니다. 운영 limit 결정은 KIS benchmark 결과로 판단하세요.'

    candidates = [
        item
        for item in report.summaries
        if item.completed_runs > 0 and item.error_runs == 0 and item.avg_total_scanned > 0
    ]
    if not candidates:
        return '안정적으로 완료된 KIS 케이스가 부족하여 운영값을 제안할 수 없습니다.'

    candidates.sort(
        key=lambda item: (
            item.avg_scanned_per_sec,
            item.avg_total_scanned,
            -item.avg_total_elapsed_seconds,
        ),
        reverse=True,
    )
    best = candidates[0]
    limit_label = '전체' if best.universe_limit <= 0 else str(best.universe_limit)
    mode_label = 'ON' if best.pre_screen_enabled else 'OFF'
    return (
        f"권장 운영값: universe_limit={limit_label}, pre_screen={mode_label}. "
        f"(avg scanned/sec {best.avg_scanned_per_sec:.2f}, success {best.success_rate:.1f}%)"
    )


def _validate_request(
    *,
    provider_name: str,
    cases: list[BenchmarkCase],
    repeats: int,
    allow_full_universe: bool,
) -> None:
    if repeats < 1:
        raise ValueError('repeats must be >= 1')
    if not cases:
        raise ValueError('benchmark cases are empty')
    if any(case.universe_limit <= 0 for case in cases) and not allow_full_universe:
        raise ValueError('full universe benchmark requires allow_full_universe=True')

    if provider_name.lower() == 'kis':
        if not settings.kis_app_key or not settings.kis_app_secret:
            raise ValueError('KIS benchmark requires KIS_APP_KEY and KIS_APP_SECRET')

    total_runs = len(cases) * repeats
    if total_runs >= 16:
        logger.warning('Large benchmark workload: cases=%s repeats=%s total_runs=%s', len(cases), repeats, total_runs)


def run_scan_benchmark(
    db: Session,
    strategy: Strategy,
    *,
    provider_name: str,
    universe_limits: list[int],
    repeats: int = 3,
    pre_screen_modes: list[bool] | None = None,
    pre_screen_min_market_cap: int | None = None,
    allow_full_universe: bool = False,
    keep_runs: bool = False,
    warmup_provider_universe: bool = True,
) -> ScanBenchmarkReport:
    modes = pre_screen_modes or [False]
    cases = _build_cases(universe_limits, modes)
    _validate_request(
        provider_name=provider_name,
        cases=cases,
        repeats=repeats,
        allow_full_universe=allow_full_universe,
    )
    execution_plan = _build_execution_plan(cases, repeats)

    provider = create_market_data_provider(provider_name)
    target_market = str(strategy.market or 'KOSPI').upper()

    warmup_elapsed = 0.0
    warmup_universe_count = 0
    if warmup_provider_universe:
        warmup_timed = measure_elapsed_call(provider.list_stocks, target_market)
        warmup_elapsed = warmup_timed.elapsed_seconds
        warmup_universe_count = len(warmup_timed.value)
    else:
        warmup_universe_count = len(provider.list_stocks(target_market))

    estimated_stock_scans = _estimate_stock_scans_upper_bound(warmup_universe_count, cases, repeats)
    logger.info(
        'Starting benchmark (provider=%s, strategy=%s, market=%s, cases=%s, repeats=%s, warmup_universe=%s, est_stock_scans=%s)',
        provider_name,
        strategy.id,
        target_market,
        len(cases),
        repeats,
        warmup_universe_count,
        estimated_stock_scans,
    )

    samples: list[BenchmarkSample] = []
    total_runs = len(execution_plan)
    for run_seq, (repeat_index, case) in enumerate(execution_plan, start=1):
        logger.info(
            'Benchmark progress [%s/%s] repeat=%s case=%s',
            run_seq,
            total_runs,
            repeat_index,
            case.label,
        )
        started_at = utcnow()
        try:
            timed_outcome = measure_elapsed_call(
                run_scan_with_metrics,
                db,
                strategy,
                run_type='benchmark',
                provider=provider,
                execution_options=ScanExecutionOptions(
                    universe_limit=case.universe_limit,
                    pre_screen_enabled=case.pre_screen_enabled,
                    pre_screen_min_market_cap=pre_screen_min_market_cap,
                ),
            )
            outcome = timed_outcome.value
            finished_at = utcnow()
            grades = _grade_counts_for_run(db, outcome.run.id)
            scanned = int(outcome.run.total_scanned)
            matched = int(outcome.run.total_matched)
            failed = int(outcome.run.failed_count)
            excluded = int(grades['EXCLUDED'])
            total_elapsed = float(outcome.metrics.total_elapsed_seconds or timed_outcome.elapsed_seconds)
            success_rate = (matched / scanned * 100.0) if scanned > 0 else 0.0
            scanned_per_sec = (scanned / total_elapsed) if total_elapsed > 0 else 0.0
            avg_seconds_per_stock = (total_elapsed / scanned) if scanned > 0 else 0.0

            samples.append(
                BenchmarkSample(
                    case_label=case.label,
                    universe_limit=case.universe_limit,
                    pre_screen_enabled=case.pre_screen_enabled,
                    repeat_index=repeat_index,
                    provider=provider_name,
                    strategy_id=strategy.id,
                    strategy_name=strategy.name,
                    started_at=started_at,
                    finished_at=finished_at,
                    total_elapsed_seconds=total_elapsed,
                    wrapper_elapsed_seconds=timed_outcome.elapsed_seconds,
                    provider_fetch_elapsed_seconds=outcome.metrics.provider_fetch_elapsed_seconds,
                    universe_build_elapsed_seconds=outcome.metrics.universe_build_elapsed_seconds,
                    scan_loop_elapsed_seconds=outcome.metrics.scan_loop_elapsed_seconds,
                    persistence_elapsed_seconds=outcome.metrics.persistence_elapsed_seconds,
                    original_universe_count=outcome.metrics.original_universe_count,
                    limited_universe_count=outcome.metrics.limited_universe_count,
                    filtered_universe_count=outcome.metrics.pre_screen_universe_count,
                    total_scanned=scanned,
                    total_matched=matched,
                    grade_excluded_count=excluded,
                    failed_count=failed,
                    success_rate=success_rate,
                    scanned_per_sec=scanned_per_sec,
                    avg_seconds_per_stock=avg_seconds_per_stock,
                    run_status=outcome.run.status,
                    grade_a_count=grades['A'],
                    grade_b_count=grades['B'],
                    grade_c_count=grades['C'],
                    run_id=outcome.run.id,
                )
            )

            if not keep_runs:
                db.delete(outcome.run)
                db.commit()
            logger.info(
                'Benchmark case done [%s/%s] run_id=%s elapsed=%.3fs scanned=%s matched=%s failed=%s',
                run_seq,
                total_runs,
                outcome.run.id,
                total_elapsed,
                scanned,
                matched,
                failed,
            )
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            finished_at = utcnow()
            samples.append(
                BenchmarkSample(
                    case_label=case.label,
                    universe_limit=case.universe_limit,
                    pre_screen_enabled=case.pre_screen_enabled,
                    repeat_index=repeat_index,
                    provider=provider_name,
                    strategy_id=strategy.id,
                    strategy_name=strategy.name,
                    started_at=started_at,
                    finished_at=finished_at,
                    total_elapsed_seconds=0.0,
                    wrapper_elapsed_seconds=0.0,
                    provider_fetch_elapsed_seconds=0.0,
                    universe_build_elapsed_seconds=0.0,
                    scan_loop_elapsed_seconds=0.0,
                    persistence_elapsed_seconds=0.0,
                    original_universe_count=0,
                    limited_universe_count=0,
                    filtered_universe_count=0,
                    total_scanned=0,
                    total_matched=0,
                    grade_excluded_count=0,
                    failed_count=0,
                    success_rate=0.0,
                    scanned_per_sec=0.0,
                    avg_seconds_per_stock=0.0,
                    run_status='error',
                    error_message=str(exc),
                )
            )
            logger.exception(
                'Benchmark case failed [%s/%s] (%s, repeat=%s): %s',
                run_seq,
                total_runs,
                case.label,
                repeat_index,
                exc,
            )

    summaries = _build_case_summaries(samples)
    observations = _build_observations(summaries)
    report = ScanBenchmarkReport(
        generated_at=utcnow(),
        provider=provider_name,
        strategy_id=strategy.id,
        strategy_name=strategy.name,
        market=target_market,
        repeats=repeats,
        universe_limits=sorted({case.universe_limit for case in cases}, key=lambda x: (x <= 0, x if x > 0 else 10**9)),
        pre_screen_modes=sorted({bool(case.pre_screen_enabled) for case in cases}),
        pre_screen_min_market_cap=pre_screen_min_market_cap,
        warmup_enabled=warmup_provider_universe,
        warmup_universe_count=warmup_universe_count,
        warmup_elapsed_seconds=warmup_elapsed,
        estimated_stock_scans_upper_bound=estimated_stock_scans,
        samples=samples,
        summaries=summaries,
        observations=observations,
        suspicious_findings=[],
        recommendation='',
    )
    report.suspicious_findings = _build_suspicious_findings(report.samples, report.summaries)
    report.recommendation = _build_recommendation(report)
    return report


def report_to_markdown(report: ScanBenchmarkReport) -> str:
    generated = as_kst(report.generated_at).strftime('%Y-%m-%d %H:%M:%S KST')
    limit_labels = ['ALL' if item <= 0 else str(item) for item in report.universe_limits]
    mode_labels = ['ON' if item else 'OFF' for item in report.pre_screen_modes]

    lines: list[str] = []
    lines.append('# Scan Benchmark Report')
    lines.append('')
    lines.append('## 환경 정보')
    lines.append(f'- 생성 시각: {generated}')
    lines.append(f'- Provider: `{report.provider}`')
    lines.append(f'- Strategy: `{report.strategy_id} / {report.strategy_name}`')
    lines.append(f'- Market: `{report.market}`')
    lines.append(f'- Repeats: `{report.repeats}`')
    lines.append(f'- Universe limits: `{", ".join(limit_labels)}`')
    lines.append(f'- Pre-screen modes: `{", ".join(mode_labels)}`')
    lines.append(f'- Pre-screen min market cap: `{report.pre_screen_min_market_cap}`')
    lines.append(f'- Provider warmup: `{report.warmup_enabled}` (count={report.warmup_universe_count}, elapsed={report.warmup_elapsed_seconds:.3f}s)')
    lines.append(f'- Estimated stock scans upper bound: `{report.estimated_stock_scans_upper_bound}`')
    lines.append('')

    lines.append('## 케이스별 결과 (raw)')
    lines.append('')
    lines.append('| limit | pre_screen | repeat | original | filtered | scanned | matched | excluded | failed | total_elapsed(s) | stocks/sec | provider_fetch(s) | universe_build(s) | scan_loop(s) | persistence(s) | status |')
    lines.append('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |')
    for sample in report.samples:
        limit_label = 'ALL' if sample.universe_limit <= 0 else str(sample.universe_limit)
        mode_label = 'ON' if sample.pre_screen_enabled else 'OFF'
        lines.append(
            f'| {limit_label} | {mode_label} | {sample.repeat_index} | {sample.original_universe_count} | {sample.filtered_universe_count} '
            f'| {sample.total_scanned} | {sample.total_matched} | {sample.grade_excluded_count} | {sample.failed_count} '
            f'| {sample.total_elapsed_seconds:.3f} | {sample.scanned_per_sec:.2f} '
            f'| {sample.provider_fetch_elapsed_seconds:.3f} | {sample.universe_build_elapsed_seconds:.3f} '
            f'| {sample.scan_loop_elapsed_seconds:.3f} | {sample.persistence_elapsed_seconds:.3f} | {sample.run_status} |'
        )
    lines.append('')

    lines.append('## 집계 요약 (case 평균/최소/최대)')
    lines.append('')
    lines.append('| limit | pre_screen | runs | errors | elapsed avg/min/max(s) | scanned avg | matched avg | failed avg | success rate | scanned/sec avg |')
    lines.append('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
    for item in report.summaries:
        limit_label = 'ALL' if item.universe_limit <= 0 else str(item.universe_limit)
        mode_label = 'ON' if item.pre_screen_enabled else 'OFF'
        lines.append(
            f'| {limit_label} | {mode_label} | {item.runs} | {item.error_runs} '
            f'| {item.avg_total_elapsed_seconds:.3f} / {item.min_total_elapsed_seconds:.3f} / {item.max_total_elapsed_seconds:.3f} '
            f'| {item.avg_total_scanned:.1f} | {item.avg_total_matched:.1f} | {item.avg_failed_count:.1f} '
            f'| {item.success_rate:.1f}% | {item.avg_scanned_per_sec:.2f} |'
        )
    lines.append('')

    lines.append('## 해석 요약')
    lines.extend(report.observations)
    lines.append('')

    lines.append('## Suspicious Findings')
    lines.extend(report.suspicious_findings)
    lines.append('')

    lines.append('## 권장 운영값')
    lines.append(f'- {report.recommendation}')
    lines.append('')
    return '\n'.join(lines)


def report_samples_to_csv_rows(report: ScanBenchmarkReport) -> list[dict]:
    rows: list[dict] = []
    for sample in report.samples:
        rows.append(
            {
                'case_label': sample.case_label,
                'universe_limit': sample.universe_limit,
                'pre_screen_enabled': sample.pre_screen_enabled,
                'repeat_index': sample.repeat_index,
                'provider': sample.provider,
                'strategy_id': sample.strategy_id,
                'strategy_name': sample.strategy_name,
                'started_at': sample.started_at.isoformat(),
                'finished_at': sample.finished_at.isoformat(),
                'total_elapsed_seconds': f'{sample.total_elapsed_seconds:.4f}',
                'wrapper_elapsed_seconds': f'{sample.wrapper_elapsed_seconds:.4f}',
                'provider_fetch_elapsed_seconds': f'{sample.provider_fetch_elapsed_seconds:.4f}',
                'universe_build_elapsed_seconds': f'{sample.universe_build_elapsed_seconds:.4f}',
                'scan_loop_elapsed_seconds': f'{sample.scan_loop_elapsed_seconds:.4f}',
                'persistence_elapsed_seconds': f'{sample.persistence_elapsed_seconds:.4f}',
                'original_universe_count': sample.original_universe_count,
                'limited_universe_count': sample.limited_universe_count,
                'filtered_universe_count': sample.filtered_universe_count,
                'total_scanned': sample.total_scanned,
                'total_matched': sample.total_matched,
                'grade_excluded_count': sample.grade_excluded_count,
                'failed_count': sample.failed_count,
                'success_rate': f'{sample.success_rate:.2f}',
                'scanned_per_sec': f'{sample.scanned_per_sec:.4f}',
                'avg_seconds_per_stock': f'{sample.avg_seconds_per_stock:.4f}',
                'run_status': sample.run_status,
                'grade_a_count': sample.grade_a_count,
                'grade_b_count': sample.grade_b_count,
                'grade_c_count': sample.grade_c_count,
                'run_id': sample.run_id or '',
                'error_message': sample.error_message or '',
            }
        )
    return rows
