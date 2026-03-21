"""flight.stops + search_history

Revision ID: 0003
Revises: 0002
Create Date: 2025-03-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "flights",
        sa.Column("stops", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("flights", "stops", server_default=None)
    op.execute(sa.text("UPDATE flights SET stops = 1 WHERE id % 2 = 0"))

    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("from_city", sa.String(length=128), nullable=False),
        sa.Column("to_city", sa.String(length=128), nullable=False),
        sa.Column("flight_date", sa.Date(), nullable=False),
        sa.Column("passengers", sa.Integer(), nullable=False),
        sa.Column("sort_by", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.String(length=4), nullable=False),
        sa.Column("max_price", sa.Float(), nullable=True),
        sa.Column("max_stops", sa.Integer(), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_search_history_user_id"), "search_history", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_search_history_user_id"), table_name="search_history")
    op.drop_table("search_history")
    op.drop_column("flights", "stops")
