# CAN-REQ-009: Notification Rules and Delivery

**Status:** Proposed · **Priority:** Local demo prototype · **Source:** Project Plan §§5, 10

## Purpose
Deliver timely, appropriately targeted alerts without overwhelming employees.

## Requirements
1. Send real email for prototype notifications using a configured SMTP-compatible provider, with priority-aware delivery rules. All sends are test messages, not production customer notifications.
2. Let an authorized Administrator configure recipients by alert category and team/role where available.
3. Support immediate delivery for configured critical alerts and scheduled daily/weekly digests for lower-priority items.
4. Separate collection cadence from notification cadence.
5. Track notification attempts and outcomes; failures must be visible to Administrators and must not falsely mark a recipient as notified.
6. Avoid duplicate notifications for unchanged findings; send an update when a meaningful change occurs according to configured rules.
7. During the prototype, allow delivery only to an explicit allowlist of project team-owned test email addresses. Reject any other recipient before attempting delivery; there is no production-send mode.
8. Clearly show test mode in configuration and every message. Include a conspicuous test label in the subject and body, and record recipients and delivery outcomes. Store provider credentials only in local environment secrets.
9. Demonstrate notification paths, including priority routing, category/team recipient selection, immediate messages, digests, meaningful updates, duplicate suppression, and delivery failures.

## Acceptance criteria
- A configured team-owned test recipient receives a real email for a matching alert, and the app records the delivery outcome.
- A user without the relevant notification assignment does not receive that alert by default.
- A meaningful update can trigger a notification; unchanged duplicate collection does not repeatedly notify.
- The product communicates configured cadence and does not promise guaranteed real-time discovery.
- Messages are sent only to designated team-owned test addresses; non-allowlisted recipients are rejected.
- Failed delivery is visible to an Administrator and is not recorded as successful.

## Dependencies
CAN-REQ-001, CAN-REQ-008.

## Prototype design decisions
- Send actual test messages through an SMTP-compatible provider selected and configured by the project team. Support common provider SMTP settings through environment configuration; do not commit credentials. The prototype has no in-app production mode.
- Require an explicit allowlist of team-owned test email addresses. The recipient must be on that list before any send is attempted. Do not use fictional characters' identities as real recipients; map roles to team-owned test addresses.
- Prefix every subject with **[CANARY DEMO - TEST]**, show a test-mode banner in the email body and application, and include a statement that the message is a demo notification, not evidence of a real incident.
- Route by category to configured Administrator/Cybersecurity Lead recipients. Defaults: P1 immediate, P2 prompt in the next local processing cycle, P3/P4 in a daily digest. Provide a manual “process digest” action and record attempted/sent/failed/suppressed outcomes.
- Suppress unchanged repeats; send an update when priority, affected products, exploitation status, or source evidence materially changes. Demonstrate a simulated delivery failure and retry once; clearly distinguish simulation from actual SMTP delivery status.
- Reject all non-allowlisted recipients, including when configuration is missing or malformed. Never fall back silently to a mock inbox or claim delivery on failure. Show failure and retry controls to the Administrator. No production-send toggle is exposed.

## Amendment 2026-11-14: presentation mode
With `CANARY_PRESENTATION_MODE=1`, the subject tag is `[Canary · Test]`, and in place of the header block the body
ends with a one-line notice: the message is a test notification from a sample workspace and is not evidence of an
actual incident. Every message is still labeled as a test. The allowlist, the rejection of all other recipients,
and the failure reporting are unchanged. The default (off) keeps the `[CANARY DEMO - TEST]` prefix and the full
test-mode notice.
