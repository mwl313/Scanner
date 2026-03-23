"""add total_target to scan_runs

Revision ID: 0007_scan_run_total_target
Revises: 0006_stock_daily_bar_cache
Create Date: 2026-03-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007_scan_run_total_target'
down_revision: Union[str, None] = '0006_stock_daily_bar_cache'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'scan_runs',
        sa.Column('total_target', sa.Integer(), nullable=False, server_default='0'),
    )
    op.alter_column('scan_runs', 'total_target', server_default=None)


def downgrade() -> None:
    op.drop_column('scan_runs', 'total_target')
