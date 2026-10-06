import sqlite3, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import settings
REQUIRED={'students','courses','attendance','results','rule_registry','source_register'}
with sqlite3.connect(settings.sqlite_path) as conn:
    actual={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert REQUIRED <= actual, f'Missing tables: {REQUIRED-actual}'
    assert conn.execute('SELECT COUNT(*) FROM students').fetchone()[0] > 0
print('Data validation passed')
