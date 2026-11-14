# Canary Requirements

This folder turns the working concept in `sureh.md` and `CANARY_Project_Plan.md` into implementation-ready requirement documents for an agent or development team.

## How to use these documents

Implement requirements in dependency order where practical. Each document defines one capability, its purpose, scope, functional requirements, acceptance criteria, dependencies, and unresolved decisions. Acceptance criteria are intended to be verifiable; they do not prescribe a specific framework unless the source plan does.

The project plan is a working concept, so details that it does not settle are marked **Open decision** rather than treated as product facts. The suggested stack is not binding. Avoid treating sample customers, incidents, inventories, or advisories as real data. Any demo data must be labeled.

## Requirement index

| ID | Requirement | Suggested priority | Dependencies |
|---|---|---|---|
| CAN-REQ-001 | Organization accounts, authentication, and roles | MVP | — |
| CAN-REQ-002 | Organization profile and AI asset inventory | MVP | 001 |
| CAN-REQ-003 | Monitoring source configuration | MVP | 001 |
| CAN-REQ-004 | External source collection | MVP | 003 |
| CAN-REQ-005 | Finding normalization, evidence, and deduplication | MVP | 004 |
| CAN-REQ-006 | AI-assisted analysis and factual uncertainty | MVP | 005 |
| CAN-REQ-007 | Organization relevance and priority assessment | MVP | 002, 006 |
| CAN-REQ-008 | Alert management and investigation workflow | MVP | 001, 007 |
| CAN-REQ-009 | Notification rules and delivery | MVP | 001, 008 |
| CAN-REQ-010 | Framework-anchored security questionnaire | MVP | 001, 002 |
| CAN-REQ-011 | Guided reports and mitigation recommendations | MVP | 006, 007, 010 |
| CAN-REQ-012 | Contingency plan lifecycle and human approval | MVP | 008, 011 |
| CAN-REQ-013 | Dashboard and monitoring status | MVP | 008, 009, 012 |
| CAN-REQ-014 | Audit trail and change history | MVP | 001, 008, 012 |
| CAN-REQ-015 | Security, privacy, retention, and safe data handling | MVP | all data features |
| CAN-REQ-016 | MVP demonstration and sample-data safeguards | MVP | 001–015 |

## Shared product rules

- A priority or relevance score is a triage recommendation, not proof of exposure or compromise.
- Keep confirmed facts, source claims, analysis, assumptions, and unknowns distinguishable.
- Preserve source attribution and publication dates; link to the original evidence.
- Generated plans are drafts. Authorized people review, edit, and approve them; the system does not take high-impact action on customer systems.
- Respect source terms, access controls, rate limits, and privacy requirements. Prefer APIs, RSS, and permitted public sources; do not bypass access restrictions.
- Keep each organization's data isolated and access controlled.
- The initial product targets organizations building with or adopting AI tools. Healthcare examples are illustrative and do not establish regulatory compliance.

## Source documents

- `sureh.md` — concise product problem, solution, and differentiators.
- `CANARY_Project_Plan.md` — working product concept, workflows, MVP sequence, and design principles.

