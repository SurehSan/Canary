# CAN-REQ-013: Dashboard and Monitoring Status

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§4, 10

## Purpose
Give users a simple, role-appropriate overview of current work and monitoring health.

## Requirements
1. Display counts or lists for new/unread alerts, alerts requiring action, high-priority threats, and open contingency plans.
2. Show recent relevant events and clear paths to alert details and plan records.
3. Show monitoring status, including enabled sources and recent collection errors or stale checks where applicable.
4. Present information according to the user's organization and permissions.
5. Use plain language and make the next available action clear without requiring specialist security knowledge.

## Acceptance criteria
- The dashboard reflects current alert and plan records rather than hard-coded demo counts.
- Users can navigate from a dashboard item to its detail.
- A monitoring failure is not presented as healthy monitoring.
- Cross-organization data is never included in dashboard results.

## Dependencies
CAN-REQ-008, CAN-REQ-009, CAN-REQ-012.

## Open decisions
- Dashboard layout, role-specific widgets, and definition of “requires action.”
