import pytest
from candidate_manager import CandidateManager


def test_add_candidate(cm):
    c = cm.add_candidate(name="Alice", role="Backend Developer")
    assert c["id"].startswith("cand_")
    assert c["stage"] == "Sourced"
    assert c["name"] == "Alice"


def test_move_stage(cm):
    c = cm.add_candidate(name="Bob", role="Frontend Developer")
    result = cm.move_stage(c["id"], "Interview", note="Passed phone screen")

    assert result is True
    updated = [x for x in cm.get_all() if x["id"] == c["id"]][0]
    assert updated["stage"] == "Interview"
    assert len(updated["history"]) == 2  # Sourced + Interview


def test_move_invalid(cm):
    c = cm.add_candidate(name="Carol", role="Designer")
    with pytest.raises(ValueError):
        cm.move_stage(c["id"], "InvalidStage")


def test_update_score(cm):
    c = cm.add_candidate(name="Dave", role="SRE")
    cm.update_score(c["id"], 85)
    updated = [x for x in cm.get_all() if x["id"] == c["id"]][0]
    assert updated["score"] == 85


def test_add_note(cm):
    c = cm.add_candidate(name="Eve", role="PM")
    cm.add_note(c["id"], "Great communication skills")
    updated = [x for x in cm.get_all() if x["id"] == c["id"]][0]
    assert "Great communication skills" in updated["notes"]


def test_delete(cm):
    c = cm.add_candidate(name="Frank", role="QA")
    cm.delete_candidate(c["id"])
    ids = [x["id"] for x in cm.get_all()]
    assert c["id"] not in ids


def test_get_by_stage(cm):
    cm.add_candidate(name="Grace", role="Dev")
    c2 = cm.add_candidate(name="Hank", role="Dev")
    cm.move_stage(c2["id"], "Interview")

    sourced = cm.get_by_stage("Sourced")
    assert len(sourced) == 1
    assert sourced[0]["name"] == "Grace"

    interview = cm.get_by_stage("Interview")
    assert len(interview) == 1
    assert interview[0]["name"] == "Hank"


def test_get_stats(cm):
    cm.add_candidate(name="A", role="Dev")
    cm.add_candidate(name="B", role="Dev")
    c3 = cm.add_candidate(name="C", role="Dev")
    cm.move_stage(c3["id"], "Offer")

    stats = cm.get_stats()
    assert stats["Sourced"] == 2
    assert stats["Offer"] == 1
    assert stats["Rejected"] == 0


def test_persistence(cm):
    c = cm.add_candidate(name="Zara", role="Lead")
    cm.move_stage(c["id"], "Contacted")

    cm2 = CandidateManager(db_path=cm.db_path)
    assert len(cm2.get_all()) == 1
    assert cm2.get_all()[0]["stage"] == "Contacted"
