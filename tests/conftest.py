import sqlite3
import pytest

import db as db_mod
from hc_manager import HCManager
from knowledge_manager import KnowledgeManager
from candidate_manager import CandidateManager


@pytest.fixture(autouse=True)
def _fresh_db(tmp_path):
    """Give every test an isolated in-memory SQLite database.

    Uses a tmp_path-based nonexistent path for legacy JSON migration so real
    data files on disk are never touched.
    """
    conn = sqlite3.connect(":memory:")
    db_mod.set_connection(conn)
    yield
    conn.close()
    db_mod.close_db()


@pytest.fixture
def hc_manager(tmp_path):
    # Pass a nonexistent legacy JSON path to prevent migration from real data
    return HCManager(db_path=str(tmp_path / "nonexistent.json"))


@pytest.fixture
def km(tmp_path):
    return KnowledgeManager(db_path=str(tmp_path / "nonexistent.json"))


@pytest.fixture
def cm(tmp_path):
    return CandidateManager(db_path=str(tmp_path / "nonexistent.json"))
