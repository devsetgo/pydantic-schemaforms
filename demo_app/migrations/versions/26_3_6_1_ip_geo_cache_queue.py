"""26.3.6.1

Revision ID: 26_3_6_1
Revises: 
Create Date: 2026-03-07

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "26_3_6_1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ip_geo_cache",
        sa.Column("ip", sa.Text(), primary_key=True),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("fetched_at", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column("country_code", sa.Text(), nullable=True),
        sa.Column("region", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
        sa.Column("raw_json", sa.Text(), nullable=False),
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index("idx_ip_geo_cache_expires_at", "ip_geo_cache", ["expires_at"])

    op.create_table(
        "ip_geo_queue",
        sa.Column("ip", sa.Text(), primary_key=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.Text(), nullable=False),
        sa.Column("locked_by", sa.Text(), nullable=True),
        sa.Column("locked_until", sa.Text(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_ip_geo_queue_status_next_attempt_at",
        "ip_geo_queue",
        ["status", "next_attempt_at"],
    )

    # Single leader lock so only one FastAPI/Uvicorn worker performs lookups.
    op.create_table(
        "ip_geo_leader_lock",
        sa.Column("lock_key", sa.Text(), primary_key=True),
        sa.Column("locked_by", sa.Text(), nullable=False),
        sa.Column("locked_until", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ip_geo_leader_lock")
    op.drop_index("idx_ip_geo_queue_status_next_attempt_at", table_name="ip_geo_queue")
    op.drop_table("ip_geo_queue")
    op.drop_index("idx_ip_geo_cache_expires_at", table_name="ip_geo_cache")
    op.drop_table("ip_geo_cache")
