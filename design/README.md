# Canary Design Phase Overview

This document splits Canary's design into eight areas. Each area traces
back to the requirements in [`../requirements/`](../requirements/README.md).

| # | Design area | Requirements covered |
|---|---|---|
| DES-001 | System architecture | All |
| DES-002 | Data model | CAN-REQ-001, 002, 005, 008, 010, 012, 014 |
| DES-003 | Collection pipeline | CAN-REQ-003, 004, 005 |
| DES-004 | AI analysis layer | CAN-REQ-006, 007, 011 |
| DES-005 | Workflows and state machines | CAN-REQ-008, 012 |
| DES-006 | UX and UI | CAN-REQ-008, 010, 011, 012, 013 |
| DES-007 | Notifications | CAN-REQ-009 |
| DES-008 | Security, privacy, and demo data | CAN-REQ-001, 015, 016 |

------------------------------------------------------------------------

## DES-001: System architecture

- **Components:** Next.js frontend, FastAPI backend, PostgreSQL, a job
  worker (Celery or Redis), the LLM provider, and the email service.
- **Data flow:** collect → normalize → analyze → score → alert → notify.
- **Deployment:** one machine or a hosted service for the hackathon,
  plus how configuration and secrets are handled.

## DES-002: Data model

- **Core records:**
  - Organization, User, Membership
  - InventoryItem
  - Source
  - Finding and SourceRef
  - Alert
  - Assessment and Answer
  - Guide
  - Plan and PlanVersion
  - AuditEvent
- **Isolation:** every table is scoped to an organization (CAN-REQ-015).
- **History:** how version history is stored.
- **Uncertainty:** how values are marked as unknown or unconfirmed.

## DES-003: Collection pipeline

- **Collection:** source adapters for RSS and APIs, a scheduler,
  retries and error logging, and rate limiting.
- **Normalization:** convert every item into one shared finding format.
- **Deduplication:** match by CVE ID, URL, and title similarity.
- **Cadence:** how often to collect is set separately from how often to
  notify.

## DES-004: AI analysis layer

This is the riskiest area, so design and prototype it first.

- **Prompts and output schemas:** facts, interpretation, and unknowns
  are kept separate, and each claim cites its source.
- **Relevance matching:** matching against the inventory is done in
  code, not by the LLM. It produces one of four match states:
  confirmed, possible, industry-only, or no known match.
- **Priority:** a formula with visible factors, adjusted by
  questionnaire answers and current threats.
- **Guides:** step-by-step guide generation, and the rule for when a
  missing fact justifies a follow-up question.
- **Guardrails:** never claim the organization is exposed or
  compromised, and define what happens when evidence is thin.

## DES-005: Workflows and state machines

- **Alert statuses:** New → Under investigation → Exposure confirmed →
  Mitigation in progress → Resolved and verified. An alert can also end
  as Not applicable or Risk accepted.
- **Plan statuses:** Draft → In review → Approved → Archived.
- **Permissions:** which roles can make each change, and what each
  change writes to the audit trail.

## DES-006: UX and UI

- **Screens:**
  - Onboarding and AI inventory
  - Questionnaire
  - Dashboard
  - Alert list and alert detail
  - Guide view
  - Plan editor
  - Settings for sources and recipients
- **Visual language:** priority badges, match-state labels, "AI-generated
  draft" labels, and "Simulated" banners.
- **Wireframes:** based on the
  [Fernwood demo flow](../demo/hallusquatting-demo-flow.md).

## DES-007: Notifications

- **Routing:** recipients chosen by alert category and role.
- **Timing:** immediate sends for critical alerts, digests for
  everything else.
- **Duplicates:** don't re-send an unchanged finding; send an update
  when something meaningful changes.
- **Templates:** email layouts for alerts, updates, and digests.
- **Test mode:** separate test and production modes, with a safety
  switch that only allows mock inboxes.

## DES-008: Security, privacy, and demo data

- **Access:** login provider choice (Auth0 or another), roles enforced on
  the server, and data kept separate for each organization.
- **LLM data:** what customer data is allowed into model prompts.
- **Retention:** how long data is kept and how it's deleted.
- **Demo data:** seed data for Fernwood Labs and Prairie Valley Medical
  Center, labeled as simulated.

------------------------------------------------------------------------

## Suggested order

1. Data model (DES-002) and architecture (DES-001), since everything
   depends on them.
2. AI analysis layer (DES-004), because it's the riskiest.
3. Collection pipeline (DES-003).
4. Workflows (DES-005) and UX (DES-006).
5. Notifications (DES-007).
6. Security (DES-008).
7. Demo seed data.

## Checking the design against the demo

Walk through the
[Fernwood demo flow](../demo/hallusquatting-demo-flow.md) step by step.
Every step should land on a specific component, table, and screen. If
one doesn't, the design is missing something.
