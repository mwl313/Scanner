"""add stock daily bar cache table

Revision ID: 0006_stock_daily_bar_cache
Revises: 0005_foreign_kis_stability
Create Date: 2026-03-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006_stock_daily_bar_cache'
down_revision: Union[str, None] = '0005_foreign_kis_stability'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'stock_daily_bars',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('stock_code', sa.String(length=20), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('open_price', sa.Numeric(14, 2), nullable=False),
        sa.Column('high_price', sa.Numeric(14, 2), nullable=False),
        sa.Column('low_price', sa.Numeric(14, 2), nullable=False),
        sa.Column('close_price', sa.Numeric(14, 2), nullable=False),
        sa.Column('volume', sa.BIGINT(), nullable=False),
        sa.Column('trading_value', sa.BIGINT(), nullable=False),
        sa.Column('source', sa.String(length=80), nullable=False),
        sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_code', 'trade_date', name='uq_stock_daily_bars_stock_trade_date'),
    )
    op.create_index(op.f('ix_stock_daily_bars_stock_code'), 'stock_daily_bars', ['stock_code'], unique=False)
    op.create_index(op.f('ix_stock_daily_bars_trade_date'), 'stock_daily_bars', ['trade_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_stock_daily_bars_trade_date'), table_name='stock_daily_bars')
    op.drop_index(op.f('ix_stock_daily_bars_stock_code'), table_name='stock_daily_bars')
    op.drop_table('stock_daily_bars')
