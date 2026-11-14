# Canary One-Day Implementation and Test Plan

## Goal

Build and verify a locally run demo prototype in one day. **Claude owns
implementation. Codex owns test planning, test implementation, verification,
and reporting.** The demo must represent CAN-REQ-001 through CAN-REQ-016 in the
Fernwood Labs hallusquatting walkthrough, using working features or clearly
labeled simulations. This is not a production deployment.

## Quick repository review

The repository currently contains product, design, methodology, and requirement
documents, but no application scaffold or implementation code. The relevant
sources of truth are:

- [Development methodology](../methodology.md): vertical slices, short cycles,
  test the core claims, keep the demo runnable, and use the requirement
  acceptance criteria as the definition of done.
- [Local prototype design](../design/design.md): prototype boundaries,
  technical decisions left to the coding agent, and the required behavior.
- [Requirements index](../requirements/README.md) and CAN-REQ-001 through 016:
  feature requirements and acceptance criteria.
- [Project plan](CANARY_Project_Plan.md): product intent and one-day prototype
  direction.
- [Fernwood demo flow](hallusquatting-demo-flow.md): exact walkthrough,
  score example, role names, seeded data, and test-email behavior.

The methodology has legacy references to `design/README.md`,
`demo/hallusquatting-demo-flow.md`, and a mock inbox. The current paths are
`design/design.md` and `documents/hallusquatting-demo-flow.md`; the current
notification requirement is real test email restricted to an allowlist of
team-owned addresses. Follow the design, requirements, and demo flow where
older methodology text conflicts. At startup, Claude should make a small
methodology update: correct both stale links, replace mock-inbox language with
the current allowlisted real-test-email policy, and record Claude/Codex owners
and the one-day timeline.

## Working agreement

1. **Claude** makes and records the minimum technical choices needed to start:
   local app stack, local database/schema, startup/reset commands, and any
   package/configuration assumptions. Prefer tools already available and the
   shortest reliable path to a local demo. Do not pause for approval on routine
   stack or schema choices.
2. **Codex** first converts the acceptance criteria and demo flow into a
   compact test matrix. Once Claude records the data model and API/interface
   contract, Codex writes tests against those contracts and does not edit
   application implementation files unless Claude explicitly hands off a fix.
3. Keep the default branch runnable at each handoff. Use short-lived branches
   if the agents work in separate checkouts; otherwise make small, named
   commits and avoid simultaneous edits to the same files.
4. Keep AI output deterministic for the seeded demo. OpenAI API use is
   optional; the demo must work without an API key. Do not spend the day tuning
   prompts or pursuing broad test coverage.
5. SMTP credentials and real team-owned test addresses must be configured
   locally before the live email smoke test. Never commit secrets or send to
   non-allowlisted recipients. If configuration is unavailable, test the
   blocked/failure and allowlist behavior and report that real inbox delivery
   could not be verified; do not silently substitute a mock inbox.

## One-day sequence

| Timebox | Claude: implementation | Codex: verification |
|---|---|---|
| 0:00–0:30 | Inspect environment; update methodology paths, notification policy, and owners/timeline. Select stack/schema, record choices and startup commands. Establish shared data/API contract. | Read all CAN-REQ acceptance criteria and create a prioritized test matrix. Identify safe test email configuration and required local secrets. |
| 0:30–1:30 | Create the smallest local app, database, seed/reset path, demo accounts, roles, and Fernwood organization. Keep the app runnable. | Prepare core logic tests from the contract: organization isolation, unknown-version matching, priority calculation, deduplication, and state transitions. |
| 1:30–3:00 | Build the first vertical slice: source records → normalized finding with citations → deterministic analysis → relevance/priority → alert and dashboard. Seed the HalluSquatting reports so the flow works without external network access. | Run focused tests as interfaces land; check seeded output against the demo's expected Possible match and 65/100 P2 score. Report defects with requirement IDs and reproduction steps. |
| 3:00–4:30 | Add inventory/questionnaire history, alert assignment and statuses, targeted guide, plan stages/review/approval, audit events, source health, and demo labels. | Test questionnaire history, role permissions, alert/plan transitions, audit provenance, and reset. Verify each result is organization-scoped. |
| 4:30–5:30 | Add notification routing, SMTP test delivery, explicit recipient allowlist, message labels, delivery log, failure handling, and local configuration documentation. Add any remaining requirement simulations. | Test allowlisted delivery with a controlled SMTP test setup, non-allowlisted rejection, failure reporting, dedup suppression, and digest behavior. Send a real test message only to a configured team-owned address. |
| 5:30–7:30 | Fix high-priority integration defects. Keep the build runnable and the walkthrough data intact. | Run unit/integration tests, start the app from a clean state, and perform the full Fernwood walkthrough. Check all 16 requirements against the traceability matrix. Report pass/fail/blocked with evidence. |
| 7:30–8:00 | Freeze scope; fix only showstopper bugs; update setup, configuration, and known-limitations documentation. | Re-run affected critical tests and the smoke walkthrough. Hand off a concise verification report and any remaining blockers. |

