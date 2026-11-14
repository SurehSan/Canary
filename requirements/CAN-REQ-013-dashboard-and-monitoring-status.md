# CAN-REQ-013: Dashboard and Monitoring Status

**Status:** Proposed · **Priority:** Local demo prototype · **Source:** Project Plan §§4, 10

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

## Prototype design decisions
- Show unread/new alerts, alerts requiring action, P1/P2 counts, recent relevant events, open plans, and source freshness/errors. All values derive from saved organization records.
- “Requires action” means a New unread alert, an assigned alert in investigation or mitigation, a guide with a pending user step, or a plan in review awaiting approval. Provide direct links to each record.
- Both prototype roles see the same organization-scoped status data; expose management actions only to Administrators and investigation/implementation actions to Cybersecurity Leads. Never present failed/stale collection as healthy.
