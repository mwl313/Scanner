"""Rename foreign investor value columns to quantity-oriented names

Revision ID: 0008_foreign_qty_naming_refactor
Revises: 0007_scan_run_total_target
Create Date: 2026-03-23 20:10:00
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '0008_foreign_qty_naming_refactor'
down_revision = '0007_scan_run_total_target'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('foreign_investor_daily', 'net_buy_value', new_column_name='net_buy_qty')
    op.alter_column('scan_results', 'foreign_net_buy_value', new_column_name='foreign_net_buy_qty')
    op.alter_column(
        'scan_results',
        'foreign_net_buy_confirmed_value',
        new_column_name='foreign_net_buy_confirmed_qty',
    )
    op.alter_column(
        'scan_results',
        'foreign_net_buy_snapshot_value',
        new_column_name='foreign_net_buy_snapshot_qty',
    )


def downgrade() -> None:
    op.alter_column(
        'scan_results',
        'foreign_net_buy_snapshot_qty',
        new_column_name='foreign_net_buy_snapshot_value',
    )
    op.alter_column(
        'scan_results',
        'foreign_net_buy_confirmed_qty',
        new_column_name='foreign_net_buy_confirmed_value',
    )
    op.alter_column('scan_results', 'foreign_net_buy_qty', new_column_name='foreign_net_buy_value')
    op.alter_column('foreign_investor_daily', 'net_buy_qty', new_column_name='net_buy_value')
