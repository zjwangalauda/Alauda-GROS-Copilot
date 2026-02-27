import sys
import os
import pytest

# Ensure the project root is on sys.path so managers can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hc_manager import HCManager
from knowledge_manager import KnowledgeManager
from candidate_manager import CandidateManager


@pytest.fixture
def hc_manager(tmp_path):
    return HCManager(db_path=str(tmp_path / "hc.json"))


@pytest.fixture
def km(tmp_path):
    return KnowledgeManager(db_path=str(tmp_path / "fragments.json"))


@pytest.fixture
def cm(tmp_path):
    return CandidateManager(db_path=str(tmp_path / "candidates.json"))
