"""add strategy scan universe limit

Revision ID: 0004_strategy_scan_limit
Revises: 0003_strategy_schema_refactor
Create Date: 2026-03-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_strategy_scan_limit'
down_revision: Union[str, None] = '0003_strategy_schema_refactor'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'strategies',
        sa.Column('scan_universe_limit', sa.Integer(), nullable=False, server_default='300'),
    )
    op.execute('UPDATE strategies SET scan_universe_limit = 300 WHERE scan_universe_limit IS NULL')
    op.alter_column('strategies', 'scan_universe_limit', server_default=None)


def downgrade() -> None:
    op.drop_column('strategies', 'scan_universe_limit')
