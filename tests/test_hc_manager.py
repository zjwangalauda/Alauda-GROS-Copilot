import pytest
from hc_manager import HCManager


SAMPLE_KWARGS = dict(
    department="Engineering",
    role_title="Backend Developer",
    location="Beijing",
    urgency="High",
    mission="Build microservices",
    tech_stack="Python, Go",
    deal_breakers="None",
    selling_point="Great team",
)


def test_submit_request(hc_manager):
    initial_count = len(hc_manager.get_all_requests())
    req_id = hc_manager.submit_request(**SAMPLE_KWARGS)

    assert req_id.startswith("HC_")
    assert len(hc_manager.get_all_requests()) == initial_count + 1

    req = hc_manager.get_all_requests()[0]
    assert req["department"] == "Engineering"
    assert req["role_title"] == "Backend Developer"
    assert req["status"] == "Pending"


def test_unique_ids(hc_manager):
    id1 = hc_manager.submit_request(**SAMPLE_KWARGS)
    id2 = hc_manager.submit_request(**SAMPLE_KWARGS)
    assert id1 != id2


def test_update_status_approved(hc_manager):
    req_id = hc_manager.submit_request(**SAMPLE_KWARGS)
    result = hc_manager.update_status(req_id, "Approved")

    assert result is True
    req = [r for r in hc_manager.get_all_requests() if r["id"] == req_id][0]
    assert req["status"] == "Approved"


def test_update_status_invalid(hc_manager):
    req_id = hc_manager.submit_request(**SAMPLE_KWARGS)
    with pytest.raises(ValueError):
        hc_manager.update_status(req_id, "InvalidStatus")


def test_update_not_found(hc_manager):
    result = hc_manager.update_status("HC_nonexistent", "Approved")
    assert result is False


def test_get_approved(hc_manager):
    id1 = hc_manager.submit_request(**SAMPLE_KWARGS)
    id2 = hc_manager.submit_request(**SAMPLE_KWARGS)
    hc_manager.update_status(id1, "Approved")

    approved = hc_manager.get_approved_requests()
    assert len(approved) == 1
    assert approved[0]["id"] == id1


def test_persistence(hc_manager):
    req_id = hc_manager.submit_request(**SAMPLE_KWARGS)
    hc_manager.update_status(req_id, "Approved")

    # Create a new instance pointing to the same file
    mgr2 = HCManager(db_path=hc_manager.db_path)
    assert len(mgr2.get_all_requests()) == 1
    assert mgr2.get_all_requests()[0]["id"] == req_id
    assert mgr2.get_all_requests()[0]["status"] == "Approved"


def test_transition_from_approved_blocked(hc_manager):
    """Approved is a terminal state — cannot transition to anything."""
    req_id = hc_manager.submit_request(**SAMPLE_KWARGS)
    hc_manager.update_status(req_id, "Approved")
    with pytest.raises(ValueError, match="terminal state"):
        hc_manager.update_status(req_id, "Pending")


def test_transition_from_rejected_blocked(hc_manager):
    """Rejected is a terminal state — cannot transition to anything."""
    req_id = hc_manager.submit_request(**SAMPLE_KWARGS)
    hc_manager.update_status(req_id, "Rejected")
    with pytest.raises(ValueError, match="terminal state"):
        hc_manager.update_status(req_id, "Approved")
