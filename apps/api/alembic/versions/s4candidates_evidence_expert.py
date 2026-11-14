"""§6: чесні кандидати колізій — джерело виявлення + експертне рішення.

Revision ID: s4candidates
Revises: s4changenotes
Create Date: 2026-11-13
"""

import sqlalchemy as sa

from alembic import op

revision = "s4candidates"
down_revision = "s4changenotes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conflict_candidates",
        sa.Column(
            "source_of_detection",
            sa.String(length=40),
            nullable=False,
            server_default="code",
        ),
    )
    op.add_column(
        "conflict_candidates",
        sa.Column("reviewed_by", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "conflict_candidates",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Ідемпотентність: той самий тип + та сама пара норм — один кандидат.
    op.create_unique_constraint(
        "uq_conflict_candidates_pair",
        "conflict_candidates",
        ["provision_a_id", "provision_b_id", "conflict_type"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_conflict_candidates_pair", "conflict_candidates", type_="unique"
    )
    op.drop_column("conflict_candidates", "reviewed_at")
    op.drop_column("conflict_candidates", "reviewed_by")
    op.drop_column("conflict_candidates", "source_of_detection")
