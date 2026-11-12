"""§4.3: джерело зміни в legal_events (стаття + акт-джерело з примітки).

Revision ID: s4changenotes
Revises: s3revcontent
Create Date: 2026-11-12
"""

import sqlalchemy as sa

from alembic import op

revision = "s4changenotes"
down_revision = "s3revcontent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "legal_events",
        sa.Column("source_provision", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "legal_events",
        sa.Column("source_act_ref", sa.String(length=120), nullable=True),
    )
    op.create_index(
        "ix_legal_events_source_provision", "legal_events", ["source_provision"]
    )
    op.create_index(
        "ix_legal_events_source_act_ref", "legal_events", ["source_act_ref"]
    )


def downgrade() -> None:
    op.drop_index("ix_legal_events_source_act_ref", table_name="legal_events")
    op.drop_index("ix_legal_events_source_provision", table_name="legal_events")
    op.drop_column("legal_events", "source_act_ref")
    op.drop_column("legal_events", "source_provision")
