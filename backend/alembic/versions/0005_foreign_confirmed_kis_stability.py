"""add foreign coverage/reason fields for scan results

Revision ID: 0005_foreign_kis_stability
Revises: 0004_strategy_scan_universe_limit
Create Date: 2026-03-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005_foreign_kis_stability'
down_revision: Union[str, None] = '0004_strategy_scan_limit'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scan_results', sa.Column('foreign_unavailable_reason', sa.String(length=40), nullable=True))
    op.add_column(
        'scan_results',
        sa.Column('foreign_coverage_days', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'scan_results',
        sa.Column('foreign_required_days', sa.Integer(), nullable=False, server_default='0'),
    )
    op.alter_column('scan_results', 'foreign_coverage_days', server_default=None)
    op.alter_column('scan_results', 'foreign_required_days', server_default=None)


def downgrade() -> None:
    op.drop_column('scan_results', 'foreign_required_days')
    op.drop_column('scan_results', 'foreign_coverage_days')
    op.drop_column('scan_results', 'foreign_unavailable_reason')
