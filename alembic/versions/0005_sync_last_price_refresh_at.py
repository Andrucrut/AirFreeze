"""sync last_price_refresh_at column

Revision ID: 0005
Revises: 0004
Create Date: 2025-03-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('flights')]

    if 'last_price_refresh_at' not in existing_columns:
        op.add_column(
            'flights',
            sa.Column('last_price_refresh_at', sa.DateTime(timezone=True), nullable=True)
        )
        print("✅ Колонка last_price_refresh_at добавлена")
    else:
        print("⏭️ Колонка last_price_refresh_at уже существует, пропускаем")


def downgrade() -> None:
    op.drop_column('flights', 'last_price_refresh_at')