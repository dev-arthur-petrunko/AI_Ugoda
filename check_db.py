import sys
sys.path.insert(0, 'apps/api')
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Add UNIQUE constraint on legal_documents.nreg
    try:
        conn.execute(text("ALTER TABLE legal_documents ADD CONSTRAINT uq_legal_documents_nreg UNIQUE (nreg)"))
        conn.commit()
        print("OK: Added uq_legal_documents_nreg UNIQUE constraint")
    except Exception as e:
        print(f"WARN: uq_legal_documents_nreg: {e}")

    # Verify
    result = conn.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE indexname LIKE 'uq_%'"))
    print("\n=== UNIQUE constraints in database ===")
    for r in result:
        print(r)

