"""Initial AI Ugoda schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-23 00:00:00.000000

"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("locale", sa.String(length=10), nullable=False, server_default=sa.text("'uk'")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "legal_documents",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("official_identifier", sa.String(length=200), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=True),
        sa.Column("document_number", sa.String(length=100), nullable=True),
        sa.Column("adoption_date", sa.Date(), nullable=True),
        sa.Column("issuing_authority", sa.String(length=200), nullable=True),
        sa.Column(
            "current_known_status",
            sa.String(length=60),
            nullable=False,
            server_default=sa.text("'Статус потребує перевірки'"),
        ),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_metadata_json", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_legal_documents_source_id"), "legal_documents", ["source_id"], unique=True)
    op.create_index(op.f("ix_legal_documents_document_number"), "legal_documents", ["document_number"])
    op.create_index(op.f("ix_legal_documents_current_known_status"), "legal_documents", ["current_known_status"])
    op.create_index("ix_legal_documents_title_trgm", "legal_documents", ["title"], postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"})

    op.create_table(
        "document_revisions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("legal_document_id", sa.String(36), nullable=False),
        sa.Column("revision_label", sa.String(length=100), nullable=True),
        sa.Column("revision_date", sa.Date(), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_checksum", sa.String(length=128), nullable=True),
        sa.Column("original_content_location", sa.Text(), nullable=True),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("parser_version", sa.String(length=40), nullable=True),
        sa.Column("imported_at", sa.Date(), nullable=True),
        sa.Column("verification_status", sa.String(length=40), nullable=False, server_default=sa.text("'unverified'")),
        sa.ForeignKeyConstraint(["legal_document_id"], ["legal_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_revisions_legal_document_id"), "document_revisions", ["legal_document_id"])
    op.create_index(op.f("ix_document_revisions_revision_date"), "document_revisions", ["revision_date"])

    op.create_table(
        "legal_provisions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("document_revision_id", sa.String(36), nullable=False),
        sa.Column("provision_identifier", sa.String(length=100), nullable=False),
        sa.Column("parent_provision_id", sa.String(36), nullable=True),
        sa.Column("heading", sa.String(length=500), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("ordinal", sa.Integer(), nullable=True),
        sa.Column("content_checksum", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["document_revision_id"], ["document_revisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_provision_id"], ["legal_provisions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_legal_provisions_document_revision_id"), "legal_provisions", ["document_revision_id"])
    op.create_index(op.f("ix_legal_provisions_provision_identifier"), "legal_provisions", ["provision_identifier"])

    op.create_table(
        "legal_events",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("source_document_id", sa.String(36), nullable=True),
        sa.Column("affected_document_id", sa.String(36), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("source_event_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("discovered_at", sa.Date(), nullable=True),
        sa.Column("old_revision_id", sa.String(36), nullable=True),
        sa.Column("new_revision_id", sa.String(36), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("processing_status", sa.String(length=40), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("ai_summary_status", sa.String(length=40), nullable=False, server_default=sa.text("'pending'")),
        sa.ForeignKeyConstraint(["affected_document_id"], ["legal_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["old_revision_id"], ["document_revisions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["new_revision_id"], ["document_revisions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_legal_events_affected_document_id"), "legal_events", ["affected_document_id"])
    op.create_index(op.f("ix_legal_events_event_type"), "legal_events", ["event_type"])

    op.create_table(
        "legal_references",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("source_provision_id", sa.String(36), nullable=False),
        sa.Column("target_document_id", sa.String(36), nullable=True),
        sa.Column("target_provision_identifier", sa.String(length=200), nullable=True),
        sa.Column("reference_type", sa.String(length=80), nullable=False),
        sa.Column("resolution_status", sa.String(length=40), nullable=False, server_default=sa.text("'unresolved'")),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["source_provision_id"], ["legal_provisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_document_id"], ["legal_documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_legal_references_source_provision_id"), "legal_references", ["source_provision_id"])

    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("analysis_type", sa.String(length=80), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("model_provider", sa.String(length=60), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=60), nullable=True),
        sa.Column("source_revision_ids", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("structured_result_json", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("analysis_status", sa.String(length=40), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_analyses_analysis_type"), "ai_analyses", ["analysis_type"])
    op.create_index(op.f("ix_ai_analyses_target_id"), "ai_analyses", ["target_id"])

    op.create_table(
        "conflict_candidates",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("provision_a_id", sa.String(36), nullable=False),
        sa.Column("provision_b_id", sa.String(36), nullable=False),
        sa.Column("conflict_type", sa.String(length=100), nullable=False),
        sa.Column("evidence_json", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("confidence", sa.String(length=40), nullable=False, server_default=sa.text("'low'")),
        sa.Column("review_status", sa.String(length=60), nullable=False, server_default=sa.text("'Не підтверджено'")),
        sa.ForeignKeyConstraint(["provision_a_id"], ["legal_provisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["provision_b_id"], ["legal_provisions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conflict_candidates_provision_a_id"), "conflict_candidates", ["provision_a_id"])
    op.create_index(op.f("ix_conflict_candidates_provision_b_id"), "conflict_candidates", ["provision_b_id"])

    op.create_table(
        "user_monitoring_rules",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("rule_type", sa.String(length=60), nullable=False),
        sa.Column("rule_configuration", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("delivery_preferences", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_notified_at", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_monitoring_rules_user_id"), "user_monitoring_rules", ["user_id"])

    op.create_table(
        "user_bookmarks",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("document_id", sa.String(36), nullable=False),
        sa.Column("provision_identifier", sa.String(length=200), nullable=True),
        sa.Column("note", sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["legal_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_bookmarks_user_id"), "user_bookmarks", ["user_id"])
    op.create_index(op.f("ix_user_bookmarks_document_id"), "user_bookmarks", ["document_id"])

    op.create_table(
        "contract_documents",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("secure_storage_key", sa.String(length=200), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("file_metadata", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("processing_status", sa.String(length=40), nullable=False, server_default=sa.text("'uploaded'")),
        sa.Column("retention_policy", sa.String(length=60), nullable=False, server_default=sa.text("'configurable'")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("secure_storage_key"),
    )
    op.create_index(op.f("ix_contract_documents_owner_id"), "contract_documents", ["owner_id"])

    op.create_table(
        "contract_analyses",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("contract_document_id", sa.String(36), nullable=False),
        sa.Column("analysis_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("source_revision_ids", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("structured_result_json", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("model_metadata", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["contract_document_id"], ["contract_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contract_analyses_contract_document_id"), "contract_analyses", ["contract_document_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=True),
        sa.Column("target_id", sa.String(36), nullable=True),
        sa.Column("metadata_json", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_actor_id"), "audit_logs", ["actor_id"])
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("contract_analyses")
    op.drop_table("contract_documents")
    op.drop_table("user_bookmarks")
    op.drop_table("user_monitoring_rules")
    op.drop_table("conflict_candidates")
    op.drop_table("ai_analyses")
    op.drop_table("legal_references")
    op.drop_table("legal_events")
    op.drop_table("legal_provisions")
    op.drop_table("document_revisions")
    op.drop_index(op.f("ix_legal_documents_title_trgm"), table_name="legal_documents")
    op.drop_index(op.f("ix_legal_documents_current_known_status"), table_name="legal_documents")
    op.drop_index(op.f("ix_legal_documents_document_number"), table_name="legal_documents")
    op.drop_index(op.f("ix_legal_documents_source_id"), table_name="legal_documents")
    op.drop_table("legal_documents")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")