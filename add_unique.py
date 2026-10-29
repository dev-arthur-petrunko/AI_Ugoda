import sys
sys.path.insert(0, 'apps/api')
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Find and show duplicate revisions
    dups = conn.execute(text("""
        SELECT legal_document_id, source_hash, count(*) as cnt
        FROM document_revisions
        GROUP BY legal_document_id, source_hash
        HAVING count(*) > 1
    """)).fetchall()
    
    print(f"Found {len(dups)} duplicate (legal_document_id, source_hash) groups:")
    for d in dups:
        print(f"  doc={d[0]}, hash={d[1]}, count={d[2]}")
    
    if dups:
        # Delete duplicates, keeping the one with the smallest id
        conn.execute(text("""
            DELETE FROM document_revisions
            WHERE id NOT IN (
                SELECT DISTINCT ON (legal_document_id, source_hash) id
                FROM document_revisions
                ORDER BY legal_document_id, source_hash, id
            )
        """))
        conn.commit()
        print(f"\nDeleted duplicate revisions, keeping one per (legal_document_id, source_hash)")

    # Now add UNIQUE constraint on document_revisions(legal_document_id, source_hash)
    try:
        conn.execute(text("ALTER TABLE document_revisions ADD CONSTRAINT uq_revision_doc_source_hash UNIQUE (legal_document_id, source_hash)"))
        print("OK: Added uq_revision_doc_source_hash UNIQUE constraint")
    except Exception as e:
        print(f"WARN: uq_revision_doc_source_hash: {e}")

    # Add UNIQUE constraint on legal_provisions(document_revision_id, provision_identifier)
    try:
        conn.execute(text("ALTER TABLE legal_provisions ADD CONSTRAINT uq_provision_revision_ident UNIQUE (document_revision_id, provision_identifier)"))
        print("OK: Added uq_provision_revision_ident UNIQUE constraint")
    except Exception as e:
        print(f"WARN: uq_provision_revision_ident: {e}")

    conn.commit()
    print("\nOK: All UNIQUE constraints committed")

    # Verify
    result = conn.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE indexname LIKE 'uq_%'"))
    print("\n=== UNIQUE constraints in database ===")
    for r in result:
        print(r)

