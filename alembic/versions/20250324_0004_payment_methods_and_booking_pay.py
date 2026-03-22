"""payment_methods, booking paid_at / payment_method_id

Revision ID: 0004
Revises: 0003
Create Date: 2025-03-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_methods",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False, server_default="Карта"),
        sa.Column("last_four", sa.String(length=4), nullable=False),
        sa.Column("holder_name", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_methods_user_id"), "payment_methods", ["user_id"], unique=False)
    op.alter_column("payment_methods", "label", server_default=None)

    op.add_column("bookings", sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bookings", sa.Column("payment_method_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_bookings_payment_method_id_payment_methods",
        "bookings",
        "payment_methods",
        ["payment_method_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute(sa.text("UPDATE bookings SET paid_at = created_at WHERE paid_at IS NULL"))


def downgrade() -> None:
    op.drop_constraint("fk_bookings_payment_method_id_payment_methods", "bookings", type_="foreignkey")
    op.drop_column("bookings", "payment_method_id")
    op.drop_column("bookings", "paid_at")
    op.drop_index(op.f("ix_payment_methods_user_id"), table_name="payment_methods")
    op.drop_table("payment_methods")
