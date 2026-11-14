# Canary runtime verification report

Date: 2026-11-14  
Commit reviewed: `28a2868` (slice 4 and review fixes)  
Method: HTTP walkthrough using `requests.Session` against `http://127.0.0.1:5000`; SQLite observations; pytest; local SMTP capture. No browser was used.

## 1. Commands run and environment

| Command / check | Observed result |
|---|---|
| `python --version` | `Python 3.13.5` |
| `python -c "import flask, pytest; print(flask.__version__, pytest.__version__)"` | Flask `3.1.3`, pytest `8.3.4`; Flask emitted a deprecation warning for `__version__`. |
| `python -c "import requests; print(requests.__version__)"` | `2.32.3` |
| `Get-ChildItem env:CANARY_* -ErrorAction SilentlyContinue` | No variables listed before the controlled capture run. |
| `Test-Path .env` | `False` |
| `python run.py --reset` | `Demo data reset to seed state.` |
| `python -m pytest -p no:cacheprovider -q` | First sandbox attempt hit `PermissionError: [WinError 5]` scanning the default pytest Temp directory. The approved rerun reached 100% with no failure indicators. |
| `python -m pytest -p no:cacheprovider -q -o addopts=` | `172 passed in 43.84s`, exit code 0. This changes only pytest's configured duplicate `-q`, so pytest prints the summary. |
| `python tests/codex/http_walkthrough.py` | Completed both HTTP runs. W1–W17 passed in both runs, except W8 was Blocked in the no-SMTP run as expected. The separate new-organization workflow check failed in both runs (CDX-3). |
| `python tests/codex/scheduler_smoke.py` | 193.2 seconds, 76 active HTTP requests, one queued notification processed as Rejected/attempt 1, no scheduler errors. |
| `python run.py --reset` + SQLite count query | Before: 2 organizations, 1 alert, 0 plans, 6 inventory items, 1 assessment, 45 audit rows. After: 2 organizations, 0 alerts, 0 plans, 6 inventory items, 1 assessment, 2 seed audit rows. |

The app bound to loopback only. `CANARY_SCHEDULER=0` was used for walkthrough runs; the scheduler check used `CANARY_SCHEDULER=1` with live RSS off. The capture run set SMTP host to the local capture server and allowlisted only `sureh-test@team.example`; no real email provider or inbox was used. The `main` worktree was used. Git metadata is read-only in this environment, so the report and helper files are uncommitted and no branch or commit was created. Existing unrelated worktree entries (`D file_000000008bec81f5806122c29bbb38a2.png`, `?? design/logo.png`) were left untouched.

## 2. Automated results

All 172 collected tests passed, including the four independent checks in `tests/codex/test_runtime_verification.py`.

| Test file | Result |
|---|---:|
| `tests/codex/test_runtime_verification.py` | 4 passed |
| `tests/test_access.py` | 8 passed |
| `tests/test_analysis.py` | 8 passed |
| `tests/test_e2e_fernwood.py` | 1 passed |
| `tests/test_guide_plan.py` | 18 passed |
| `tests/test_guide_unit.py` | 6 passed |
| `tests/test_live.py` | 6 passed |
| `tests/test_normalize.py` | 7 passed |
| `tests/test_notifications.py` | 16 passed |
| `tests/test_notify_unit.py` | 7 passed |
| `tests/test_review_fixes.py` | 4 passed |
| `tests/test_review_gaps.py` | 31 passed |
| `tests/test_scheduler.py` | 2 passed |
| `tests/test_scoring.py` | 12 passed |
| `tests/test_slice.py` | 13 passed |
| `tests/test_slice4_features.py` | 25 passed |
| `tests/test_workflow.py` | 4 passed |
| **Total** | **172 passed** |

The four independent checks were:

- Fernwood's GHSA outage did not show as Failed for Prairie Valley, and Fernwood received no GHSA items during its simulated failure.
- An exact product-key match with an Unknown version returned Possible, never Confirmed.
- A corrected analysis statement appeared in the material follow-up email captured locally; the correction alone did not send an email.
- Invite → revoke → re-invite changed status/role as expected and produced audit events.

## 3. Walkthrough

