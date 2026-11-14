"""CAN-REQ-008: alert transitions."""
import pytest

from canary.workflow import TransitionError, check_transition


def test_documented_happy_path_is_permitted():
    for cur, new in [("new", "under_investigation"), ("under_investigation", "mitigation_in_progress")]:
        check_transition(cur, new)
    check_transition("mitigation_in_progress", "resolved_verified", note="Auto-install disabled and verified")


def test_new_cannot_jump_to_resolved():
    with pytest.raises(TransitionError):
        check_transition("new", "resolved_verified", note="x")


def test_exposure_confirmed_requires_human_evidence_note():
    with pytest.raises(TransitionError, match="Evidence note"):
        check_transition("under_investigation", "exposure_confirmed", note="  ")
    check_transition("under_investigation", "exposure_confirmed", note="Malicious package found in lockfile")


def test_resolved_alert_can_be_reopened():
    check_transition("resolved_verified", "under_investigation")
