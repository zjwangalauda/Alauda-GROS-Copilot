"""SQLite database layer — WAL mode singleton."""

import os
import sqlite3
import threading

_lock = threading.Lock()
_connection: sqlite3.Connection | None = None

DEFAULT_DB_PATH = os.path.join("data", "recruitment.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS hc_requests (
    id TEXT PRIMARY KEY,
    date TEXT,
    department TEXT,
    role_title TEXT,
    location TEXT,
    urgency TEXT,
    mission TEXT,
    tech_stack TEXT,
    deal_breakers TEXT,
    selling_point TEXT,
    status TEXT DEFAULT 'Pending'
);

CREATE TABLE IF NOT EXISTS candidates (
    id TEXT PRIMARY KEY,
    name TEXT,
    role TEXT,
    hc_id TEXT,
    source TEXT,
    linkedin_url TEXT,
    stage TEXT DEFAULT 'Sourced',
    score REAL,
    notes TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS candidate_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT REFERENCES candidates(id) ON DELETE CASCADE,
    stage TEXT,
    note TEXT,
    date TEXT
);

CREATE TABLE IF NOT EXISTS playbook_fragments (
    id TEXT PRIMARY KEY,
    date TEXT,
    expires_at TEXT,
    content_hash TEXT UNIQUE,
    source_url TEXT,
    region TEXT,
    category TEXT,
    content TEXT,
    tags TEXT
);
"""


def get_db(db_path: str | None = None) -> sqlite3.Connection:
    """Return a module-level singleton connection (WAL mode, foreign keys on)."""
    global _connection
    with _lock:
        if _connection is None:
            path = db_path or DEFAULT_DB_PATH
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            _connection = sqlite3.connect(path, check_same_thread=False)
            _connection.row_factory = sqlite3.Row
            _connection.execute("PRAGMA journal_mode=WAL")
            _connection.execute("PRAGMA foreign_keys=ON")
            init_db(_connection)
        return _connection


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist."""
    conn.executescript(_SCHEMA)
    conn.commit()


def set_connection(conn: sqlite3.Connection) -> None:
    """Override the singleton — used by tests with :memory: databases."""
    global _connection
    with _lock:
        _connection = conn
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA foreign_keys=ON")
        init_db(_connection)


def close_db() -> None:
    """Close and clear the singleton connection."""
    global _connection
    with _lock:
        if _connection is not None:
            _connection.close()
            _connection = None
