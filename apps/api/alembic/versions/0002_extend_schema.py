"""Extend schema for AI Ugoda TZ v2

Revision ID: 0002_extend_schema
Revises: 0001_initial_schema
Create Date: 2026-10-23 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_extend_schema"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # legal_force_levels — довідник рівнів юридичної сили
    op.create_table(
        "legal_force_levels",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, unique=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority_weight", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_legal_force_levels_level"), "legal_force_levels", ["level"], unique=True)

    # legal_documents: додаємо поля nreg, legal_force_level, is_temporary, valid_until_condition
    op.add_column("legal_documents", sa.Column("nreg", sa.String(length=100), nullable=True))
    op.add_column("legal_documents", sa.Column("legal_force_level", sa.String(length=40), nullable=True))
    op.add_column("legal_documents", sa.Column("is_temporary", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("legal_documents", sa.Column("valid_until_condition", sa.String(length=500), nullable=True))

    # document_revisions: effective_from/effective_to, source_hash
    op.add_column("document_revisions", sa.Column("effective_from", sa.Date(), nullable=True))
    op.add_column("document_revisions", sa.Column("effective_to", sa.Date(), nullable=True))
    op.add_column("document_revisions", sa.Column("source_hash", sa.String(length=128), nullable=True))
    op.create_index(op.f("ix_document_revisions_effective_from"), "document_revisions", ["effective_from"])
    op.create_index(op.f("ix_document_revisions_effective_to"), "document_revisions", ["effective_to"])

    # legal_provisions: адреса норми (article/part/point/subpoint)
    op.add_column("legal_provisions", sa.Column("article_number", sa.String(length=50), nullable=True))
    op.add_column("legal_provisions", sa.Column("part_number", sa.String(length=50), nullable=True))
    op.add_column("legal_provisions", sa.Column("point_number", sa.String(length=50), nullable=True))
    op.add_column("legal_provisions", sa.Column("subpoint_number", sa.String(length=50), nullable=True))
    op.create_index(op.f("ix_legal_documents_nreg"), "legal_documents", ["nreg"])

    # legal_links — зв'язки між положеннями/актами
    op.create_table(
        "legal_links",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("source_provision_id", sa.String(36), nullable=False),
        sa.Column("target_provision_id", sa.String(36), nullable=True, index=True),
        sa.Column("target_document_id", sa.String(36), nullable=True, index=True),
        sa.Column("link_type", sa.String(length=60), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False, server_default=sa.text("'source_to_target'")),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("resolution_status", sa.String(length=40), nullable=False, server_default=sa.text("'unresolved'")),
        sa.Column("source_meta_json", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["source_provision_id"], ["legal_provisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_provision_id"], ["legal_provisions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_document_id"], ["legal_documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_legal_links_source_provision_id"), "legal_links", ["source_provision_id"])
    op.create_index(op.f("ix_legal_links_link_type"), "legal_links", ["link_type"])

    # conflict_candidates: додаємо rule_applied, winner_provision_id, explanation
    op.add_column("conflict_candidates", sa.Column("rule_applied", sa.String(length=100), nullable=True))
    op.add_column("conflict_candidates", sa.Column("winner_provision_id", sa.String(36), nullable=True, index=True))
    op.add_column("conflict_candidates", sa.Column("explanation", sa.Text(), nullable=True))
    op.create_foreign_key("fk_conflict_candidates_winner_provision", "conflict_candidates", "legal_provisions", ["winner_provision_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_conflict_candidates_winner_provision", "conflict_candidates", type_="foreignkey")
    op.drop_column("conflict_candidates", "explanation")
    op.drop_column("conflict_candidates", "winner_provision_id")
    op.drop_column("conflict_candidates", "rule_applied")
    op.drop_table("legal_links")
    op.drop_column("legal_provisions", "subpoint_number")
    op.drop_column("legal_provisions", "point_number")
    op.drop_column("legal_provisions", "part_number")
    op.drop_column("legal_provisions", "article_number")
    op.drop_index(op.f("ix_document_revisions_effective_to"), table_name="document_revisions")
    op.drop_index(op.f("ix_document_revisions_effective_from"), table_name="document_revisions")
    op.drop_column("document_revisions", "source_hash")
    op.drop_column("document_revisions", "effective_to")
    op.drop_column("document_revisions", "effective_from")
    op.drop_index(op.f("ix_legal_documents_nreg"), table_name="legal_documents")
    op.drop_column("legal_documents", "valid_until_condition")
    op.drop_column("legal_documents", "is_temporary")
    op.drop_column("legal_documents", "legal_force_level")
    op.drop_column("legal_documents", "nreg")
    op.drop_index(op.f("ix_legal_force_levels_level"), table_name="legal_force_levels")
    op.drop_table("legal_force_levels")