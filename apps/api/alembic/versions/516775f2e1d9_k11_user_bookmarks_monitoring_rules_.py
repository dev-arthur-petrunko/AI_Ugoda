"""K11: user bookmarks, monitoring rules, contract documents

Revision ID: 516775f2e1d9
Revises: 0005_ukrainian_fts
Create Date: 2026-10-30 12:31:53.425047

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '516775f2e1d9'
down_revision: Union[str, None] = '0005_ukrainian_fts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user_bookmarks
    op.create_table(
        "user_bookmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("provision_identifier", sa.String(length=200), nullable=True),
        sa.Column("note", sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["legal_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_bookmarks_document_id"), "user_bookmarks", ["document_id"], unique=False)
    op.create_index(op.f("ix_user_bookmarks_user_id"), "user_bookmarks", ["user_id"], unique=False)

    # user_monitoring_rules
    op.create_table(
        "user_monitoring_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("rule_type", sa.String(length=60), nullable=False),
        sa.Column("rule_configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("delivery_preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_notified_at", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_monitoring_rules_user_id"), "user_monitoring_rules", ["user_id"], unique=False)

    # contract_documents
    op.create_table(
        "contract_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=True),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("secure_storage_key", sa.String(length=200), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("file_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("processing_status", sa.String(length=40), nullable=False, server_default="uploaded"),
        sa.Column("retention_policy", sa.String(length=60), nullable=False, server_default="configurable"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("secure_storage_key"),
    )
    op.create_index(op.f("ix_contract_documents_owner_id"), "contract_documents", ["owner_id"], unique=False)
    op.create_index(op.f("ix_contract_documents_workspace_id"), "contract_documents", ["workspace_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_contract_documents_workspace_id"), table_name="contract_documents")
    op.drop_index(op.f("ix_contract_documents_owner_id"), table_name="contract_documents")
    op.drop_table("contract_documents")
    op.drop_index(op.f("ix_user_monitoring_rules_user_id"), table_name="user_monitoring_rules")
    op.drop_table("user_monitoring_rules")
    op.drop_index(op.f("ix_user_bookmarks_user_id"), table_name="user_bookmarks")
    op.drop_index(op.f("ix_user_bookmarks_document_id"), table_name="user_bookmarks")
    op.drop_table("user_bookmarks")