Both runs started from `python run.py --reset`, used the real app over HTTP, and ended with the reset check. “Run 1” had no SMTP configuration. “Run 2” used the local capture server; capture evidence is not real inbox delivery.

| Step | Run 1: no SMTP | Run 2: local SMTP capture |
|---|---|---|
| W1 Organization and roles | **Pass** — demo banner, Unknown runtime version, Wyatt/Sureh/Koewen, and initial No assessment observed. | **Pass** — same. |
| W2 Sources and refresh | **Pass** — four sources; THN/CSA success, two items; GHSA/OWASP successful no-new-record checks; separate cadences shown. | **Pass** — same. |
| W3 Per-org GHSA outage | **Pass** — Fernwood failure after 3 attempts; Prairie Valley did not show Failed. Outage was turned off. | **Pass** — same. |
| W4 Normalized finding | **Pass** — one finding; THN/CSA dates preserved; Proposed grouping and shared-evidence notice visible. | **Pass** — same. |
| W5 Analysis | **Pass** — source-supported/context/unknown/interpretation/conflict sections and demo label present; no claim Fernwood is exposed or compromised. | **Pass** — same. |
| W6 Relevance and score | **Pass** — Possible, 65/100, P2 High; factor values 16/8/12/15/9/5 and the P1 gate reason observed. | **Pass** — same. |
| W7 Email and allowlist | **Pass** — P2 was Blocked with no address, then Rejected after adding an address and retrying; off-list check was Rejected. | **Pass** — P2 Sent to the allowlisted capture recipient; off-list check was Rejected with no capture-server connection. |
| W8 Simulated send failure and retry | **Blocked** — requires an SMTP endpoint. | **Pass** — Failed (simulated), then Retry Sent at attempt 2. |
| W9 Xygeni follow-up | **Pass** — third source and material update; queued update ended Blocked/Rejected. | **Pass** — third source and Update email captured. |
| W10 Alert, guide, and question | **Pass** — Sureh assigned/investigating; five-step guide; Unknown left step 4 conditional and step 1 marked in progress. | **Pass** — same. |
| W11 Plan review/approval | **Pass** — Lead approval returned 403; Wyatt approved; applicable stages, Koewen owner, audit event, and no-execution notice verified. | **Pass** — same. |
| W12 Analysis correction | **Pass** — corrected text, reason/editor/date, correction history and correction row observed. | **Pass** — same. |
| W13 Profile/inventory edits | **Pass** — profile size cleared to Unknown; blank-version item stored as Unknown, then edited; audit changes observed. | **Pass** — same. |
| W14 Registration/org/invite/role | **Pass** — new account created an organization as Admin; last-admin demotion returned 400; invite and role change audited; Koewen opened the organization. | **Pass** — same. |
| W15 Privacy/data flows | **Pass** — current SMTP status, Live RSS off, no model provider, reset retention, and no-compliance boundary observed. | **Pass** — same disclosures with SMTP configured to the local capture endpoint. |
| W16 Cross-org IDs | **Pass** — Prairie Valley received 404 for Fernwood alert, guide, plan and POST; Fernwood alert was unchanged. | **Pass** — same. |
| W17 Closeout/reset | **Pass** — alert resolved with note; No and Yes assessments retained before reset; reset removed entered records and restored two seed organizations. | **Pass** — same. |

Additional check tied to CAN-REQ-016, run in both walkthroughs: after creating a fresh organization, adding an AI coding-agent inventory item, and refreshing sources already collected for Fernwood, the new organization had **0 alerts**. It therefore could not proceed to a guide or plan. See CDX-3.

## 4. Email

- **Real inbox delivery: Blocked.** No team SMTP account or team-owned inbox was available, and none was contacted.
- **Local SMTP capture, not a real inbox:** captured 3 messages in the capture run: initial P2, follow-up Update, and simulated-failure Retry. The capture server saw only `sureh-test@team.example`. A delivery check to an off-list address was Rejected without opening a capture-server connection.
- **No-SMTP run:** P2 was Blocked while Sureh had no test address. After entering an address, retry was Rejected because the allowlist was empty. The separate off-list delivery check was also Rejected.

## 5. Defects

### CDX-3: Newly created organizations do not assess already-collected findings

