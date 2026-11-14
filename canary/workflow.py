"""Alert investigation states and permitted transitions — CAN-REQ-008."""

ALERT_STATUSES = {
    "new": "New",
    "under_investigation": "Under investigation",
    "exposure_confirmed": "Exposure confirmed",
    "mitigation_in_progress": "Mitigation in progress",
    "resolved_verified": "Resolved and verified",
    "not_applicable": "Not applicable",
    "risk_accepted": "Risk accepted",
}

ALERT_TRANSITIONS = {
    "new": ["under_investigation"],
    "under_investigation": ["mitigation_in_progress", "exposure_confirmed", "not_applicable", "risk_accepted"],
    "exposure_confirmed": ["mitigation_in_progress"],
    "mitigation_in_progress": ["resolved_verified"],
    "resolved_verified": ["under_investigation"],
    "not_applicable": ["under_investigation"],
    "risk_accepted": ["under_investigation"],
}

# Human-entered note required: Exposure confirmed is never an AI inference.
NOTE_REQUIRED = {"exposure_confirmed": "Evidence note", "resolved_verified": "Verification note",
                 "risk_accepted": "Risk acceptance reason"}


class TransitionError(ValueError):
    pass


def check_transition(current, new, note=""):
    if new not in ALERT_TRANSITIONS.get(current, []):
        raise TransitionError(f"Cannot move from {ALERT_STATUSES.get(current, current)} to "
                              f"{ALERT_STATUSES.get(new, new)}.")
    if new in NOTE_REQUIRED and not (note or "").strip():
        raise TransitionError(f"{NOTE_REQUIRED[new]} is required for {ALERT_STATUSES[new]}.")
