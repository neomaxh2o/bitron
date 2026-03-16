#!/usr/bin/env python3
import sqlite3, pathlib

# Path to database (correct relative to this script)
DB_DIR = pathlib.Path(__file__).resolve().parents[1] / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "bitron_memory.db"

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()
# Check if 'details' column already exists
cur.execute("PRAGMA table_info(deploy_steps);")
columns = [row[1] for row in cur.fetchall()]
if "details" not in columns:
    cur.execute("ALTER TABLE deploy_steps ADD COLUMN details TEXT;")
    conn.commit()
    print("Column 'details' added to deploy_steps.")
else:
    print("Column 'details' already present.")
conn.close()
