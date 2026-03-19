"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'strategies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('market', sa.String(length=20), nullable=False),
        sa.Column('min_market_cap', sa.BigInteger(), nullable=False),
        sa.Column('min_trading_value', sa.BigInteger(), nullable=False),
        sa.Column('rsi_period', sa.Integer(), nullable=False),
        sa.Column('rsi_signal_period', sa.Integer(), nullable=False),
        sa.Column('rsi_min', sa.Float(), nullable=False),
        sa.Column('rsi_max', sa.Float(), nullable=False),
        sa.Column('bb_period', sa.Integer(), nullable=False),
        sa.Column('bb_std', sa.Float(), nullable=False),
        sa.Column('use_ma5_filter', sa.Boolean(), nullable=False),
        sa.Column('use_ma20_filter', sa.Boolean(), nullable=False),
        sa.Column('foreign_net_buy_days', sa.Integer(), nullable=False),
        sa.Column('scan_interval_type', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_strategies_user_id'), 'strategies', ['user_id'], unique=False)

    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_sessions_token_hash'), 'sessions', ['token_hash'], unique=True)
    op.create_index(op.f('ix_sessions_expires_at'), 'sessions', ['expires_at'], unique=False)

    op.create_table(
        'scan_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=False),
        sa.Column('run_type', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('total_scanned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_matched', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_scan_runs_strategy_id'), 'scan_runs', ['strategy_id'], unique=False)

    op.create_table(
        'scan_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scan_run_id', sa.Integer(), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=False),
        sa.Column('stock_code', sa.String(length=20), nullable=False),
        sa.Column('stock_name', sa.String(length=120), nullable=False),
        sa.Column('market', sa.String(length=20), nullable=False),
        sa.Column('price', sa.Numeric(14, 2), nullable=False),
        sa.Column('ma5', sa.Numeric(14, 2), nullable=False),
        sa.Column('ma20', sa.Numeric(14, 2), nullable=False),
        sa.Column('ma60', sa.Numeric(14, 2), nullable=False),
        sa.Column('bb_upper', sa.Numeric(14, 2), nullable=False),
        sa.Column('bb_mid', sa.Numeric(14, 2), nullable=False),
        sa.Column('bb_lower', sa.Numeric(14, 2), nullable=False),
        sa.Column('rsi', sa.Numeric(8, 3), nullable=False),
        sa.Column('rsi_signal', sa.Numeric(8, 3), nullable=False),
        sa.Column('foreign_net_buy_value', sa.BIGINT(), nullable=False),
        sa.Column('trading_value', sa.BIGINT(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('grade', sa.String(length=20), nullable=False),
        sa.Column('matched_reasons_json', sa.JSON(), nullable=False),
        sa.Column('failed_reasons_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['scan_run_id'], ['scan_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_scan_results_scan_run_id'), 'scan_results', ['scan_run_id'], unique=False)
    op.create_index(op.f('ix_scan_results_strategy_id'), 'scan_results', ['strategy_id'], unique=False)
    op.create_index(op.f('ix_scan_results_stock_code'), 'scan_results', ['stock_code'], unique=False)
    op.create_index(op.f('ix_scan_results_grade'), 'scan_results', ['grade'], unique=False)

    op.create_table(
        'watchlist_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stock_code', sa.String(length=20), nullable=False),
        sa.Column('stock_name', sa.String(length=120), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'stock_code', name='uq_watchlist_user_stock'),
    )
    op.create_index(op.f('ix_watchlist_items_user_id'), 'watchlist_items', ['user_id'], unique=False)
    op.create_index(op.f('ix_watchlist_items_strategy_id'), 'watchlist_items', ['strategy_id'], unique=False)

    op.create_table(
        'trade_journals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=True),
        sa.Column('stock_code', sa.String(length=20), nullable=False),
        sa.Column('stock_name', sa.String(length=120), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('buy_reason', sa.Text(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('entry_price', sa.Numeric(14, 2), nullable=False),
        sa.Column('exit_price', sa.Numeric(14, 2), nullable=True),
        sa.Column('profit_value', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('profit_rate', sa.Numeric(8, 4), nullable=False, server_default='0'),
        sa.Column('memo', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_trade_journals_user_id'), 'trade_journals', ['user_id'], unique=False)
    op.create_index(op.f('ix_trade_journals_strategy_id'), 'trade_journals', ['strategy_id'], unique=False)
    op.create_index(op.f('ix_trade_journals_trade_date'), 'trade_journals', ['trade_date'], unique=False)

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=True),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_sent', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_strategy_id'), 'notifications', ['strategy_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notifications_strategy_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_table('notifications')

    op.drop_index(op.f('ix_trade_journals_trade_date'), table_name='trade_journals')
    op.drop_index(op.f('ix_trade_journals_strategy_id'), table_name='trade_journals')
    op.drop_index(op.f('ix_trade_journals_user_id'), table_name='trade_journals')
    op.drop_table('trade_journals')

    op.drop_index(op.f('ix_watchlist_items_strategy_id'), table_name='watchlist_items')
    op.drop_index(op.f('ix_watchlist_items_user_id'), table_name='watchlist_items')
    op.drop_table('watchlist_items')

    op.drop_index(op.f('ix_scan_results_grade'), table_name='scan_results')
    op.drop_index(op.f('ix_scan_results_stock_code'), table_name='scan_results')
    op.drop_index(op.f('ix_scan_results_strategy_id'), table_name='scan_results')
    op.drop_index(op.f('ix_scan_results_scan_run_id'), table_name='scan_results')
    op.drop_table('scan_results')

    op.drop_index(op.f('ix_scan_runs_strategy_id'), table_name='scan_runs')
    op.drop_table('scan_runs')

    op.drop_index(op.f('ix_sessions_expires_at'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_token_hash'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')
    op.drop_table('sessions')

    op.drop_index(op.f('ix_strategies_user_id'), table_name='strategies')
    op.drop_table('strategies')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
