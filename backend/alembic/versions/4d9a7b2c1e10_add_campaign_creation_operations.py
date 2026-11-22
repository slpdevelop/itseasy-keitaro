"""Add persistent campaign creation checkpoints.

Revision ID: 4d9a7b2c1e10
Revises: c091b71c4c41
Create Date: 2026-11-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4d9a7b2c1e10"
down_revision: str | Sequence[str] | None = "c091b71c4c41"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campaign_creation_operations",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("owner_token", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_campaign_creation_operations_updated_at",
        "campaign_creation_operations",
        ["updated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_campaign_creation_operations_updated_at",
        table_name="campaign_creation_operations",
    )
    op.drop_table("campaign_creation_operations")
