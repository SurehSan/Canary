# Canary Development Methodology

We'll use a short-cycle agile approach organized around the demo and
built in vertical slices. The demo should work early and improve with
every task, instead of coming together at the last minute.

------------------------------------------------------------------------

## 1. Build one thin end-to-end path first

- Before polishing anything, get the
  [Fernwood demo flow](documents/php2shell-demo-flow.md) running from
  start to finish with stubs:
  - a hardcoded organization
  - one RSS source
  - a fake LLM response
  - an alert screen
  - a real test email sent only to an allowlisted, team-owned address
- After that, every task replaces a stub with the real implementation.
- Why: the demo works from early on and only gets better, so a late
  crunch doesn't leave us with half-built layers.

## 2. Short iterations

- Work in cycles of one day, or half a day during the event itself.
- Each cycle ends with a demo-able build and a quick check of what's
  blocking people.
- The requirement docs (`CAN-REQ-xxx`) are the backlog. Work through
  them in the order set by the [design overview](design/design.md):
  1. Data model
  2. AI analysis
  3. Collection pipeline
  4. UX
  5. Notifications

## 3. Split work by layer, with agreed interfaces

- Agree on the data model (DES-002) and the API contracts first.
- Once those are set, people can work in parallel on the frontend, the
  pipeline, the AI analysis, and notifications without blocking each
  other.
- Each design area has one owner.

## 4. Light git workflow

- Keep `main` runnable at all times. It is the demo build.
- Use short-lived feature branches and small pull requests, each
  reviewed by one teammate.
- Name branches and commits after requirements so work traces back to
  the plan, for example `feat/REQ-007-priority`.

## 5. Test where it counts

- **Write tests first** for the logic that the demo's main claims
  depend on:
  - matching findings against the AI inventory
  - the priority formula
  - deduplication
  - alert and plan status transitions
  - the allowlist check that sends real test email only to team-owned
    addresses and rejects every other recipient before sending
- **For the LLM**, save fixed sample inputs and the output format we
  expect, so prompt changes can't silently break the analysis.
- **Write one end-to-end test** that runs the whole Fernwood flow.
- **Don't chase test coverage** on the UI.

## 6. Definition of done

A task is done when:

- [ ] it meets its requirement's acceptance criteria,
- [ ] it works in the end-to-end demo flow,
- [ ] any simulated data is labeled as simulated (CAN-REQ-016), and
- [ ] nothing claims an organization is exposed without evidence
      (CAN-REQ-006, CAN-REQ-007).

## 7. What we're skipping

- Heavy Scrum ceremonies
- Story points
- Long upfront design. The design docs are enough to start, and we
  refine them as we build.

------------------------------------------------------------------------

## Notification policy

Prototype notifications are **real test emails** sent through a locally
configured SMTP provider, and only to an explicit allowlist of team-owned
addresses. Every subject starts with `[CANARY DEMO - TEST]` and every body
carries a test-mode notice. Non-allowlisted recipients are rejected before any
send. If SMTP is not configured or a send fails, the app shows a blocked or
failed state; there is no mock inbox fallback. Automated tests use a local SMTP
capture server and never send to arbitrary addresses.

## Owners and timeline

- **Timeline:** one day (8 hours), following
  [the implementation plan](documents/implementation-plan.md).
- **Claude:** implementation (stack, schema, app, seed/reset, all DES areas).
- **Codex:** test matrix, test implementation, verification, and reporting.
  Codex does not edit application files unless Claude hands off a fix.
