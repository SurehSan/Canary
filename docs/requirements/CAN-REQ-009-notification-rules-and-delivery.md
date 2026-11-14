# CAN-REQ-009: Notification Rules and Delivery

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§5, 10

## Purpose
Deliver timely, appropriately targeted alerts without overwhelming employees.

## Requirements
1. Use email as the MVP notification channel, with priority-aware delivery rules.
2. Let an authorized administrator configure recipients by alert category and team/role where available.
3. Support immediate delivery for configured critical alerts and scheduled daily/weekly digests for lower-priority items.
4. Separate collection cadence from notification cadence.
5. Track notification attempts and outcomes; failures must be visible to administrators and must not falsely mark a recipient as notified.
6. Avoid duplicate notifications for unchanged findings; send an update when a meaningful change occurs according to configured rules.
7. During development and system verification, use project team-owned email addresses as mock recipient accounts. Route test notifications only to the configured mock accounts until the team explicitly enables delivery to non-test recipients.
8. Make the active delivery mode clear in configuration (test/mock or production) and provide a safe way to verify message content, recipients, and delivery outcomes using the mock accounts.
9. Test the notification paths with mock accounts, including priority routing, category/team recipient selection, immediate messages, digests, meaningful updates, duplicate suppression, and delivery failures.

## Acceptance criteria
- A configured recipient receives a testable email notification for a matching alert.
- A user without the relevant notification assignment does not receive that alert by default.
- A meaningful update can trigger a notification; unchanged duplicate collection does not repeatedly notify.
- The product communicates configured cadence and does not promise guaranteed real-time discovery.
- In test/mock mode, notifications are delivered to designated project mock email accounts and are not sent to customer or other non-test recipients.
- Tests confirm that messages go to the intended mock account and that failed delivery is visible to an administrator.

## Dependencies
CAN-REQ-001, CAN-REQ-008.

## Open decisions
- Email provider and configuration of project-owned mock accounts.
- Digest scheduling, delivery retries, unsubscribe/administrative controls, and default recipient rules.
- The explicit process for enabling production delivery to non-test recipients.
