"""Add uniqueness constraints (Stage 6 / D11)."""
from __future__ import annotations

from alembic import op

revision = "0004_unique_constraints"
down_revision = "0003_pgvector_fts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Deduplicate legal_documents by nreg (keep lowest id) before adding constraint.
    op.execute(
        """
        DELETE FROM legal_documents a
        USING legal_documents b
        WHERE a.nreg IS NOT NULL AND a.nreg = b.nreg AND a.id > b.id
        """
    )
    op.create_unique_constraint(
        "uq_legal_documents_nreg", "legal_documents", ["nreg"]
    )
    # Deduplicate revisions by (legal_document_id, effective_from).
    op.execute(
        """
        DELETE FROM document_revisions a
        USING document_revisions b
        WHERE a.legal_document_id = b.legal_document_id
          AND a.effective_from IS NOT NULL AND a.effective_from = b.effective_from
          AND a.id > b.id
        """
    )
    op.create_unique_constraint(
        "uq_revision_doc_effective", "document_revisions",
        ["legal_document_id", "effective_from"],
    )
    # Deduplicate provisions by (document_revision_id, provision_identifier).
    op.execute(
        """
        DELETE FROM legal_provisions a
        USING legal_provisions b
        WHERE a.document_revision_id = b.document_revision_id
          AND a.provision_identifier = b.provision_identifier
          AND a.id > b.id
        """
    )
    op.create_unique_constraint(
        "uq_provision_revision_ident", "legal_provisions",
        ["document_revision_id", "provision_identifier"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_provision_revision_ident", "legal_provisions", type_="unique")
    op.drop_constraint("uq_revision_doc_effective", "document_revisions", type_="unique")
    op.drop_constraint("uq_legal_documents_nreg", "legal_documents", type_="unique")