Severity: Medium  
Requirement: CAN-REQ-016 — “A new demo organization can complete the workflow from setup through approved or edited plan.”  
Location: `canary/admin_views.py:29-34` (`_reassess_org` only selects existing relevance rows); `canary/collector.py:43-53, 124-136` (collection processes touched findings; already-known canonical URLs are skipped).

Steps to reproduce:

1. Run `python run.py --reset`, then start the app with `CANARY_SCHEDULER=0`.
2. Register a new local demo account and create a new organization.
3. Add an inventory item with `ai_coding_agent, auto_install_packages` capability tags and High criticality.
4. Refresh sources after Fernwood has already collected the fixture items.
5. Open the new organization's Alerts page.

Expected: The new organization's enabled sources make already-stored shared findings eligible for that organization's analysis. With matching inventory, the user can open an alert and continue to a guide and plan.

Actual: The new organization has 0 alerts. Refresh skips the already-known source URLs, returns no touched findings, and does not run organization relevance for those findings. Inventory reassessment also selects only finding IDs already present in that organization's `relevance` rows, which are initially empty. The workflow has no alert from which to create a guide or plan.

Evidence: `tests/codex/http_walkthrough.py` recorded alert count `0` after this sequence in both HTTP runs. The same result was observed twice, once without SMTP and once with local SMTP capture. This does not block the seeded Fernwood walkthrough, but it leaves the explicit new-organization acceptance criterion unmet.

Suggested fix (no code changes): When an organization is created, or when its inventory/source settings change, assess existing shared findings available through its enabled sources even if the organization has no prior relevance rows. Add a regression test that creates a second org after fixture collection and verifies a relevant inventory item produces an alert.

## 6. Traceability matrix

Statuses use the guide's definitions. “Pass” means the stated test/HTTP observation succeeded. “Simulated” marks behavior intentionally represented by a labeled deterministic or demo path. “Blocked” marks an external check unavailable here. Acceptance points are abbreviated; their source is the corresponding CAN-REQ document.

