# Canary Requirements

This folder turns the working concept in `sureh.md` and `CANARY_Project_Plan.md` into requirements for a locally run demo prototype. “Prototype design decisions” in each requirement are the chosen defaults for this project; production prerequisites are called out separately where relevant.

## How to use these documents

Represent every requirement CAN-REQ-001 through CAN-REQ-016 in the local prototype, using a working feature or clearly labeled simulation where external/production behavior is out of scope. Each document defines one capability, purpose, requirements, acceptance criteria, dependencies, and prototype design decisions. Acceptance criteria are intended to be verifiable; the specific implementation stack remains a design choice.

The project plan is a working concept. Prototype defaults are selected to make the design implementable and are not claims about a future hosted product. The target is local execution only, with fictional/sample data and visible demo labels, and the one-day schedule favors a complete demo flow over production readiness. The coding agent may choose the simplest suitable local stack and database/schema, documenting its choices before implementation. See [the design overview](../design/design.md) for scope, traceability, and the combined design choices. Do not treat prototype simulations as production security, delivery, reliability, or compliance controls.

## Requirement index

| ID | Requirement | Prototype coverage | Dependencies |
|---|---|---|---|
| CAN-REQ-001 | Organization accounts, authentication, and roles | Required | — |
| CAN-REQ-002 | Organization profile and AI asset inventory | Required | 001 |
| CAN-REQ-003 | Monitoring source configuration | Required | 001 |
| CAN-REQ-004 | External source collection | Required | 003 |
| CAN-REQ-005 | Finding normalization, evidence, and deduplication | Required | 004 |
| CAN-REQ-006 | AI-assisted analysis and factual uncertainty | Required | 005 |
| CAN-REQ-007 | Organization relevance and priority assessment | Required | 002, 006 |
| CAN-REQ-008 | Alert management and investigation workflow | Required | 001, 007 |
| CAN-REQ-009 | Notification rules and delivery | Required | 001, 008 |
| CAN-REQ-010 | Framework-anchored security questionnaire | Required | 001, 002 |
| CAN-REQ-011 | Guided reports and mitigation recommendations | Required | 006, 007, 010 |
| CAN-REQ-012 | Contingency plan lifecycle and human approval | Required | 008, 011 |
| CAN-REQ-013 | Dashboard and monitoring status | Required | 008, 009, 012 |
| CAN-REQ-014 | Audit trail and change history | Required | 001, 008, 012 |
| CAN-REQ-015 | Security, privacy, retention, and safe data handling | Required | all data features |
| CAN-REQ-016 | Demo prototype and sample-data safeguards | Required | 001–015 |

## Shared product rules

- A priority or relevance score is a triage recommendation, not proof of exposure or compromise.
- Keep confirmed facts, source claims, analysis, assumptions, and unknowns distinguishable.
- Preserve source attribution and publication dates; link to the original evidence.
- Generated plans are drafts. Authorized people review, edit, and approve them; the system does not take high-impact action on customer systems.
- Prototype email is actually sent only to explicitly allowlisted team-owned test addresses, with conspicuous test labeling; it is never routed to customers or other non-test recipients.
- Respect source terms, access controls, rate limits, and privacy requirements. Prefer APIs, RSS, and permitted public sources; do not bypass access restrictions.
- Keep each organization's data isolated and access controlled.
- The initial product targets organizations building with or adopting AI tools. Healthcare examples are illustrative and do not establish regulatory compliance.

## Source documents

- `sureh.md` — concise product problem, solution, and differentiators.
- `CANARY_Project_Plan.md` — working product concept, workflows, local prototype sequence, and design principles.

