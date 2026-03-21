"""initial schema and seed mock flights

Revision ID: 0001
Revises:
Create Date: 2025-03-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "flights",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("from_city", sa.String(length=128), nullable=False),
        sa.Column("to_city", sa.String(length=128), nullable=False),
        sa.Column("departure_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("arrival_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_flights_from_city"), "flights", ["from_city"], unique=False)
    op.create_index(op.f("ix_flights_to_city"), "flights", ["to_city"], unique=False)

    op.create_table(
        "freezes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("flight_id", sa.Integer(), nullable=False),
        sa.Column("frozen_price", sa.Float(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["flight_id"], ["flights.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_freezes_flight_id"), "freezes", ["flight_id"], unique=False)
    op.create_index(op.f("ix_freezes_user_id"), "freezes", ["user_id"], unique=False)

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("flight_id", sa.Integer(), nullable=False),
        sa.Column("price_paid", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["flight_id"], ["flights.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bookings_flight_id"), "bookings", ["flight_id"], unique=False)
    op.create_index(op.f("ix_bookings_user_id"), "bookings", ["user_id"], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO flights (from_city, to_city, departure_time, arrival_time, price)
            VALUES
            (
                'Moscow',
                'Berlin',
                (timezone('utc', now()) + interval '3 days')::timestamptz,
                (timezone('utc', now()) + interval '3 days' + interval '3 hours')::timestamptz,
                189.5
            ),
            (
                'Moscow',
                'Berlin',
                (timezone('utc', now()) + interval '3 days' + interval '8 hours')::timestamptz,
                (timezone('utc', now()) + interval '3 days' + interval '11 hours')::timestamptz,
                215.0
            ),
            (
                'Saint Petersburg',
                'Paris',
                (timezone('utc', now()) + interval '5 days')::timestamptz,
                (timezone('utc', now()) + interval '5 days' + interval '4 hours')::timestamptz,
                320.75
            ),
            (
                'Moscow',
                'Dubai',
                (timezone('utc', now()) + interval '7 days')::timestamptz,
                (timezone('utc', now()) + interval '7 days' + interval '5 hours')::timestamptz,
                410.0
            ),
            (
                'Moscow',
                'Istanbul',
                (timezone('utc', now()) + interval '10 days')::timestamptz,
                (timezone('utc', now()) + interval '10 days' + interval '2 hours 30 minutes')::timestamptz,
                175.25
            );
            """
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_bookings_user_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_flight_id"), table_name="bookings")
    op.drop_table("bookings")
    op.drop_index(op.f("ix_freezes_user_id"), table_name="freezes")
    op.drop_index(op.f("ix_freezes_flight_id"), table_name="freezes")
    op.drop_table("freezes")
    op.drop_index(op.f("ix_flights_to_city"), table_name="flights")
    op.drop_index(op.f("ix_flights_from_city"), table_name="flights")
    op.drop_table("flights")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
