"""daily price refresh fields and freeze fee

Revision ID: 0005
Revises: 0004
Create Date: 2025-03-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "flights",
        sa.Column("last_price_refresh_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(sa.text("UPDATE flights SET last_price_refresh_at = timezone('utc', now())"))

    op.add_column(
        "freezes",
        sa.Column("freeze_fee_paid", sa.Float(), nullable=False, server_default="30"),
    )
    op.alter_column("freezes", "freeze_fee_paid", server_default=None)


def downgrade() -> None:
    op.drop_column("freezes", "freeze_fee_paid")
    op.drop_column("flights", "last_price_refresh_at")
