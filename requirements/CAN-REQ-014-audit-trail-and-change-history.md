# CAN-REQ-014: Audit Trail and Change History

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§6, 11

## Purpose
Preserve enough history for an organization to understand what Canary found, what changed, and what people decided.

## Requirements
1. Record important user actions on alerts, assessments, recommendations, plans, memberships, and organization settings.
2. For each event, record organization, actor or system process, action, target record, timestamp, and relevant before/after summary where appropriate.
3. Preserve finding and plan revisions so changed evidence or guidance can be compared with earlier versions.
4. Restrict audit history to authorized users in the same organization.
5. Audit records must not expose secrets or unnecessary sensitive content.

## Acceptance criteria
- A reviewer can determine who changed an alert status or approved a plan and when.
- A finding update preserves its prior state and identifies the changed information.
- Audit history for one organization cannot be queried by another.
- Sensitive credentials are absent from audit records.

## Dependencies
CAN-REQ-001, CAN-REQ-008, CAN-REQ-012.

## Open decisions
- Retention period, export needs, tamper-evidence requirements, and which events are considered audit-critical.
