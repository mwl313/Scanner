import argparse
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.strategy import Strategy
from app.services.scan_benchmark_service import (
    report_samples_to_csv_rows,
    report_to_markdown,
    run_scan_benchmark,
)
from app.utils.reporting import write_csv_report, write_markdown_report

PRESETS: dict[str, dict] = {
    'custom': {},
    'mock-smoke': {
        'provider': 'mock',
        'universe_limits': [20, 40],
        'pre_screen_mode': 'both',
        'repeats': 1,
    },
    'kis-baseline': {
        'provider': 'kis',
        'universe_limits': [120, 200, 300, 500],
        'pre_screen_mode': 'off',
        'repeats': 3,
    },
    'kis-prescreen': {
        'provider': 'kis',
        'universe_limits': [120, 200, 300, 500],
        'pre_screen_mode': 'on',
        'repeats': 3,
    },
    'kis-scaling': {
        'provider': 'kis',
        'universe_limits': [120, 200, 300, 500],
        'pre_screen_mode': 'both',
        'repeats': 3,
    },
}


def _parse_universe_limits(raw: str) -> list[int]:
    values: list[int] = []
    for token in raw.split(','):
        item = token.strip()
        if not item:
            continue
        try:
            values.append(int(item))
        except ValueError as exc:
            raise SystemExit(f'Invalid universe limit: {item}') from exc
    if not values:
        raise SystemExit('Universe limits are empty')
    return values


def _resolve_pre_screen_modes(mode: str) -> list[bool]:
    normalized = mode.strip().lower()
    if normalized == 'off':
        return [False]
    if normalized == 'on':
        return [True]
    if normalized == 'both':
        return [False, True]
    raise SystemExit(f'Invalid pre-screen mode: {mode}')


def _resolve_strategy(db, strategy_id: int | None, strategy_name: str | None) -> Strategy:
    if strategy_id is not None:
        strategy = db.scalar(select(Strategy).where(Strategy.id == strategy_id))
        if not strategy:
            raise SystemExit(f'Strategy not found: id={strategy_id}')
        return strategy

    if strategy_name:
        strategy = db.scalar(select(Strategy).where(Strategy.name == strategy_name).order_by(Strategy.id.asc()))
        if not strategy:
            raise SystemExit(f'Strategy not found: name={strategy_name}')
        return strategy

    strategy = db.scalar(select(Strategy).where(Strategy.is_active.is_(True)).order_by(Strategy.id.asc()))
    if not strategy:
        strategy = db.scalar(select(Strategy).order_by(Strategy.id.asc()))
    if not strategy:
        raise SystemExit('No strategy available in database')
    return strategy


def _apply_preset(args, preset_name: str):
    preset = PRESETS.get(preset_name, {})
    if not preset:
        return args
    if preset.get('provider') and args.provider is None:
        args.provider = preset['provider']
    if preset.get('universe_limits') and args.universe_limits is None:
        args.universe_limits = ','.join(str(item) for item in preset['universe_limits'])
    if preset.get('pre_screen_mode') and args.pre_screen_mode is None:
        args.pre_screen_mode = preset['pre_screen_mode']
    if preset.get('repeats') and args.repeats is None:
        args.repeats = preset['repeats']
    return args


