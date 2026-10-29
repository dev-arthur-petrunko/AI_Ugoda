import sys
sys.path.insert(0, 'apps/api')
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT version_num FROM alembic_version"))
    print("Alembic version:", result.fetchone())
    
    # Check Ukrainian FTS config
    result2 = conn.execute(text("SELECT cfgname FROM pg_ts_config WHERE cfgname = 'ukrainian'"))
    print("Ukrainian config exists:", result2.fetchone() is not None)
    
    # Check hunspell dictionary
    result3 = conn.execute(text("SELECT dictname FROM pg_ts_dict WHERE dictname = 'ukrainian_hunspell'"))
    print("Hunspell dictionary exists:", result3.fetchone() is not None)
