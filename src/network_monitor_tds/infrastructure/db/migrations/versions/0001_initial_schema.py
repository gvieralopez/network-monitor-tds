"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-03 23:34:47.106489
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("mac", sa.String(length=17), nullable=False),
        sa.Column("ip", sa.String(length=15), nullable=True),
        sa.Column("first_seen", sa.DateTime(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=False),
        sa.Column("acknowledged", sa.Boolean(), nullable=False),
        sa.Column("label_name", sa.String(length=100), nullable=True),
        sa.Column("label_category", sa.String(length=20), nullable=True),
        sa.Column("label_icon", sa.String(length=40), nullable=True),
        sa.PrimaryKeyConstraint("mac", name=op.f("pk_devices")),
    )
    with op.batch_alter_table("devices", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_devices_last_seen"), ["last_seen"], unique=False)

    op.create_table(
        "plugin_configs",
        sa.Column("plugin_id", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("plugin_id", name=op.f("pk_plugin_configs")),
    )
    op.create_table(
        "detections",
        sa.Column("mac", sa.String(length=17), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("first_seen", sa.DateTime(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["mac"], ["devices.mac"], name=op.f("fk_detections_mac_devices"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("mac", "source", name=op.f("pk_detections")),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("mac", sa.String(length=17), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["mac"], ["devices.mac"], name=op.f("fk_events_mac_devices"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
    )
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_events_occurred_at"), ["occurred_at"], unique=False)

    op.create_table(
        "facts",
        sa.Column("mac", sa.String(length=17), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["mac"], ["devices.mac"], name=op.f("fk_facts_mac_devices"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("mac", "name", name=op.f("pk_facts")),
    )
    op.create_table(
        "presence",
        sa.Column("mac", sa.String(length=17), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["mac"], ["devices.mac"], name=op.f("fk_presence_mac_devices"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("mac", name=op.f("pk_presence")),
    )
    op.create_table(
        "presence_intervals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mac", sa.String(length=17), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["mac"],
            ["devices.mac"],
            name=op.f("fk_presence_intervals_mac_devices"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_presence_intervals")),
    )
    with op.batch_alter_table("presence_intervals", schema=None) as batch_op:
        batch_op.create_index(
            "ix_presence_intervals_mac_started_at", ["mac", "started_at"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("presence_intervals", schema=None) as batch_op:
        batch_op.drop_index("ix_presence_intervals_mac_started_at")

    op.drop_table("presence_intervals")
    op.drop_table("presence")
    op.drop_table("facts")
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_events_occurred_at"))

    op.drop_table("events")
    op.drop_table("detections")
    op.drop_table("plugin_configs")
    with op.batch_alter_table("devices", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_devices_last_seen"))

    op.drop_table("devices")
