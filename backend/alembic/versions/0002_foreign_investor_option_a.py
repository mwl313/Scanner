"""add foreign investor daily table and scan result metadata

Revision ID: 0002_foreign_investor_option_a
Revises: 0001_initial
Create Date: 2026-03-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_foreign_investor_option_a'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'foreign_investor_daily',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('stock_code', sa.String(length=20), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('net_buy_value', sa.BIGINT(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_code', 'trade_date', name='uq_foreign_investor_daily_stock_trade_date'),
    )
    op.create_index(op.f('ix_foreign_investor_daily_stock_code'), 'foreign_investor_daily', ['stock_code'], unique=False)
    op.create_index(op.f('ix_foreign_investor_daily_trade_date'), 'foreign_investor_daily', ['trade_date'], unique=False)

    op.add_column('scan_results', sa.Column('foreign_net_buy_confirmed_value', sa.BIGINT(), nullable=True))
    op.add_column('scan_results', sa.Column('foreign_net_buy_snapshot_value', sa.BIGINT(), nullable=True))
    op.add_column(
        'scan_results',
        sa.Column('foreign_data_status', sa.String(length=20), nullable=False, server_default='unavailable'),
    )
    op.add_column('scan_results', sa.Column('foreign_data_source', sa.String(length=80), nullable=True))
    op.alter_column('scan_results', 'foreign_data_status', server_default=None)


def downgrade() -> None:
    op.drop_column('scan_results', 'foreign_data_source')
    op.drop_column('scan_results', 'foreign_data_status')
    op.drop_column('scan_results', 'foreign_net_buy_snapshot_value')
    op.drop_column('scan_results', 'foreign_net_buy_confirmed_value')

    op.drop_index(op.f('ix_foreign_investor_daily_trade_date'), table_name='foreign_investor_daily')
    op.drop_index(op.f('ix_foreign_investor_daily_stock_code'), table_name='foreign_investor_daily')
    op.drop_table('foreign_investor_daily')
