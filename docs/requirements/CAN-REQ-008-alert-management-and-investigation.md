# CAN-REQ-008: Alert Management and Investigation Workflow

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§4, 6, 10

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

## Open decisions
- Fine-grained role permissions, status transition rules, comments, and team assignment model.
