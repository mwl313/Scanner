from app.schemas.strategy import StrategyConfig
from app.services.strategy_schema_service import (
    legacy_strategy_to_config,
    normalize_strategy_config,
    strategy_config_to_legacy_fields,
)


def test_legacy_strategy_mapping_to_new_config():
    legacy = {
        'market': 'KOSPI',
        'min_market_cap': 5000000000000,
        'min_trading_value': 12000000000,
        'rsi_period': 12,
        'rsi_signal_period': 7,
        'rsi_min': 25,
        'rsi_max': 45,
        'bb_period': 18,
        'bb_std': 2.5,
        'use_ma5_filter': False,
        'use_ma20_filter': True,
        'foreign_net_buy_days': 5,
    }

    config = legacy_strategy_to_config(legacy)
    categories = config['categories']

    assert config['market'] == 'KOSPI'
    assert categories['rsi']['period'] == 12
    assert categories['rsi']['signal_period'] == 7
    assert categories['rsi']['min'] == 25
    assert categories['rsi']['max'] == 45
    assert categories['bollinger']['period'] == 18
    assert categories['bollinger']['std'] == 2.5
    assert categories['ma']['ma5_vs_ma20']['enabled'] is False
    assert categories['ma']['price_vs_ma20']['enabled'] is True
    assert categories['foreign']['days'] == 5
    assert categories['market_cap']['min_market_cap'] == 5000000000000
    assert categories['trading_value']['min_trading_value'] == 12000000000


def test_normalize_partial_strategy_config_merges_defaults():
    partial = {
        'categories': {
            'rsi': {'period': 20, 'enabled': False},
            'foreign': {'days': 7},
        }
    }
    normalized = normalize_strategy_config(partial)

    assert normalized['categories']['rsi']['enabled'] is False
    assert normalized['categories']['rsi']['period'] == 20
    assert normalized['categories']['rsi']['signal_period'] == 9
    assert normalized['categories']['foreign']['days'] == 7
    assert normalized['categories']['trading_value']['mandatory'] is True


def test_strategy_config_to_legacy_fields_projection():
    config = StrategyConfig().model_dump()
    config['categories']['rsi']['period'] = 21
    config['categories']['foreign']['days'] = 4
    config['categories']['ma']['price_vs_ma20']['enabled'] = False

    legacy = strategy_config_to_legacy_fields(config)

    assert legacy['rsi_period'] == 21
    assert legacy['foreign_net_buy_days'] == 4
    assert legacy['use_ma20_filter'] is False
