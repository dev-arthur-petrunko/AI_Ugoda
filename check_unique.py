import sys
sys.path.insert(0, 'apps/api')
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'document_revisions' ORDER BY ordinal_position"))
    print("=== document_revisions columns ===")
    for r in result:
        print(r)

    result2 = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'legal_provisions' ORDER BY ordinal_position"))
    print("\n=== legal_provisions columns ===")
    for r in result2:
        print(r)

    result3 = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'legal_documents' ORDER BY ordinal_position"))
    print("\n=== legal_documents columns ===")
    for r in result3:
        print(r)