def _validate_kis_environment(settings, provider_name: str):
    if provider_name.lower() != 'kis':
        return
    if not settings.kis_app_key or not settings.kis_app_secret:
        raise SystemExit('KIS benchmark requires KIS_APP_KEY and KIS_APP_SECRET in environment')


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    settings = get_settings()
    parser = argparse.ArgumentParser(description='Run scan benchmark and generate markdown/csv reports')
    parser.add_argument('--preset', choices=sorted(PRESETS.keys()), default='custom')
    parser.add_argument('--strategy-id', type=int, default=None)
    parser.add_argument('--strategy-name', type=str, default=None)
    parser.add_argument('--provider', choices=['mock', 'kis'], default=None, help='benchmark provider')
    parser.add_argument('--universe-limits', type=str, default=None)
    parser.add_argument('--include-full-universe', action='store_true', help='append 0(full universe) case')
    parser.add_argument('--allow-full-universe', action='store_true', help='required for limit=0')
    parser.add_argument('--repeats', type=int, default=None)
    parser.add_argument('--pre-screen-mode', choices=['off', 'on', 'both'], default=None)
    parser.add_argument('--pre-screen-min-market-cap', type=int, default=None)
    parser.add_argument('--output-dir', type=str, default='reports')
    parser.add_argument('--keep-runs', action='store_true', help='keep benchmark scan runs in DB')
    parser.add_argument('--no-provider-warmup', action='store_true', help='disable provider universe warmup')
    args = parser.parse_args()

    args = _apply_preset(args, args.preset)
    provider_name = args.provider or settings.data_provider
    universe_limits = _parse_universe_limits(args.universe_limits or '120,200,300,500')
    repeats = args.repeats if args.repeats is not None else 3
    pre_screen_mode = args.pre_screen_mode or 'both'
    pre_screen_modes = _resolve_pre_screen_modes(pre_screen_mode)

    if args.include_full_universe and 0 not in universe_limits:
        universe_limits.append(0)
    if any(limit <= 0 for limit in universe_limits) and not args.allow_full_universe:
        raise SystemExit('Full universe case(limit=0) requires --allow-full-universe flag')

    _validate_kis_environment(settings, provider_name)

    planned_case_count = len(set(universe_limits)) * len(set(pre_screen_modes))
    total_runs = planned_case_count * repeats
    if total_runs >= 20:
        print(f'[benchmark][warn] large benchmark: cases={planned_case_count}, repeats={repeats}, total_runs={total_runs}')
    if any(limit <= 0 for limit in universe_limits):
        print('[benchmark][warn] full universe case included. This can take long and stress rate limits.')

    db = SessionLocal()
    try:
        strategy = _resolve_strategy(db, args.strategy_id, args.strategy_name)

        print('[benchmark] started')
        print(f'[benchmark] preset: {args.preset}')
        print(f'[benchmark] strategy: {strategy.id} / {strategy.name}')
        print(f'[benchmark] provider: {provider_name}')
        print(f'[benchmark] limits: {universe_limits}')
        print(f'[benchmark] pre-screen modes: {pre_screen_modes}')
        print(f'[benchmark] repeats: {repeats}')
        print(f'[benchmark] output dir: {args.output_dir}')

        report = run_scan_benchmark(
            db,
            strategy,
            provider_name=provider_name,
            universe_limits=universe_limits,
            repeats=repeats,
            pre_screen_modes=pre_screen_modes,
            pre_screen_min_market_cap=args.pre_screen_min_market_cap,
            allow_full_universe=args.allow_full_universe,
            keep_runs=args.keep_runs,
            warmup_provider_universe=not args.no_provider_warmup,
        )

        markdown = report_to_markdown(report)
        csv_rows = report_samples_to_csv_rows(report)
        csv_fieldnames = list(csv_rows[0].keys()) if csv_rows else ['case_label', 'run_status']

        md_path = write_markdown_report(
            markdown,
            output_dir=args.output_dir,
            prefix='scan-benchmark',
        )
        csv_path = write_csv_report(
            rows=csv_rows,
            fieldnames=csv_fieldnames,
            output_dir=args.output_dir,
            prefix='scan-benchmark',
        )

        print(f'[benchmark] warmup universe count: {report.warmup_universe_count}')
        print(f'[benchmark] estimated stock scans upper bound: {report.estimated_stock_scans_upper_bound}')
        print(f'[benchmark] markdown report: {md_path}')
        print(f'[benchmark] csv report: {csv_path}')
        print(f'[benchmark] recommendation: {report.recommendation}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
