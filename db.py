import os
from sqlalchemy import create_engine, text

_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///database.db")

if _DATABASE_URL.startswith("postgres://"):
    _DATABASE_URL = _DATABASE_URL.replace("postgres://", "postgresql://", 1)

_engine = create_engine(
    _DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in _DATABASE_URL else {},
    pool_pre_ping=True,
)

def get_conn():
    return _engine.connect()

def _pk():
    return "SERIAL" if "postgresql" in _DATABASE_URL else "INTEGER"

def init_db():
    pk = _pk()
    with _engine.connect() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS assets (
                id {pk} PRIMARY KEY,
                asset_type TEXT NOT NULL,
                serial_number TEXT,
                part_number TEXT,
                model_name TEXT,
                assigned_to TEXT,
                campus TEXT,
                issued_date TEXT,
                location TEXT,
                remarks TEXT,
                email_sent TEXT,
                acknowledgement TEXT,
                status TEXT DEFAULT 'Assigned',
                batch TEXT,
                ip_address TEXT,
                extension TEXT,
                credentials TEXT,
                created_at TEXT DEFAULT (CURRENT_TIMESTAMP)
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS handover (
                id {pk} PRIMARY KEY,
                date TEXT,
                employee_name TEXT,
                iqama TEXT,
                job_title TEXT,
                department TEXT,
                campus TEXT,
                asset_receipt_date TEXT,
                return_date TEXT,
                notes TEXT,
                item_name TEXT,
                model TEXT,
                serial TEXT,
                color TEXT,
                condition TEXT,
                accessories TEXT,
                created_at TEXT DEFAULT (CURRENT_TIMESTAMP)
            )
        """))
        conn.commit()

def is_seeded():
    with _engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM assets")).scalar()
        return result > 0

def rows_as_dicts(result):
    keys = result.keys()
    return [dict(zip(keys, row)) for row in result.fetchall()]