| Criterion | Status | Evidence |
|---|---|---|
| 001 — New user creates an organization and accesses its workspace | Pass | W14; `test_new_user_registers_and_creates_org_as_admin` |
| 001 — Admin invites a second user and assigns a role | Pass | W14; `test_admin_invites_existing_user_and_changes_role`; independent invite/revoke/re-invite check |
| 001 — Different roles receive only assigned capabilities | Pass | W11 Lead approval 403; `test_lead_cannot_invite_or_change_roles`, `test_lead_cannot_approve_and_admin_must_confirm` |
| 001 — Revoked member cannot read or modify protected data | Pass | `test_revoked_member_loses_access`; `test_invite_reactivates_revoked_member` |
| 001 — Automated checks cover cross-org access | Pass | `test_other_org_admin_gets_404_on_every_id_route` (20-route matrix); W16 |
| 002 — Organization profile and inventory can be saved/edited | Pass | W13; `test_admin_edits_profile_with_unknowns_and_audit`, `test_inventory_edit_and_delete_are_audited_and_rescore` |
| 002 — Inventory links teams/criticality when supplied | Pass | W13; inventory form values persisted; `test_inventory_edit_and_delete_are_audited_and_rescore` |
| 002 — Missing version remains Unknown and cannot produce positive version match | Pass | W13 and independent `test_unknown_version_exact_product_match_stays_possible` |
| 002 — Different org cannot access profile/inventory | Pass | `test_other_org_cannot_edit_or_delete_inventory`; W16 org boundary checks |
| 003 — Admin sees enabled sources and recent status | Pass | W2/W3 source pages |
| 003 — Disabling source stops collection for that org | Pass | `test_disabled_source_is_not_collected` |
| 003 — Outage/rate limit is visible, not empty success | Pass | W3; `test_simulated_outage_is_failure_not_empty_success`; per-org outage test |
| 003 — No authenticated/paywalled/arbitrary retrieval | Pass | `test_live_sources_off_by_default_never_touch_network`; configured fixed public feed and HTTP tests |
| 004 — New source preserves original URL and available dates | Pass | W2/W4; `test_refresh_collects_sources_with_url_dates_and_outcome` |
| 004 — Failure differs from successful no-new-record check | Pass | W2/W3; collection outcome rows; `test_simulated_outage_is_failure_not_empty_success` |
| 004 — Recollection is idempotent | Pass | `test_recollection_is_idempotent` |
| 004 — Collection obeys rate limits/access restrictions | Pass | `test_live_fetch_respects_minimum_interval`; live adapter uses fixed public feed; external fetch itself blocked/unrun |
| 005 — Finding exposes source links, times and source facts | Pass | W4/W5; alert source records and dates observed |
| 005 — Related reports retain separate citations | Pass | W4; `test_thn_and_csa_group_under_one_canonical_finding_with_both_citations` |
| 005 — Conflicting source claims stay uncertain | Pass | W5; `test_conflicting_exploitation_claims_are_surfaced` |
| 005 — Update changes current view and preserves change record | Pass | W9; revisions and three linked sources observed; `test_followup_evidence_sends_update_notification` |
| 006 — Summary separates what happened/known/uncertain and cites sources | Pass | W5; analysis validators/tests |
| 006 — Unsupported fields remain Unknown/unverified | Pass | W5; `test_unrecognized_finding_gets_minimal_analysis_with_explicit_unknowns` |
| 006 — Untrusted source text cannot change model behavior | Simulated | Deterministic demo analysis has no connected model provider; hostile XML tests and `tests/test_analysis.py` checks passed |
| 006 — Correction is reflected with provenance | Pass | W12; `test_correction_is_recorded_with_provenance_and_shown`; corrected text also captured in update email |
| 007 — Priority and inventory evidence are explainable | Pass | W6; score factors and evidence observed |
| 007 — Industry-only is potential relevance, not exposure | Pass | `test_industry_only_relevance`; alert page exposure disclaimer observed |
| 007 — Unknown versions never confirm affected-version match | Pass | independent exact-product Unknown-version check; `test_unknown_version_never_confirmed_even_with_exact_product` |
| 007 — Reviewer override is visible | Pass | `test_override_to_p3_goes_to_digest_not_prompt_queue`, `test_override_to_p1_sends_immediately` |
| 008 — Alert can be filtered/opened and source inspected | Pass | W4/W10; `test_alert_detail_separates_facts_unknowns_and_shows_why_not_p1` |
| 008 — Alert can be assigned and moved through outcomes | Pass | W10/W17; `test_workflow.py`, `test_full_fernwood_walkthrough` |
| 008 — Status/assignment changes show actor and time | Pass | W11/W17 audit evidence; end-to-end test |
| 008 — New evidence distinguished from original alert | Pass | W9 “Updated evidence” and three-source finding observed |
| 009 — Real allowlisted test recipient receives email | Blocked | No real SMTP account or team inbox; capture is explicitly not a real inbox |
| 009 — Unassigned user does not receive by default | Pass | `test_only_routed_recipient_is_notified` |
| 009 — Material update sends, unchanged collection suppresses duplicates | Pass | W9; `test_followup_evidence_sends_update_notification`, `test_unchanged_reassessment_is_suppressed` |
| 009 — Cadence is communicated without real-time promise | Pass | W2 collection/notification cadence labels; privacy page |
| 009 — Only allowlisted team test recipients; others rejected | Pass | W7 local capture recipient and no-connection off-list rejection; retry/digest gap tests |
| 009 — Failure is visible and never marked successful | Pass | W7/W8; `test_smtp_refusal_is_recorded_as_failed`, simulated retry checks |
| 010 — Questions have traceable framework mapping | Pass | W1 questionnaire history; `test_questionnaire_shows_mapping_and_explains_threat_weighting` |
| 010 — Authorized users can complete/review assessment | Pass | W17 new Yes assessment and history |
| 010 — New assessment preserves prior one | Pass | W17 No/Yes history; `test_new_assessment_preserves_prior_no_answer` |
| 010 — Changed weighting explains priority change | Pass | `test_questionnaire_shows_mapping_and_explains_threat_weighting` |
| 011 — Guide can start from alert without questionnaire prerequisite | Pass | `test_guide_generated_from_alert_without_questionnaire` |
| 011 — Ordered actionable steps have rationale/checks | Pass | W10 five ordered steps; `test_hallusquatting_guide_has_five_ordered_steps_with_required_fields` |
| 011 — Missing context gets targeted question and reason | Pass | W10; `test_asks_one_targeted_question_when_install_permission_is_unknown` |
| 011 — Unknown keeps conditional action useful without inventing facts | Pass | W10; `test_unknown_answer_keeps_step_4_conditional` |
| 011 — Steps distinguish facts/assumptions and link evidence | Pass | W10 guide content; `test_steps_link_only_to_supplied_sources_plus_framework` |
| 011 — User can edit draft and record progress | Pass | W10 step progress; `test_step_progress_and_edit_are_audited_with_before_after` |
| 012 — User can create/edit/save draft linked to alert/scenario | Pass | W11 plan created from guide; plan lifecycle tests |
| 012 — Only authorized role can approve | Pass | W11 Sureh got 403; Wyatt approved |
| 012 — Approval/subsequent edit recorded and approved version distinct | Pass | W11 approval/audit; `test_editing_approved_plan_returns_to_draft_and_keeps_approved_version` |
| 012 — Plan supports owners and review date | Pass | `test_plan_action_owner_and_review_date_can_be_set`; W11 Koewen owner |
| 013 — Dashboard counts derive from current records | Pass | `test_dashboard_counts_derive_from_records`, `test_dashboard_counts_open_plans_and_plan_awaiting_approval` |
| 013 — Dashboard links navigate to details | Pass | W1/W10 navigation; end-to-end test |
| 013 — Monitoring failure not shown healthy | Pass | W3 source health failure; outage test |
| 013 — Dashboard excludes other org data | Pass | W16; route matrix and org-scoped dashboard tests |
| 014 — Reviewer can see who/status or plan approval and when | Pass | W11/W17 audit history; end-to-end test |
| 014 — Finding updates preserve prior state/change | Pass | W9 revisions; `test_followup_evidence_sends_update_notification` |
| 014 — Audit history is organization-scoped | Pass | `test_other_org_admin_gets_404_on_every_id_route`; W16 |
| 014 — Credentials absent from audit records | Pass | `test_cdx2_smtp_error_text_is_not_persisted_or_shown`; notification tests |
| 015 — Access controls prevent cross-tenant reads/writes | Pass | W16; 20-route `test_review_gaps.py` matrix |
| 015 — Retention/deletion behavior documented before real customer data | Pass | W15 privacy page: local demo data retained until reset; no real regulated data |
| 015 — Third-party data flows disclosed/minimized | Pass | W15 reports actual SMTP/Live RSS/model-provider settings; capture is local-only |
| 015 — Collection does not bypass source controls | Pass | Fixed public feed; no arbitrary source configuration; live safety tests |
| 015 — UI labels exposure and human-reviewed plans | Pass | W5/W11; privacy page; alert/plan disclaimers |
| 016 — New demo organization can complete setup through approved/edited plan | **Fail** | Runtime HTTP check in both runs: new org + relevant inventory + refresh yielded 0 alerts (CDX-3). |
| 016 — Demo-only records visibly marked/segregated | Pass | W1/W5/W15 demo/fictional banners and simulated labels |
| 016 — Real findings link to sources; simulated findings are distinct | Pass | W4/W9 source links; Xygeni labeled as demo follow-up |
| 016 — IBM/GitHub examples verified or omitted from presentation | Blocked for broader materials | Not present in `canary/` UI; project concept docs still contain the unverified examples with “verify before presenting” notes. Do not present those passages as facts. |

## 7. Verdict

**The seeded Fernwood walkthrough is ready for a local presentation using the local SMTP capture result as a simulation of provider delivery.** W1–W17 passed across the two HTTP runs, scheduler concurrency showed no lock errors, all 172 tests passed, and reset restored the seed state. Real inbox delivery remains Blocked as expected, and the optional live RSS fetch was not attempted because network access is restricted here; injected-feed tests passed.

**The prototype does not meet every stated acceptance criterion yet.** CDX-3 leaves new organizations without assessments/alerts for already-collected findings, so CAN-REQ-016's new-organization workflow criterion fails. Fix it or explicitly limit the presentation claim to the seeded Fernwood walkthrough. Keep the unverified IBM/GitHub passages out of presentation materials unless checked against primary sources.
