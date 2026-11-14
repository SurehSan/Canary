# CAN-REQ-008: Alert Management and Investigation Workflow

**Status:** Proposed · **Priority:** Local demo prototype · **Source:** Project Plan §§4, 6, 10

## Purpose
Give users a central place to understand, assign, investigate, and resolve relevant findings.

## Requirements
1. Present alerts with concise summary, priority, relevance rationale, known/unknown information, timestamps, and source links.
2. Users can filter alerts by priority, category, date, and status, and distinguish unread alerts.
3. An authorized user can assign an alert to a responsible person or team.
4. Track investigation outcomes including Under investigation, Exposure confirmed, Mitigation in progress, Resolved and verified, Not applicable, and Risk accepted.
5. Record who changed an alert's status, assignment, or assessment and when.
6. New meaningful evidence can update an existing alert without erasing previous review state or history.

## Acceptance criteria
- Users can find an alert using the supported filters and open the underlying source.
- An alert can be assigned and moved through the documented outcomes.
- Status and assignment changes are attributable and time-stamped.
- Users can distinguish new evidence from the original alert content.

## Dependencies
CAN-REQ-001, CAN-REQ-007.

## Prototype design decisions
- Use only Administrator and Cybersecurity Lead roles (CAN-REQ-001). Administrators manage members/settings and can perform all alert actions. Cybersecurity Leads can assign alerts to either lead, investigate, comment, edit guide steps, and recommend/perform mitigation status changes. Seed two leads to demonstrate delegated research and implementation work.
- Allow transitions New → Under investigation → Mitigation in progress → Resolved and verified; Under investigation may also move to Exposure confirmed, Not applicable, or Risk accepted. Exposure confirmed requires a human-entered evidence note. Reopening a resolved alert creates an audited transition to Under investigation. Record actor, time, previous/new status, assignment, and comments.
- New evidence updates the alert while preserving prior review, assignment, and status; show a visible update indicator and retain the earlier finding version. Require a reason for manual priority or relevance overrides.
