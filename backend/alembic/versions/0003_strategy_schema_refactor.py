"""add strategy_config schema and backfill from legacy fields

Revision ID: 0003_strategy_schema_refactor
Revises: 0002_foreign_investor_option_a
Create Date: 2026-03-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_strategy_schema_refactor'
down_revision: Union[str, None] = '0002_foreign_investor_option_a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'strategies',
        sa.Column('strategy_config', sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    op.execute(
        """
        UPDATE strategies
        SET strategy_config = jsonb_build_object(
            'version', 1,
            'market', UPPER(COALESCE(market, 'KOSPI')),
            'scoring', jsonb_build_object('normalize_to_percent', true),
            'categories', jsonb_build_object(
                'rsi', jsonb_build_object(
                    'enabled', true,
                    'mandatory', true,
                    'weight', 30,
                    'period', COALESCE(rsi_period, 14),
                    'signal_period', COALESCE(rsi_signal_period, 9),
                    'cross_lookback_bars', 1,
                    'min', COALESCE(rsi_min, 30.0),
                    'max', COALESCE(rsi_max, 40.0)
                ),
                'bollinger', jsonb_build_object(
                    'enabled', true,
                    'mandatory', false,
                    'weight', 20,
                    'period', COALESCE(bb_period, 20),
                    'std', COALESCE(bb_std, 2.0),
                    'lower_proximity_pct', 0.03
                ),
                'ma', jsonb_build_object(
                    'price_vs_ma20', jsonb_build_object(
                        'enabled', COALESCE(use_ma20_filter, true),
                        'mandatory', COALESCE(use_ma20_filter, true),
                        'weight', 15,
                        'mode', 'near_or_above',
                        'tolerance_pct', 0.02
                    ),
                    'ma5_vs_ma20', jsonb_build_object(
                        'enabled', COALESCE(use_ma5_filter, true),
                        'mandatory', false,
                        'weight', 10,
                        'mode', 'ma5_equal_or_above_ma20'
                    ),
                    'ma20_vs_ma60', jsonb_build_object(
                        'enabled', false,
                        'mandatory', false,
                        'weight', 10,
                        'mode', 'ma20_equal_or_above_ma60'
                    )
                ),
                'foreign', jsonb_build_object(
                    'enabled', true,
                    'mandatory', false,
                    'weight', 20,
                    'days', COALESCE(foreign_net_buy_days, 3),
                    'unavailable_policy', 'neutral'
                ),
                'market_cap', jsonb_build_object(
                    'enabled', true,
                    'mandatory', true,
                    'weight', 0,
                    'min_market_cap', COALESCE(min_market_cap, 3000000000000)
                ),
                'trading_value', jsonb_build_object(
                    'enabled', true,
                    'mandatory', true,
                    'weight', 10,
                    'min_trading_value', COALESCE(min_trading_value, 10000000000)
                )
            )
        )
        WHERE strategy_config IS NULL OR strategy_config::text = '{}';
        """
    )

    op.alter_column('strategies', 'strategy_config', server_default=None)


def downgrade() -> None:
    op.drop_column('strategies', 'strategy_config')

