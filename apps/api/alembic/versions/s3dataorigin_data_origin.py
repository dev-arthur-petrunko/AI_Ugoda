"""S3.2: data_origin column on legal_documents (official | fixture).

Revision ID: s3dataorigin
Revises: 516775f2e1d9
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op

revision = "s3dataorigin"
down_revision = "516775f2e1d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "legal_documents",
        sa.Column(
            "data_origin",
            sa.String(length=20),
            nullable=False,
            server_default="fixture",
        ),
    )
    op.create_index(
        "ix_legal_documents_data_origin",
        "legal_documents",
        ["data_origin"],
    )


def downgrade() -> None:
    op.drop_index("ix_legal_documents_data_origin", table_name="legal_documents")
    op.drop_column("legal_documents", "data_origin")
