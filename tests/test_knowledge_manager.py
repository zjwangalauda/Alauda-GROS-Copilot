import os
from datetime import datetime, timedelta
from knowledge_manager import KnowledgeManager


def test_add_fragment(km):
    ok, msg = km.add_fragment(
        region="China",
        category="Sourcing",
        content="Always check LinkedIn before cold outreach.",
    )
    assert ok is True
    assert msg == "added"


def test_duplicate(km):
    km.add_fragment(region="China", category="Sourcing", content="Same content")
    ok, msg = km.add_fragment(region="China", category="Sourcing", content="Same content")
    assert ok is False
    assert msg == "duplicate"


def test_expiry_ok(km):
    fragment = {"expires_at": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")}
    assert km.get_expiry_status(fragment) == "ok"


def test_expiry_expired(km):
    fragment = {"expires_at": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")}
    assert km.get_expiry_status(fragment) == "expired"


def test_expiry_soon(km):
    fragment = {"expires_at": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")}
    assert km.get_expiry_status(fragment) == "expiring_soon"


def test_compile_markdown(km, tmp_path):
    km.add_fragment(region="China", category="Sourcing", content="Test knowledge fragment.")
    output_file = str(tmp_path / "playbook.md")
    result = km.compile_to_markdown(output_file=output_file)

    assert result is True
    assert os.path.exists(output_file)
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Test knowledge fragment." in content


def test_persistence(km, tmp_path):
    km.add_fragment(region="US", category="Interview", content="Persistence check content")

    # New instance shares the same SQLite singleton
    km2 = KnowledgeManager(db_path=str(tmp_path / "nonexistent.json"))
    assert len(km2.get_all_fragments()) == 1
    assert km2.get_all_fragments()[0]["content"] == "Persistence check content"