If time compresses, preserve this order: runnable local app → full seeded
vertical slice → test-email safety and delivery → human-reviewed plan →
remaining requirement representations → visual polish. Represent lower-priority
or external behaviors with labeled simulations rather than dropping the
requirement silently.

## Minimum implementation deliverables

- A clean local startup path and documented dependency/configuration setup.
- Local persistent storage with organization scoping, demo seed, and full reset.
- Demo accounts for Administrator Wyatt and Cybersecurity Leads Sureh and
  Koewen; role checks on relevant actions.
- Seeded Fernwood inventory, initial **No** questionnaire assessment, source
  records and HalluSquatting finding, with real source URLs/dates preserved.
- Finding detail that separates source facts, interpretation, and unknowns;
  deduplication preserves all citations.
- Explainable match and priority result: Possible, 65/100, P2. Unknown version
  must not yield a Confirmed match; P1 requires the documented gate.
- Working alert investigation, targeted guide, contingency plan review and
  Administrator approval, dashboard, and audit history.
- Real SMTP test email only to the configured team-owned allowlist, with
  `[CANARY DEMO - TEST]` in the subject and test notice in the body. Non-listed
  recipients must be rejected; failed sends must remain failures in the UI.
- Visible Demo data labels, privacy boundaries, error states, and reset control.
- A README section recording the chosen stack/schema, startup/reset commands,
  environment variables, test commands, demo steps, and known limitations.

## Codex test matrix

Codex should prioritize the logic behind the demo's claims, then run the full
walkthrough:

1. **Identity and isolation (001, 002, 015):** role permissions, revoked
   membership, selected-organization scoping, and denial of cross-organization
   reads/writes.
2. **Sources and finding lifecycle (003–006):** source status/error distinction,
   collection metadata, idempotent collection, canonical grouping, source
   preservation, conflict/unknown handling, analysis schema and citation
   validation.
3. **Matching and priority (007):** known version overlap, unknown version,
   Possible/industry-only/no-match cases, exact score bands, P1 gate, and
   reasoned override. Confirm the seeded example is Possible / 65 / P2.
4. **Workflows and advice (008, 010–012, 014):** assignment, permitted status
   transitions, evidence requirement for Exposure confirmed, targeted question
   and Unknown behavior, assessment history, plan approval authorization,
   version history, and audit provenance.
5. **Email safety (009, 015):** allowlist enforcement before send, correct
   recipients and test labels, no production route, accurate success/failure
   logging, unchanged-message suppression, material update, retry, and digest.
6. **Dashboard and demo safeguards (013, 016):** counts derive from stored
   records, failure/staleness is visible, sample data is labeled, reset restores
   seed state, and the application makes no exposure/compliance claim unsupported
   by evidence.
7. **End-to-end:** start from documented setup, run the complete Fernwood demo
   in order, and confirm every requirement is shown in a feature or labeled
   simulation.

Use a local SMTP capture/test server for automated email assertions. Verify
actual inbox delivery as a separate manual smoke check only when team-owned
test credentials and a recipient are configured. Do not let automated tests
send email to an unconfigured or arbitrary address.

## Handoff and definition of done

Claude hands Codex the running commit, setup instructions, chosen schema and
interfaces, seeded demo credentials (stored safely/documented for local demo),
and a list of simulated requirements. Codex returns:

- Commands run and environment used.
- Test names/results grouped by requirement ID.
- Full-demo smoke result and any steps that required manual intervention.
- Real email result, or explicit blocked reason if configuration was absent.
- Defects grouped by blocker/high/medium and reproducible steps.
- Requirements represented only by simulations and known limitations.

The prototype is ready to present when it starts locally from the documented
instructions, completes the Fernwood flow end to end, sends real test email
only to the allowlisted address when configured, preserves uncertainty and
human approval, and has no unresolved blocker in the walkthrough. Any failed
or unverified acceptance criterion must be reported honestly; do not mark a
requirement complete solely because a screen exists.
