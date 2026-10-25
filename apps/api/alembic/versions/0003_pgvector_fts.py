"""Add pgvector + FTS support (Stage 5)."""
from __future__ import annotations

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision = "0003_pgvector_fts"
down_revision = "0002_extend_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.add_column("legal_provisions", sa.Column("embedding", Vector(1536), nullable=True))
    op.execute(
        """
        ALTER TABLE legal_provisions
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (to_tsvector('simple', coalesce(heading, '') || ' ' || coalesce(text, ''))) STORED
        """
    )
    op.create_index(
        "ix_legal_provisions_search_vector",
        "legal_provisions",
        ["search_vector"],
        postgresql_using="gin",
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_legal_provisions_embedding "
        "ON legal_provisions USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_legal_provisions_embedding")
    op.drop_index("ix_legal_provisions_search_vector", table_name="legal_provisions")
    op.drop_column("legal_provisions", "search_vector")
    op.drop_column("legal_provisions", "embedding")
