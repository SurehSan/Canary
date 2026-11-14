# Canary code review handoff (2026-11-14)

## Executive handoff for Claude

Slices 1–3 are represented in the current code and have substantial unit and acceptance-test coverage, but this review did not execute the test suite or walkthrough. The repo is ready to continue slice 4. The six slice-4 items called out in the review guide remain unbuilt: analysis correction UI, organization/profile/inventory editing, organization creation, simulated invites, role changes, and the privacy/data-flow disclosure page.

Please include tests for the new routes, org boundaries, audit provenance, and unknown-value handling as those features land. Also address or explicitly rule on CDX-1 and CDX-2 below. No blocker was established by this static review; runtime behavior remains unverified.

## 1. Commands run and environment

- OS: Windows (PowerShell; workspace `C:\Users\DSU Student\Desktop\Canary`).
- Python: 3.13.5.
- Review guide and implementation plan read; inspected the README, demo flow, requirement index and requirements 001, 002, 006, and 015; reviewed current application modules and existing tests.
- Git status/log were read using `git -c safe.directory=...` because Git otherwise rejected the workspace ownership. The requested review branch could not be created because `.git` is read-only in this environment. The report is on the current `main` worktree; no app code or existing tests were modified.
- Environment: no `CANARY_*` variables were set in the review shell. No SMTP configuration or team test inbox was available.
- No pytest command, app startup, scheduler run, live-source fetch, or manual walkthrough was run. This is a source and existing-test review, not a verification pass.

## 2. Test results grouped by requirement

“Covered” below means an existing test is present and appears to assert the named behavior; it does not mean the test was run in this review.

| Requirement | Existing coverage / current status |
|---|---|
| 001 | `tests/test_access.py`: wrong password, role denial, org selection, cross-org alert read/write, revoked-member access. Create organization, simulated invite, and role change are **not built yet**. |
| 002 | `tests/test_access.py::test_inventory_shows_unknown_version_explicitly`; profile and inventory editing are **not built yet**. |
| 003 | `tests/test_slice.py::test_disabled_source_is_not_collected`; source configuration and outage behavior are also covered by `tests/test_slice.py`. |
| 004 | `tests/test_slice.py::test_refresh_collects_sources_with_url_dates_and_outcome`, `test_recollection_is_idempotent`, and `test_simulated_outage_is_failure_not_empty_success`; live adapter has injected-HTTP tests in `tests/test_live.py`. Not run. |
| 005 | `tests/test_normalize.py` covers canonicalization, exact duplicates, and proposed grouping; `tests/test_slice.py` covers source preservation/grouping and confirm/undo. Cross-organization effects of the global grouping state were not exercised. |
| 006 | `tests/test_analysis.py` covers fact/unknown separation, citations, conflict, exposure language, and validation. Authorized analysis correction/provenance is **not built yet**. |
| 007 | `tests/test_scoring.py` covers match states, unknown version, industry-only, score bands, P1 gate, seeded 65/P2, and duplicate penalty as a pure scoring input. Not run. |
| 008 | `tests/test_workflow.py` covers transitions and evidence note; `tests/test_slice.py` covers assignment/status. Cross-org alert denial is in `tests/test_access.py`. |
| 009 | `tests/test_notifications.py` covers allowlist, missing address/config, SMTP refusal, retry, dedup, updates, digest, and role permissions; `tests/test_notify_unit.py` covers content, allowlist parsing, cadence, and fingerprint. Missing specific coverage: rejected retry/digest must never connect; SMTP exception text must not disclose secrets; digest-batch retry consistency. Real inbox is blocked (see section 4). |
| 010 | `tests/test_guide_plan.py` covers saved assessment history, validation, framework mapping, and weighting. |
| 011 | `tests/test_guide_unit.py` and `tests/test_guide_plan.py` cover target question, unknown/yes condition, links, edits/progress, and org denial. |
| 012 | `tests/test_guide_plan.py` covers approval authorization, review/edit restrictions, approved snapshot, active owners, and dashboard counts. No explicit no-op edit or archived-edit assertion was found. |
| 013 | `tests/test_slice.py::test_dashboard_counts_derive_from_records` and `tests/test_guide_plan.py::test_dashboard_counts_open_plans_and_plan_awaiting_approval`; scheduler concurrency is unverified. |
| 014 | Audit assertions exist in `tests/test_slice.py`, `tests/test_guide_plan.py`, and `tests/test_notifications.py`; `tests/test_e2e_fernwood.py` checks key walkthrough audit actions. Not run. |
| 015 | Access tests cover selected-org scoping/revocation; notification tests check password absence from pages/database in ordinary successful flow. Privacy/data-flow disclosure page is **not built yet**. CSRF and cookie behavior have no tests. |
| 016 | Labels and reset are covered in `tests/test_access.py`, `tests/test_slice.py`, and `tests/test_e2e_fernwood.py`; the end-to-end test exists but was not run. |

## 3. Full-demo smoke result

