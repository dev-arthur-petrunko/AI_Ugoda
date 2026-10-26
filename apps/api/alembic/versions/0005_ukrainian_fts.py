"""Switch FTS to Ukrainian Hunspell config (Stage 6)."""
from __future__ import annotations

from alembic import op

revision = "0005_ukrainian_fts"
down_revision = "0004_unique_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure dictionary/config exist (idempotent) for volumes created before init script.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_ts_dict WHERE dictname = 'ukrainian_hunspell') THEN
                CREATE TEXT SEARCH DICTIONARY ukrainian_hunspell (
                    TEMPLATE = ispell,
                    DictFile = uk_UA,
                    AffFile = uk_UA
                );
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'ukrainian') THEN
                CREATE TEXT SEARCH CONFIGURATION ukrainian (COPY = simple);
            END IF;
        END
        $$;
        """
    )
    op.execute(
        "ALTER TEXT SEARCH CONFIGURATION ukrainian "
        "ALTER MAPPING FOR word, hword, hword_part, hword_numpart WITH ukrainian_hunspell;"
    )

    # Rebuild search_vector generated column with ukrainian config.
    op.execute("DROP INDEX IF EXISTS ix_legal_provisions_search_vector")
    op.execute("ALTER TABLE legal_provisions DROP COLUMN IF EXISTS search_vector")
    op.execute(
        """
        ALTER TABLE legal_provisions
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (to_tsvector('ukrainian', coalesce(heading, '') || ' ' || coalesce(text, ''))) STORED
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_legal_provisions_search_vector "
        "ON legal_provisions USING gin (search_vector)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_legal_provisions_search_vector")
    op.execute("ALTER TABLE legal_provisions DROP COLUMN IF EXISTS search_vector")
    op.execute(
        """
        ALTER TABLE legal_provisions
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (to_tsvector('simple', coalesce(heading, '') || ' ' || coalesce(text, ''))) STORED
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_legal_provisions_search_vector "
        "ON legal_provisions USING gin (search_vector)"
    )
