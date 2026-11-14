# CAN-REQ-016: MVP Demonstration and Sample-Data Safeguards

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§3, 10, 11

## Purpose
Demonstrate Canary's end-to-end value with a realistic workflow without misleading users about fictional or simulated information.

## Requirements
1. The MVP can demonstrate organization setup, AI inventory/questionnaire entry, source finding intake, analysis, alert delivery/viewing, report or plan creation, human review, and saved dashboard state.
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

## Open decisions
- Which sample real advisory to use, demo reset strategy, and whether the demo environment is local, hosted, or seeded.
