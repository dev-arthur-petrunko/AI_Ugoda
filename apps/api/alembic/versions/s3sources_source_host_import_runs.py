"""S3.3: source_host on document_revisions + import_runs table.

Revision ID: s3sources
Revises: s3dataorigin
Create Date: 2026-11-05
"""

import sqlalchemy as sa

from alembic import op

revision = "s3sources"
down_revision = "s3dataorigin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document_revisions",
        sa.Column("source_host", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "ix_document_revisions_source_host",
        "document_revisions",
        ["source_host"],
    )
    op.create_table(
        "import_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("added", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("report_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_import_runs_status", "import_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_import_runs_status", table_name="import_runs")
    op.drop_table("import_runs")
    op.drop_index("ix_document_revisions_source_host", table_name="document_revisions")
    op.drop_column("document_revisions", "source_host")
