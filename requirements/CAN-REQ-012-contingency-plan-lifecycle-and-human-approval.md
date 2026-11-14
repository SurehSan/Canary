# CAN-REQ-012: Contingency Plan Lifecycle and Human Approval

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§4, 6, 10, 11

## Purpose
Help organizations prepare and maintain response plans while keeping decisions with authorized personnel.

## Requirements
1. A user can create a proposed contingency plan from an alert or a scenario.
2. Plans can contain staged actions, owners, responsibilities, review dates, and links to the originating threat or report.
3. Authorized users can edit plans, assign owners, record approval, and track review/exercise dates.
4. Preserve plan versions and show who changed or approved each version and when.
5. A generated plan remains a draft until an authorized human approves it.
6. Canary does not independently execute actions on customer systems or make clinical/high-impact decisions.
7. Support plan status sufficient to distinguish draft, in review, approved, and archived/retired.

## Acceptance criteria
- A user can generate, edit, and save a draft plan linked to its source alert or scenario.
- Only an authorized role can approve a plan.
- Approval and subsequent edits are recorded; edits to an approved plan are distinguishable from the approved version.
- A plan can be assigned owners and a future review date.

## Dependencies
CAN-REQ-008, CAN-REQ-011.

## Open decisions
- Exact plan stages and status transitions, approval policy, export format, and reminder behavior.