**Not run.** The app was not started or reset, and no walkthrough step is claimed as passed. `tests/test_e2e_fernwood.py::test_full_fernwood_walkthrough` is the existing automated walkthrough, but it was not executed. The guide's score expectation (Possible, 65/100, P2) is asserted in `tests/test_scoring.py` and `tests/test_slice.py`; it was not independently observed in a running app during this review.

## 4. Real email result

**Blocked: no SMTP configuration.** No SMTP host/from address, allowlisted team-owned recipient, or inbox credentials were configured. No email was sent. Automated capture-server coverage is present in `tests/test_notifications.py`, but those tests were not run here.

## 5. Findings

### CDX-1: Source outage simulation is global across organizations

Severity: Medium  
Requirement: CAN-REQ-003 — “An administrator can enable or disable monitoring sources for their organization.”  
Location: `canary/views.py:235-243`; global field in `canary/schema.sql:93`; collection uses the global catalog row in `canary/collector.py:43-52`.

Steps to reproduce:

1. Run `python run.py --reset`, then `python run.py`.
2. Sign in as `priya` in Prairie Valley and turn on “Simulate outage” for a catalog source.
3. Sign in as `wyatt` in Fernwood and refresh sources.

Expected: A demo outage initiated by an organization administrator affects only that organization's simulation, or the UI clearly identifies it as a system-wide simulation controlled outside the organization.

Actual: The POST changes `source_catalog.simulate_failure`, a global catalog field. `run_collection` fetches each source row once if any organization has enabled it, so the simulation affects the collection outcome observed by other organizations too. The audit event is attributed only to the initiating organization.

Evidence: Static code path above; not reproduced at runtime. Existing outage test (`tests/test_slice.py::test_simulated_outage_is_failure_not_empty_success`) checks the failure state but not cross-org impact.

Suggested fix (no code changes): Store outage simulation state per organization, or make the UI and audit clearly describe this as a global system-level demo switch and restrict it accordingly. Add a Prairie Valley-to-Fernwood isolation test after choosing the intended behavior.

### CDX-2: SMTP exception text is persisted verbatim to notification and audit records

Severity: Low  
Requirement: CAN-REQ-015 — “Third-party data flows (including model and email providers) are inventoried and configured to minimize customer data exposure.”  
Location: `canary/delivery.py:141-155`.

Steps to reproduce:

1. Run `python run.py --reset` and configure an allowlisted test recipient plus a test SMTP endpoint that returns a deliberately sensitive authentication error response.
2. Trigger a notification send that reaches SMTP and inspect `notifications.error` and the corresponding audit summary.

Expected: Persist a bounded, sanitized SMTP error category/status; provider-controlled response text must not be able to put credentials or other sensitive values in the database, UI, or audit log.

Actual: `dispatch` stores `str(exc)[:200]` in `notifications.error` and includes the same string in the audit summary. The current password test only checks a successful send path (`tests/test_notifications.py::test_smtp_password_never_appears_in_pages_or_database`); no exception-path secret check exists. This is a conditional exposure risk, not evidence that the configured provider currently returns the password.

Evidence: Static code inspection; not reproduced against SMTP. 

Suggested fix (no code changes): Store the exception class and safe SMTP response code only, or map failures to sanitized user-facing categories. Add an injected exception test that includes a sentinel secret and asserts it is absent from the notification row, page, and audit log.

### Slice 4 acceptance criteria: not built yet

These are planned work, not regressions in slices 1–3:

- **CAN-REQ-006:** authorized users can correct analysis; correction provenance includes prior value, editor, timestamp, and reason. No correction route/UI or correction-specific test was found.
- **CAN-REQ-002:** users can create/edit/remove inventory and edit the organization profile; no write forms/routes were found.
- **CAN-REQ-001:** create an organization with the creator as admin, simulate an invite to a seeded user, and assign/change role. No create-org, invite, or role-change routes were found. Existing membership revocation is implemented.
- **CAN-REQ-015:** privacy/data-flow disclosure page is absent. The README documents some boundaries, but there is no in-app disclosure page.

## 6. Rulings

### Review-focus rulings

