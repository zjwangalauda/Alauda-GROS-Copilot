"""Tests for TalentPoolManager."""

import pytest

from talent_pool_manager import TalentPoolManager


class FakeAgent:
    """Minimal mock agent for testing."""

    def extract_text_from_file(self, file_name, file_bytes):
        return f"Parsed content of {file_name}"

    def extract_candidate_info(self, parsed_text):
        return {
            "candidate_name": "Test User",
            "email": "test@example.com",
            "phone": "+1234567890",
            "linkedin_url": "https://linkedin.com/in/testuser",
            "tags": "Python,Kubernetes,Go",
        }


@pytest.fixture
def agent():
    return FakeAgent()


@pytest.fixture
def tpm():
    return TalentPoolManager()


class FakeUploadedFile:
    def __init__(self, name, content=b"fake resume content"):
        self.name = name
        self._content = content

    def read(self):
        return self._content


def test_import_single_file(tpm, agent):
    files = [FakeUploadedFile("resume.pdf")]
    result = tpm.import_files(files, agent)
    assert result["imported"] == 1
    assert result["skipped_dup"] == 0


def test_import_duplicate_skipped(tpm, agent):
    files = [FakeUploadedFile("resume.pdf")]
    tpm.import_files(files, agent)
    result = tpm.import_files(files, agent)
    assert result["imported"] == 0
    assert result["skipped_dup"] == 1


def test_import_unsupported_format(tpm, agent):
    files = [FakeUploadedFile("data.xlsx")]
    result = tpm.import_files(files, agent)
    assert result["skipped_unsupported"] == 1
    assert result["imported"] == 0


def test_get_all_talents(tpm, agent):
    tpm.import_files([FakeUploadedFile("a.pdf")], agent)
    tpm.import_files([FakeUploadedFile("b.txt", b"different content")], agent)
    talents = tpm.get_all_talents()
    assert len(talents) == 2


def test_delete_talent(tpm, agent):
    tpm.import_files([FakeUploadedFile("c.pdf")], agent)
    talents = tpm.get_all_talents()
    assert len(talents) == 1

    tid = talents[0]["id"]
    assert tpm.delete_talent(tid) is True
    assert len(tpm.get_all_talents()) == 0


def test_delete_nonexistent_talent(tpm):
    assert tpm.delete_talent("tp_nonexistent") is False


def test_get_talent(tpm, agent):
    tpm.import_files([FakeUploadedFile("d.pdf")], agent)
    talents = tpm.get_all()
    t = tpm.get_talent(talents[0]["id"])
    assert t is not None
    assert t["candidate_name"] == "Test User"
    assert t["email"] == "test@example.com"
    assert "Python" in t["tags"]


def test_get_stats(tpm, agent):
    tpm.import_files([FakeUploadedFile("e.pdf")], agent)
    stats = tpm.get_stats()
    assert stats["total"] == 1


def test_import_from_directory(tpm, agent, tmp_path):
    # Create test files
    (tmp_path / "resume1.txt").write_bytes(b"resume one content")
    (tmp_path / "resume2.txt").write_bytes(b"resume two content")
    (tmp_path / "readme.md").write_bytes(b"not a resume")

    result = tpm.import_from_directory(str(tmp_path), agent)
    assert result["imported"] == 2
    assert result["skipped_unsupported"] == 1


def test_import_from_nonexistent_directory(tpm, agent):
    result = tpm.import_from_directory("/nonexistent/path", agent)
    assert len(result["errors"]) == 1


def test_get_all_talents_since_date(tpm, agent):
    tpm.import_files([FakeUploadedFile("f.pdf")], agent)
    # Future date should return nothing
    talents = tpm.get_all_talents(since_date="2099-01-01")
    assert len(talents) == 0
    # Past date should return all
    talents = tpm.get_all_talents(since_date="2000-01-01")
    assert len(talents) == 1
