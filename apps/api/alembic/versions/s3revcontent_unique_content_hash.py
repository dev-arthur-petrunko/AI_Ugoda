"""S3.5: UNIQUE (document_id, content_sha256) — один вміст = одна редакція.

Revision ID: s3revcontent
Revises: s3sources
Create Date: 2026-11-07

content_sha256 реалізовано колонкою source_hash (SHA-256 нормалізованого тексту):
той самий текст під іншою датою не створює другу редакцію (див. правило S3.7).
Перевірено перед додаванням: дублів (legal_document_id, source_hash) у БД — 0.
"""

from alembic import op

revision = "s3revcontent"
down_revision = "s3sources"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_revision_doc_content",
        "document_revisions",
        ["legal_document_id", "source_hash"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_revision_doc_content", "document_revisions", type_="unique")
