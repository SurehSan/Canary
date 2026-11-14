# CAN-REQ-009: Notification Rules and Delivery

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§5, 10

## Purpose
Deliver timely, appropriately targeted alerts without overwhelming employees.

## Requirements
1. Support email notifications for the MVP, with priority-aware delivery rules.
2. Let an authorized administrator configure recipients by alert category and team/role where available.
3. Support immediate delivery for configured critical alerts and scheduled daily/weekly digests for lower-priority items.
4. Separate collection cadence from notification cadence.
5. Track notification attempts and outcomes; failures must be visible to administrators and must not falsely mark a recipient as notified.
6. Avoid duplicate notifications for unchanged findings; send an update when a meaningful change occurs according to configured rules.

## Acceptance criteria
- A configured recipient receives a testable email notification for a matching alert.
- A user without the relevant notification assignment does not receive that alert by default.
- A meaningful update can trigger a notification; unchanged duplicate collection does not repeatedly notify.
- The product communicates configured cadence and does not promise guaranteed real-time discovery.

## Dependencies
CAN-REQ-001, CAN-REQ-008.

## Open decisions
- Email provider, digest scheduling, delivery retries, unsubscribe/administrative controls, and default recipient rules.