1. **Global state — finding (CDX-1).** The source outage switch is stored globally and a collection run is global. Organization administrators can therefore change another organization's observed source outcome. Follow-up evidence and grouping also mutate global findings/source items, as documented in the README; because source evidence is shared globally, that is a coherent data model, but the UI should say that the change affects all organizations receiving the finding and the audit trail should make the system-wide scope clear. No cross-org test was run.
2. **Cross-organization access — stands for reviewed routes; coverage gap remains.** Alert lookup includes `org_id`; guide and plan lookups do too; notification retry includes `org_id`; revoke-member lookup scopes to current `org_id`; grouping first checks the org-scoped alert and then requires the item to belong to that alert's finding. Existing tests cover only some routes. Full GET/POST route matrix has not been run, and missing route-level tests are not proof of a defect.
3. **Revocation mid-session — stands by inspection.** `load_user` rechecks active membership before each request and clears selected organization if revoked. Alert owner and plan owner queries also filter active members. Existing revocation coverage is in `tests/test_access.py::test_revoked_member_loses_access`. Not run.
4. **Email safety ordering — partial finding.** `_precheck` enforces recipient allowlist before SMTP setup and is called by `dispatch`, including retry and digest dispatch. Existing tests cover normal non-allowlisted send and empty allowlist. The retry/digest no-connection cases and digest batch consistency are not tested. Exception text persistence is CDX-2.
5. **CSRF — stands for the documented local-only demo boundary, with a clear production limitation.** No CSRF token is implemented, and Flask's SameSite setting is not explicitly configured. The documented app binds to loopback and uses fictional/demo data; the guide explicitly asks to grade this for the local demo. This is not a slice-4 blocker, but a hosted or shared-network deployment would require CSRF defenses and deliberate cookie settings.
6. **Untrusted RSS — partial / unverified.** Code caps the response read at 2 MB, filters links to `http://` or `https://`, strips markup from excerpts, and Jinja templates autoescape rendered text by default. `tests/test_live.py` covers ordinary parsing and relevance, not entity expansion, oversized/truncated XML, or unsafe schemes. No hostile-input claim is made without those checks.
7. **Scoring determinism — stands for tested rubric logic; duplicate-pipeline question is not a demonstrated defect.** Pure-function tests cover boundaries, P1 gate, unknown version, industry-only, and the -10 penalty. The pipeline always passes `duplicate_without_new_info=False`; exact duplicates are normalized upstream and re-collection is idempotent. Confirm whether the product intends any non-exact duplicate to incur the penalty; if so, add a concrete detection rule and pipeline test. Current score does not use that penalty.
8. **Update/suppression and reviewer override — stands by code path, with test gaps.** Fingerprints include priority, match state, exploitation, affected products, and source URLs; override columns are not overwritten by reassessment. Existing tests cover unchanged grouping suppression, follow-up update, and priority override. Re-collection and questionnaire reassessment scenarios are not comprehensively tested.
9. **Plan lifecycle — mostly stands.** Code rejects edits for archived plans, compares before/after snapshots to avoid no-op versions, validates active owners, and stores approved snapshots. Tests cover review lock, approved snapshot preservation, and active owner changes. Explicit no-op and archived-edit tests were not found.
10. **Scheduler concurrency — untested.** The scheduler can share the SQLite DB with request handlers. No scheduler-enabled smoke/concurrency run was performed and no lock failure is claimed.
11. **Labels and claims — stands by static search.** The app banner and views label fictional/demo data and simulations; alert text says triage is not proof of exposure/compromise. Static search found no IBM 43% claim or prohibited GitHub issue-title claim in `canary/`. Search is not a runtime/browser verification.

### Claude's implementation rulings

1. Stack: **stands** — matches the local prototype plan and documented no-new-dependency choice.
2. Rubric sub-scales/source tiers: **stands provisionally** — match the documented seeded arithmetic; tests assert 65/P2. Real-world source-quality validation was outside this code review.
3. CSA/THN exploitation conflict scored `research_demonstrated`: **stands provisionally** — deterministic analysis surfaces conflict; tests assert conflict behavior. The evidence judgment is a product/source review matter beyond code correctness.
4. THN/CSA proposed grouping: **stands** — alias-based grouping is explicitly proposed and user-confirmed/undoable; tests cover the proposal classification and grouping actions.
5. Offline default and opt-in THN RSS: **stands by code/config inspection** — live mode defaults off, injects `HTTP_GET` in tests, and the adapter has a 15-minute interval check. Network behavior was not run.
6. Xygeni as labeled source-less demo step: **stands** — source UI marks it as a demo step not collected by a catalog source; source-less follow-up appears in code and tests.
7. Notification statuses: **stands by code and existing tests** — missing address/config is blocked, off-list is rejected, simulated failure is flagged. Tests not run.
8. Reviewer override may set any priority including P1 and sends immediately: **stands** — existing test covers P1 immediate notification; the override is visibly attributed and reason-required in code/tests.
9. Guide question wording and capability suppression: **stands** — guide unit tests cover targeted question and existing inventory answer suppression.
10. In-review plan edit restriction and approved-version retention: **stands** — explicit route guard and approved snapshot tests exist.
11. Questionnaire reassessment rescores findings: **stands by code inspection** — submission calls `process_findings` for that organization's known relevance rows. Notification dedup behavior after repeated reassessments has partial coverage only.

## 7. Simulation-only requirements and known limitations

- Demo authentication uses seeded accounts and shared demo credentials; there is no SSO/MFA/account recovery.
- Analysis is deterministic demo logic; no model provider is connected. Analysis correction UI is pending.
- Source outage and delivery failure are labeled simulations; Xygeni is a simulated follow-up step.
- Invites are described in the UI as simulated but invite creation itself, organization creation, and role change are not yet implemented.
- Real SMTP inbox delivery is not verified and was blocked in this environment.
- Privacy/data-flow disclosure page is pending. CSRF protections are absent, which is acceptable only within the documented loopback demo boundary.
- Scheduler concurrency, hostile RSS input, complete route-by-route authorization matrix, and full manual walkthrough remain unverified.
- Audit history is application data, not tamper-proof storage; local prototype is not production-hardened and makes no compliance claim.
