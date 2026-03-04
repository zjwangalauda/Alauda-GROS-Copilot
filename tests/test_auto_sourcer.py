"""Tests for AutoSourcer."""

import pytest
from datetime import date, timedelta

from auto_sourcer import AutoSourcer, FREEZE_DAYS
from hc_manager import HCManager
from talent_pool_manager import TalentPoolManager
from candidate_manager import CandidateManager


class FakeAgent:
    """Mock agent that returns deterministic evaluation results."""

    def extract_text_from_file(self, file_name, file_bytes):
        return f"Parsed: {file_name}"

    def extract_candidate_info(self, parsed_text):
        return {
            "candidate_name": "Test Candidate",
            "email": "test@test.com",
            "phone": "",
            "linkedin_url": "",
            "tags": "Python,K8s",
        }

    def evaluate_resume(self, jd_text, resume_text):
        """Return a high-scoring evaluation for any input."""
        return """### 📊 Quantified Assessment
- **Total Score**: 85 / 100
- **Score Breakdown**:
  - Mission Match: 35 / 40 — Reasoning: Strong match
  - Tech Stack Depth: 30 / 40 — Reasoning: Good depth
  - Deal Breaker Avoidance: 20 / 20 — Reasoning: No issues
- **Verdict**: Strong Match

### ✨ Core Highlights
- Strong K8s experience

### 🚨 Red Flags & Deal Breaker Warnings
- None

### 🎯 Phone Screen Probing Questions
- Tell me about your K8s architecture experience
"""


class LowScoreAgent(FakeAgent):
    """Mock agent that returns low scores."""

    def evaluate_resume(self, jd_text, resume_text):
        return """### 📊 Quantified Assessment
- **Total Score**: 40 / 100
- **Score Breakdown**:
  - Mission Match: 10 / 40
  - Tech Stack Depth: 10 / 40
  - Deal Breaker Avoidance: 20 / 20
- **Verdict**: Disqualified
"""


class FakeUploadedFile:
    def __init__(self, name, content=b"fake content"):
        self.name = name
        self._content = content

    def read(self):
        return self._content


def _seed_hc(hm):
    """Create an approved HC for testing."""
    hc_id = hm.submit_request(
        department="Engineering",
        role_title="Senior K8s Engineer",
        location="Singapore",
        urgency="Normal",
        mission="Build cloud-native platform",
        tech_stack="Kubernetes, Go, Docker",
        deal_breakers="No B2B experience",
        selling_point="Global expansion opportunity",
    )
    hm.update_status(hc_id, "Approved")
    return hc_id


def _seed_talent(tpm, agent, name="resume.pdf", content=b"fake resume"):
    """Import a talent into the pool."""
    tpm.import_files([FakeUploadedFile(name, content)], agent)
    return tpm.get_all()[0]


# ------------------------------------------------------------------
# Score Parsing
# ------------------------------------------------------------------

def test_parse_score():
    agent = FakeAgent()
    sourcer = AutoSourcer(agent)
    eval_md = agent.evaluate_resume("jd", "resume")
    score, verdict = sourcer._parse_score(eval_md)
    assert score == 85.0
    assert verdict == "Strong Match"


def test_parse_score_low():
    agent = LowScoreAgent()
    sourcer = AutoSourcer(agent)
    eval_md = agent.evaluate_resume("jd", "resume")
    score, verdict = sourcer._parse_score(eval_md)
    assert score == 40.0
    assert verdict == "Disqualified"


# ------------------------------------------------------------------
# Full Run
# ------------------------------------------------------------------

def test_run_with_no_hcs():
    agent = FakeAgent()
    sourcer = AutoSourcer(agent)
    run_id = sourcer.run()
    runs = sourcer.get_run_history()
    assert len(runs) == 1
    assert runs[0]["status"] == "completed"
    assert runs[0]["matches_found"] == 0


def test_run_with_no_talents(tmp_path):
    agent = FakeAgent()
    hm = HCManager(db_path=str(tmp_path / "x.json"))
    _seed_hc(hm)

    sourcer = AutoSourcer(agent)
    run_id = sourcer.run()
    runs = sourcer.get_run_history()
    assert runs[0]["status"] == "completed"
    assert runs[0]["talent_scanned"] == 0


def test_full_run_produces_shortlist(tmp_path):
    agent = FakeAgent()
    hm = HCManager(db_path=str(tmp_path / "x.json"))
    tpm = TalentPoolManager()
    hc_id = _seed_hc(hm)
    _seed_talent(tpm, agent)

    sourcer = AutoSourcer(agent)
    run_id = sourcer.run(force_full=True)

    runs = sourcer.get_run_history()
    assert runs[0]["status"] == "completed"
    assert runs[0]["matches_found"] >= 1

    shortlist = sourcer.get_shortlist()
    assert len(shortlist) >= 1
    assert shortlist[0]["score"] == 85.0
    assert shortlist[0]["verdict"] == "Strong Match"


