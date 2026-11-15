# CAN-REQ-016: Demo Prototype and Sample-Data Safeguards

**Status:** Proposed · **Priority:** Local demo prototype · **Source:** Project Plan §§3, 10, 11

## Purpose
Demonstrate Canary's end-to-end value with a realistic workflow without misleading users about fictional or simulated information.

## Requirements
1. The local prototype can demonstrate organization setup, AI inventory/questionnaire entry, source finding intake, analysis, mock alert delivery/viewing, report or plan creation, human review, and saved dashboard state.
2. Prairie Valley Medical Center may be used as a fictional demonstration organization; its data must be labeled as fictional.
3. Simulated incidents, vulnerabilities, assets, and advisories must be conspicuously labeled as simulated and must not be presented as real threats.
4. When using a real advisory, the demonstration preserves the authoritative source link and dates and does not alter the source's claims.
5. The end-to-end demonstration must show that uncertain relevance stays uncertain and that a generated plan requires authorized human approval.
6. Marketing or demo materials must not repeat the IBM 43% claim or GitHub issue-title incident as verified facts until primary sources and exact wording have been checked, as called out in the working documents.

## Acceptance criteria
- A new demo organization can complete the workflow from setup through approved or edited plan.
- Demo-only records are visibly marked and segregated from real collected records.
- A real finding links to its source; a simulated finding cannot be mistaken for one.
- The cited IBM and GitHub examples are either verified against primary sources before presentation or omitted.

## Dependencies
CAN-REQ-001 through CAN-REQ-015.

## Prototype design decisions
- Run the demo locally and seed Fernwood Labs as the primary walkthrough organization, following `documents/php2shell-demo-flow.md`. Prairie Valley Medical Center may be included as a second fictional sample to demonstrate another organization context; it is not the primary flow.
- Use the hallusquatting sources and preserve their original links and publication dates. Treat claims according to the cited sources; label any invented Fernwood assets, package events, and outcomes as fictional/simulated. Do not alter a real source's claims.
- Provide a visible “Demo data” banner and distinguish simulated/sample records from collected source records. Provide a full reset to restore the seeded state and remove user changes.
- Demonstrate all CAN-REQ-001–015 in the walkthrough or through an adjacent screen/state: accounts and roles, organization/inventory, source settings and status, collection, normalization/evidence/deduplication, analysis, relevance/priority, alert triage, mock notification, questionnaire, guide, human-approved plan, dashboard, audit history, and privacy/data safeguards.
- Do not present the IBM 43% or GitHub issue-title examples as verified until checked against primary sources. Their omission does not block the hallusquatting prototype.

## Amendment 2026-11-14: presentation mode
At the team's request, an opt-in `CANARY_PRESENTATION_MODE=1` setting gives the web app a product-like look for
live presentations. With it on:
- The demo banner and the "fictional" and "Demo data" tags are hidden.
- A subtle "Sample workspace" marker stays in the header.
- Scripted events move to an Administrator-only "Presenter tools" panel.

Truthfulness text stays in both modes: "AI-generated draft for human review", "a score is triage, not proof of
exposure", "approval executes nothing", and "Simulated" markers on presenter-triggered failures. The default
(off) keeps every label this requirement specifies. When presentation mode is used, the presenter states once,
out loud, that the workspace and people are fictional (see documents/demo-script.md).

## Amendment 2026-11-14: PHP2Shell demo scenario
At the team's request, the seeded walkthrough uses the real **PHP2Shell** vulnerability (CVE-2026-109618,
CVE-2026-109619) instead of hallusquatting; see `documents/php2shell-demo-flow.md`.

- **Sources (checked 2026-11-14):** the php.net advisory, the two php-src GitHub advisories, The Hacker News (21
  Oct 2026), and Check Point's 12 Nov 2026 advisory confirming in-the-wild exploitation (the follow-up evidence).
  Their titles, links, and dates are preserved, and their claims are not altered.
- **Fictional details:** Fernwood's billing portal and its PHP version are fictional demo context.
