"""
Database schema migration script for eRTMAC-NWIS SQLite/PostgreSQL database.
Safely adds Phase 2 columns to existing tables without data loss.
"""

import sqlite3
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.db.database import Base, engine
import backend.app.db.models

def migrate_sqlite():
    db_path = ROOT_DIR / "data" / "processed" / "nwis_local.db"
    if not db_path.exists():
        print("Database file does not exist yet. Running create_all...")
        Base.metadata.create_all(bind=engine)
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(drilling_events)")
    existing_cols = [row[1] for row in cur.fetchall()]

    new_cols = [
        ("verification_status", "TEXT DEFAULT 'VERIFIED'"),
        ("doc_id", "TEXT"),
        ("page_number", "INTEGER"),
        ("source_availability_timestamp", "TEXT"),
        ("extraction_method", "TEXT DEFAULT 'STRUCTURED_INGESTION'"),
        ("confidence_score", "REAL DEFAULT 1.0"),
        ("reviewed_by", "TEXT"),
        ("reviewed_at", "TEXT")
    ]

    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            print(f"Adding column '{col_name}' ({col_type}) to 'drilling_events'...")
            cur.execute(f"ALTER TABLE drilling_events ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()

    # Create any missing new tables
    Base.metadata.create_all(bind=engine)
    print("Database migration completed successfully.")

if __name__ == "__main__":
    migrate_sqlite()