def test_low_score_not_in_shortlist(tmp_path):
    agent = LowScoreAgent()
    hm = HCManager(db_path=str(tmp_path / "x.json"))
    tpm = TalentPoolManager()
    _seed_hc(hm)
    _seed_talent(tpm, FakeAgent())  # Use FakeAgent for import (extract_candidate_info)

    sourcer = AutoSourcer(agent)
    sourcer.run(force_full=True)

    shortlist = sourcer.get_shortlist()
    assert len(shortlist) == 0


# ------------------------------------------------------------------
# Incremental Logic
# ------------------------------------------------------------------

def test_incremental_run(tmp_path):
    agent = FakeAgent()
    hm = HCManager(db_path=str(tmp_path / "x.json"))
    tpm = TalentPoolManager()
    _seed_hc(hm)
    _seed_talent(tpm, agent, "first.pdf", b"first")

    sourcer = AutoSourcer(agent)
    first_run_id = sourcer.run(force_full=True)  # First run = full

    # Add new talent
    tpm.import_files([FakeUploadedFile("second.pdf", b"second content")], agent)

    # Second run should be incremental
    second_run_id = sourcer.run()
    runs = sourcer.get_run_history()
    second_run = next(r for r in runs if r["id"] == second_run_id)
    first_run = next(r for r in runs if r["id"] == first_run_id)
    assert first_run["run_type"] == "full"
    assert second_run["run_type"] == "incremental"


# ------------------------------------------------------------------
# Disposition
# ------------------------------------------------------------------

def test_set_disposition_interested(tmp_path):
    agent = FakeAgent()
    hm = HCManager(db_path=str(tmp_path / "x.json"))
    tpm = TalentPoolManager()
    _seed_hc(hm)
    _seed_talent(tpm, agent)

    sourcer = AutoSourcer(agent)
    sourcer.run(force_full=True)
    shortlist = sourcer.get_shortlist()
    assert len(shortlist) >= 1

    sl_id = shortlist[0]["id"]
    result = sourcer.set_disposition(sl_id, "Interested")
    assert result is True

    updated = sourcer.get_shortlist(disposition="Interested")
    assert len(updated) >= 1


def test_set_disposition_not_interested(tmp_path):
    agent = FakeAgent()
    hm = HCManager(db_path=str(tmp_path / "x.json"))
    tpm = TalentPoolManager()
    _seed_hc(hm)
    _seed_talent(tpm, agent)

    sourcer = AutoSourcer(agent)
    sourcer.run(force_full=True)
    shortlist = sourcer.get_shortlist()
    sl_id = shortlist[0]["id"]

    sourcer.set_disposition(sl_id, "Not Interested", note="Not looking")
    frozen = sourcer.get_frozen_list()
    assert len(frozen) >= 1


def test_set_disposition_invalid(tmp_path):
    agent = FakeAgent()
    sourcer = AutoSourcer(agent)
    with pytest.raises(ValueError, match="Invalid disposition"):
        sourcer.set_disposition("fake_id", "Maybe")


# ------------------------------------------------------------------
# Convert to Candidate
# ------------------------------------------------------------------

def test_convert_to_candidate(tmp_path):
    agent = FakeAgent()
    hm = HCManager(db_path=str(tmp_path / "x.json"))
    tpm = TalentPoolManager()
    _seed_hc(hm)
    _seed_talent(tpm, agent)

    sourcer = AutoSourcer(agent)
    sourcer.run(force_full=True)
    shortlist = sourcer.get_shortlist()
    sl_id = shortlist[0]["id"]

    cand_id = sourcer.convert_to_candidate(sl_id)
    assert cand_id is not None
    assert cand_id.startswith("cand_")

    # Verify candidate is in pipeline at Contacted stage
    cm = CandidateManager()
    all_cands = cm.get_all()
    cand = next(c for c in all_cands if c["id"] == cand_id)
    assert cand["stage"] == "Contacted"
    assert cand["source"] == "Auto Sourcing"
    assert cand["score"] == 85.0


# ------------------------------------------------------------------
# Freeze / Unfreeze
# ------------------------------------------------------------------

def test_unfreeze(tmp_path):
    agent = FakeAgent()
    hm = HCManager(db_path=str(tmp_path / "x.json"))
    tpm = TalentPoolManager()
    _seed_hc(hm)
    _seed_talent(tpm, agent)

    sourcer = AutoSourcer(agent)
    sourcer.run(force_full=True)
    shortlist = sourcer.get_shortlist()
    sl_id = shortlist[0]["id"]

    sourcer.set_disposition(sl_id, "Not Interested", note="Not available")
    assert len(sourcer.get_frozen_list()) >= 1

    sourcer.unfreeze(sl_id)
    # After unfreeze, disposition should be Pending
    updated = sourcer.get_shortlist(disposition="Pending")
    assert any(s["id"] == sl_id for s in updated)


# ------------------------------------------------------------------
# JD Builder
# ------------------------------------------------------------------

def test_build_jd_from_hc(tmp_path):
    agent = FakeAgent()
    hm = HCManager(db_path=str(tmp_path / "x.json"))
    hc_id = _seed_hc(hm)
    hcs = hm.get_approved_requests()

    sourcer = AutoSourcer(agent)
    jd = sourcer._build_jd_from_hc(hcs[0])
    assert "Senior K8s Engineer" in jd
    assert "Singapore" in jd
    assert "Kubernetes" in jd
