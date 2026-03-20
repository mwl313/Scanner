from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.models.strategy import Strategy
from app.schemas.strategy import StrategyConfig


def _deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _get(legacy_source: Strategy | dict[str, Any], key: str, default: Any) -> Any:
    if isinstance(legacy_source, Strategy):
        value = getattr(legacy_source, key, default)
        return default if value is None else value
    value = legacy_source.get(key, default)
    return default if value is None else value


def legacy_strategy_to_config(legacy_source: Strategy | dict[str, Any]) -> dict:
    return StrategyConfig.model_validate(
        {
            'version': 1,
            'market': str(_get(legacy_source, 'market', 'KOSPI')).upper(),
            'scoring': {'normalize_to_percent': True},
            'categories': {
                'rsi': {
                    'enabled': True,
                    'mandatory': True,
                    'weight': 30,
                    'period': int(_get(legacy_source, 'rsi_period', 14)),
                    'signal_period': int(_get(legacy_source, 'rsi_signal_period', 9)),
                    'cross_lookback_bars': 1,
                    'min': float(_get(legacy_source, 'rsi_min', 30.0)),
                    'max': float(_get(legacy_source, 'rsi_max', 40.0)),
                },
                'bollinger': {
                    'enabled': True,
                    'mandatory': False,
                    'weight': 20,
                    'period': int(_get(legacy_source, 'bb_period', 20)),
                    'std': float(_get(legacy_source, 'bb_std', 2.0)),
                    'lower_proximity_pct': 0.03,
                },
                'ma': {
                    'price_vs_ma20': {
                        'enabled': bool(_get(legacy_source, 'use_ma20_filter', True)),
                        'mandatory': bool(_get(legacy_source, 'use_ma20_filter', True)),
                        'weight': 15,
                        'mode': 'near_or_above',
                        'tolerance_pct': 0.02,
                    },
                    'ma5_vs_ma20': {
                        'enabled': bool(_get(legacy_source, 'use_ma5_filter', True)),
                        'mandatory': False,
                        'weight': 10,
                        'mode': 'ma5_equal_or_above_ma20',
                    },
                    'ma20_vs_ma60': {
                        'enabled': False,
                        'mandatory': False,
                        'weight': 10,
                        'mode': 'ma20_equal_or_above_ma60',
                    },
                },
                'foreign': {
                    'enabled': True,
                    'mandatory': False,
                    'weight': 20,
                    'days': int(_get(legacy_source, 'foreign_net_buy_days', 3)),
                    'unavailable_policy': 'neutral',
                },
                'market_cap': {
                    'enabled': True,
                    'mandatory': True,
                    'weight': 0,
                    'min_market_cap': int(_get(legacy_source, 'min_market_cap', 3000000000000)),
                },
                'trading_value': {
                    'enabled': True,
                    'mandatory': True,
                    'weight': 10,
                    'min_trading_value': int(_get(legacy_source, 'min_trading_value', 10000000000)),
                },
            },
        }
    ).model_dump()


def normalize_strategy_config(
    raw_config: StrategyConfig | dict[str, Any] | None,
    *,
    legacy_source: Strategy | dict[str, Any] | None = None,
) -> dict:
    if raw_config in (None, {}):
        if legacy_source is None:
            return StrategyConfig().model_dump()
        return legacy_strategy_to_config(legacy_source)

    raw_dict = raw_config.model_dump() if isinstance(raw_config, StrategyConfig) else dict(raw_config)
    merged = _deep_merge(StrategyConfig().model_dump(), raw_dict)
    return StrategyConfig.model_validate(merged).model_dump()


def strategy_config_to_legacy_fields(strategy_config: StrategyConfig | dict[str, Any]) -> dict:
    config = normalize_strategy_config(strategy_config)
    categories = config['categories']
    rsi = categories['rsi']
    bollinger = categories['bollinger']
    ma = categories['ma']
    foreign = categories['foreign']
    market_cap = categories['market_cap']
    trading_value = categories['trading_value']

    return {
        'market': config['market'],
        'min_market_cap': int(market_cap['min_market_cap']),
        'min_trading_value': int(trading_value['min_trading_value']),
        'rsi_period': int(rsi['period']),
        'rsi_signal_period': int(rsi['signal_period']),
        'rsi_min': float(rsi['min']),
        'rsi_max': float(rsi['max']),
        'bb_period': int(bollinger['period']),
        'bb_std': float(bollinger['std']),
        'use_ma5_filter': bool(ma['ma5_vs_ma20']['enabled']),
        'use_ma20_filter': bool(ma['price_vs_ma20']['enabled']),
        'foreign_net_buy_days': int(foreign['days']),
    }


def ensure_strategy_config(strategy: Strategy) -> tuple[dict, bool]:
    normalized = normalize_strategy_config(strategy.strategy_config, legacy_source=strategy)
    changed = strategy.strategy_config != normalized
    if changed:
        strategy.strategy_config = normalized
    return normalized, changed

