# CAN-REQ-011: Guided Reports and Mitigation Recommendations

**Status:** Proposed · **Priority:** MVP · **Source:** sureh.md; Project Plan §§1, 6, 7a, 10

## Purpose
Translate a threat and known organizational gaps into understandable, prioritized next steps.

## Requirements
1. A user can request a guided report from an alert or supported scenario.
2. Each recommendation includes priority/order, action, short explanation of the risk addressed, and evidence or rationale.
3. Recommendations use the finding's confirmed facts, uncertainty, organization inventory, and questionnaire results where relevant.
4. Separate recommended actions from facts and clearly label generated content as a draft for review.
5. Avoid unsafe or overly specific operational instructions when evidence is insufficient; direct users to authoritative vendor or organizational guidance where appropriate.
6. Authorized users can edit, reject, or mark a recommendation complete, with relevant history preserved.

## Acceptance criteria
- A report explains why each action is proposed and what risk it addresses.
- Unsupported exposure assumptions are not stated as facts.
- The user can edit the draft before it becomes part of an approved plan.
- Recommendations link back to relevant source evidence or framework guidance where available.

## Dependencies
CAN-REQ-006, CAN-REQ-007, CAN-REQ-010.

## Open decisions
- Report template, export/print format, recommendation lifecycle, and whether model-generated plans require explicit reviewer sign-off before saving.
