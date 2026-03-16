#!/usr/bin/env python3
import os, pathlib, sqlite3, datetime, shutil

BASE_DIR = pathlib.Path(__file__).resolve().parent
DB_DIR = BASE_DIR.parent / "db"
BACKUP_DIR = BASE_DIR.parent.parent.parent / "backups"  # memory/backups
DB_PATH = DB_DIR / "bitron_memory.db"

# Create directories if not exist
DB_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Backup existing DB
if DB_PATH.exists():
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"bitron_memory_{timestamp}.db"
    shutil.copy2(DB_PATH, backup_path)
    print(f"Backup {backup_path} created")

# Connect & create tables
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# General tables
c.execute("""
CREATE TABLE IF NOT EXISTS deploy_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    deploy_name TEXT NOT NULL,
    start_time TEXT NOT NULL,
    status TEXT NOT NULL,
    details TEXT
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS deploy_steps (
    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    status TEXT NOT NULL,
    output TEXT,
    FOREIGN KEY(run_id) REFERENCES deploy_runs(run_id)
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS deploy_errors (
    error_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    step_id INTEGER,
    error_msg TEXT NOT NULL,
    error_time TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES deploy_runs(run_id),
    FOREIGN KEY(step_id) REFERENCES deploy_steps(step_id)
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS system_artifacts (
    artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    artifact_path TEXT NOT NULL,
    artifact_type TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES deploy_runs(run_id)
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS semantic_memory (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    category TEXT,
    summary TEXT,
    source TEXT,
    created_at TEXT NOT NULL
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS semantic_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entry INTEGER NOT NULL,
    to_entry INTEGER NOT NULL,
    relation TEXT,
    FOREIGN KEY(from_entry) REFERENCES semantic_memory(entry_id),
    FOREIGN KEY(to_entry) REFERENCES semantic_memory(entry_id)
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS execution_memory (
    exec_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_time TEXT NOT NULL,
    details TEXT,
    status TEXT,
    FOREIGN KEY(run_id) REFERENCES deploy_runs(run_id)
);
""")

# Índices
c.execute("CREATE INDEX IF NOT EXISTS idx_deploy_runs_status ON deploy_runs(status);")
c.execute("CREATE INDEX IF NOT EXISTS idx_deploy_steps_run_id ON deploy_steps(run_id);")
c.execute("CREATE INDEX IF NOT EXISTS idx_deploy_errors_run_id ON deploy_errors(run_id);")
c.execute("CREATE INDEX IF NOT EXISTS idx_semantic_topic ON semantic_memory(topic);")
c.execute("CREATE INDEX IF NOT EXISTS idx_semantic_category ON semantic_memory(category);")
c.execute("CREATE INDEX IF NOT EXISTS idx_execution_event_type ON execution_memory(event_type);")

conn.commit()
conn.close()
print("Database initialized at", DB_PATH)
