# Canary final validation report

Date: 2026-11-14  
Reviewed commit: `e894484` (validation scope: changes described for `28a2868..e63ded3`)  
Method: pytest, targeted HTTP checks against the local app, local SMTP capture, source/document review, and a scheduler smoke run. The real `.env` was not opened or printed; no real email was sent.

## 1. Environment and commands

| Check | Observed result |
|---|---|
| `python --version` | `Python 3.13.5` |
| Python package versions | Flask `3.1.3`, pytest `8.3.4`, requests `2.32.3` |
| Existing `CANARY_*` environment variables | None listed in the review shell before the controlled runs. |
| `.env` presence | `True`; the file was not opened, printed, copied, moved, renamed, or edited. |
| No-SMTP child-process proof | `No-SMTP proof: None False set()` |
| Capture child-process proof | `Capture proof: 127.0.0.1 False {'sureh-test@team.example'}` |
| `python -m pytest -p no:cacheprovider -q -o addopts=` | `183 passed in 48.98s` |
| `python tests\codex\final_targets.py` | A1–A6, B1–B2, and C1–C2 checks completed successfully; detailed observations below. |
| `python tests\codex\verify_final_details.py` | Contrast ratios and D2 loader behavior recorded below. |
| `python design\make_brand_assets.py` | Completed; printed all six asset sizes. Before/after SHA-256 values matched and Git showed no generated asset changes. |
| `python tests\codex\http_walkthrough.py` | Completed both runs; W1–W17 results below. |
| `python tests\codex\scheduler_smoke.py` | `192.7` seconds, 76 active HTTP requests, one notification `rejected` at attempt 1, `scheduler_errors: []`. |
| Safe final `python run.py --reset` | `Demo data reset to seed state.` Final DB counts: 2 organizations, 0 alerts, 0 plans, 6 inventory items. |

The walkthrough and scheduler child processes explicitly set every SMTP variable. The capture run used only a loopback SMTP capture server, blank username/password, and a placeholder sender/allowlist. Live RSS was disabled. **No real provider or inbox was contacted.** The suite was not run behind an explicit outbound firewall rule because this environment did not provide a firewall control. Source inspection found tests either set `SMTP_HOST=None` or use the local capture server; live-source tests inject HTTP responses through `HTTP_GET`, and the live-off test fails if the HTTP hook is called.

Git reports `main...origin/main [ahead 1]`. `.git` is read-only in this workspace, so no `review/codex-final` branch or commit was created. The existing untracked `.vscode/` directory was left untouched. Only the two authorized `tests/codex/` helpers were edited; three additional `tests/codex/` verification helpers were created for this pass. No `canary/` files or Claude-authored tests were changed.

## 2. Suite result and hermetic check

**Pass: 183 tests passed.** The run included the six CDX-3 tests, four branding tests, the guide-label test, and the four existing independent Codex runtime tests.

The suite completed with `.env` present and did not send mail. SMTP configuration in the shared fixture is disabled; the notification tests use the local SMTP capture server. Network isolation via firewall was **Blocked** (not available in this environment); inspected HTTP tests use injected responses/local fixtures rather than external requests.

## 3. Targeted checks

### 4A. CDX-3: new organizations

| Check | Result and evidence |
|---|---|
| A1 | **Pass.** After Wyatt refreshed sources, a new organization was created and the matching High-criticism inventory item was POSTed. The app immediately showed one `Possible` alert without another refresh. |
| A2 | **Pass.** The new organization's Administrator created a guide, created and submitted a plan, and approved it. Stored plan status was `approved`. |
| A3 | **Pass.** A new organization without inventory had one `no_match` relevance row and zero alerts. |
| A4 | **Pass, with scope noted.** In the HTTP run, disabling THN and CSA then re-enabling CSA left the already-known alert intact; the alert count stayed at 1. `tests/test_cdx3_new_org.py::test_enabling_a_source_assesses_findings_it_already_collected` also passed in the suite and exercises the missing-relevance backlog case. Disabling did not delete prior findings. |
| A5 | **Pass.** Fernwood had exactly 1 alert and Prairie had 0. The new organization could open its own alert; Fernwood's user, Wyatt, and Prairie's user, Priya, received 404 for the new organization's alert. The new organization's user received 404 for Fernwood's alert. |
| A6 | **Pass.** Two refreshes produced zero duplicate `(org_id, finding_id)` alert pairs and zero duplicate relevance pairs. |

**CAN-REQ-016 new-organization criterion: Pass.** The original failure is resolved: a new organization can proceed from setup through an approved plan.

### 4B. Branding

| Check | Result and evidence |
|---|---|
| B1 | **Pass.** All six assets returned HTTP 200 and image MIME types: 256 logo 47,296 B; 512 logo 137,423 B (the exempt asset); 64 mark 5,704 B; 32 favicon 1,947 B; ICO 6,418 B; Apple touch icon 28,259 B. All non-512 assets are under 120 KB. |
| B2 | **Pass.** `/login`, `/`, and `/alerts/<id>` include a favicon link. Login uses the full logo with descriptive alt text; dashboard and alert pages use the decorative header mark with `alt=""`. |
| B3 | **Fail.** Light-mode P2 badge text (`#fff` on `#d9480f`) measured **4.30:1**, below the required 4.5:1. All other requested pairs passed in both modes: body, muted text on background/surface, links on background/surface, navy on canary and amber, nav text, and P1/P3/P4 badges. Dark-mode P2 measured 8.29:1. See CDX-4. |
| B4 | **Blocked (optional).** No Playwright, Selenium, or browser executable was available, so screenshots/responsive-overflow checks were not run. |
| B5 | **Pass.** `design/make_brand_assets.py` regenerated all six assets. Before/after hashes matched; Git showed no asset diff. |

### 4C. Guide link labels

| Check | Result and evidence |
|---|---|
| C1 | **Pass.** Guide links showed “The Hacker News”, “CSA research notes”, and OWASP; none displayed “Cited source”. |
| C2 | **Pass.** After adding the Xygeni follow-up, a newly created guide included “Additional evidence (demo follow-up)” and “The Hacker News”. The guide created before the follow-up retained its original labels, as expected. |

### 4D. Email configuration notes

| Check | Result and evidence |
|---|---|
| D1 | **Pass.** README and `.env.example` describe Gmail SMTP, the university Microsoft 365 `535 5.7.139` SMTP AUTH failure, first occurrence wins, and inline comments remain part of the value. |
| D2 | **Pass.** A temporary sample file under `tests/codex/` kept the first blank `CANARY_MAIL_FROM` and retained `# comment` in `CANARY_SMTP_HOST`. The real `.env` was not involved. |
| D3 | **Verified by user (not re-run).** README records real inbox verification on 2026-11-14. This review did not send a real email. |

### 4E. Documentation claims

| Check | Result and evidence |
|---|---|
| E1 | **Pass.** Repository search found `43%` and `4,000` only in explicit cautions explaining not to use the figures as facts. `issue title` had no matching use outside excluded review/guide text. |
| E2 | **Fail on exact wording; source facts verified.** The [Cline post-mortem](https://cline.bot/blog/post-mortem-unauthorized-cline-cli-npm) reports a prompt-injection vulnerability in its issue-triage workflow, describes how a crafted issue title *could* execute code, and reports an unauthorized CLI npm publish on 2026-02-17. The docs compress the potential exploit path into a definite causal event. That link is an inference from the post-mortem, not stated as definitively as the docs imply. The [IBM press release](https://newsroom.ibm.com/2026-07-29-ibm-study-one-in-four-malicious-breaches-are-ai-enabled,-costing-companies-6-million-on-average) directly supports “one in four malicious breaches” and “56% increase”. See CDX-5. |

### 4F. Demo script dry run

The local-capture HTTP walkthrough confirmed the app behavior described by the main path: Unknown inventory version; four source outcomes; Possible match, 65/100, P2 High and the P1 gate reason; conflict notice; test-labeled captured email; off-allowlist rejection; Unknown preserving the conditional guide step; Lead approval denied and Administrator approval accepted; and audit events. **Core main path: Pass in local simulation.** The capture server is not a real inbox; real inbox delivery is “Verified by user (not re-run)” per D3.

Extras passed in local simulation: Xygeni follow-up/update, human correction and provenance, Priya's cross-organization alert URL returning 404, privacy disclosures, simulated failure returning Failed (Simulated) and retry returning Sent. **If-something-goes-wrong wording: Fail.** The script says to tell the audience “DSU's filter is holding it” when the log is Sent; server acceptance does not establish that a downstream DSU filter is the cause. The 7:30 “Six months ago” line is also inaccurate for a February 17 incident on the report date (about nine months earlier). See CDX-6 and CDX-7.

## 4. Regression

`python tests\codex\http_walkthrough.py` completed both safe HTTP runs:

- **No SMTP:** W1–W7 and W9–W17 passed. W8 was Blocked as expected without SMTP. The new-organization check passed (1 alert after the scripted refresh); A1 separately verified the stronger immediate-without-refresh criterion.
- **Local SMTP capture:** W1–W17 passed, including test-labeled delivery, off-list rejection, simulated failure and retry. Three messages were captured locally; none were sent to a real inbox.

`python tests\codex\scheduler_smoke.py` ran 192.7 seconds with 76 active HTTP requests. The scheduler processed a notification as `rejected` after one attempt and recorded no `database is locked` or scheduler-cycle errors.

Final safe reset completed: `Demo data reset to seed state.` Database contains 2 organizations, 0 alerts, 0 plans, and 6 inventory items.

## 5. Defects

### CDX-4: Light-mode P2 badge falls below the contrast threshold

Severity: Low  
Location: `canary/static/canary.css` (`.prio` text `#fff`; `--p2: #d9480f` in light mode).

Expected: All priority badges meet the guide's 4.5:1 contrast threshold.  
Actual: Light-mode P2 badge measures 4.30:1. Dark-mode P2 and the other requested pairs pass.

Evidence: `python tests\codex\verify_final_details.py` computed the ratio from CSS token values. No app CSS was changed in this review.

Suggested fix: Darken the light-mode P2 background or use a foreground that yields at least 4.5:1, then rerun B3.

### CDX-5: Cline incident wording states an inferred exploit path as confirmed

Severity: Medium  
Location: `documents/sureh.md`, `documents/CANARY_Project_Plan.md`, and the opening “Say” line in `documents/demo-script.md`.

Expected: Distinguish the vulnerability Cline says *could* be exploited from the confirmed February 17 unauthorized publish.  
Actual: The text says a crafted issue prompt-injected the triage bot and led to the release as a definite chain. The post-mortem documents the vulnerability and release, but the direct causal link is an inference. The adjacent generalization that small teams have no one tracking these events is also not established by the two cited sources.

Evidence: [Cline post-mortem](https://cline.bot/blog/post-mortem-unauthorized-cline-cli-npm), especially its “How did it happen?” section. The IBM statistic itself is supported by the [IBM press release](https://newsroom.ibm.com/2026-07-29-ibm-study-one-in-four-malicious-breaches-are-ai-enabled,-costing-companies-6-million-on-average).

Suggested fix: Say that Cline disclosed a prompt-injection vulnerability in its issue-triage workflow and separately reported the unauthorized publish on February 17; avoid asserting that this exact crafted-issue path was the confirmed cause unless Cline explicitly confirms it. Either cite the small-team claim or frame it as a product problem statement rather than a sourced fact.

### CDX-6: Demo-script incident timing is stale

Severity: Low  
Location: `documents/demo-script.md`, 7:30 “Say” row.

Expected: Relative timing should match the incident date and the presentation date.  
Actual: “Six months ago” is inaccurate on 2026-11-14 for the February 17, 2026 incident; it was about nine months earlier.

Evidence: Cline's post-mortem dates the publish to February 17, 2026.  
Suggested fix: Use the month/date, or revise the relative-time phrase before each presentation.

### CDX-7: Delivery recovery line diagnoses an unverified downstream cause

Severity: Low  
Location: `documents/demo-script.md`, “If something goes wrong” table.

Expected: The presenter states only what the delivery log and inbox establish.  
Actual: A `Sent` status means the SMTP server accepted the message; it does not establish that DSU's filter is holding it. The instruction supplies that diagnosis as fact.

Suggested fix: Say the server accepted the message and it has not appeared in the inbox yet; suggest checking Junk or following up with the mail administrator without asserting a cause.

No High or Blocker defects were found; the findings above do not require failing tests under the guide's severity rule.

## 6. Verdict

- **Can CAN-REQ-016's new-organization criterion move from Fail to Pass?** Yes. A1 immediately produced the alert after inventory entry, and A2 completed guide-to-approved-plan.
- **Is every acceptance criterion now Pass, Simulated, or Verified by user?** No. The light-mode P2 contrast check and exact documentation/demo accuracy checks failed. Screenshot checks were optional and unavailable; real inbox delivery remains user-verified and was not re-run. Local capture behaviors are simulated.
- **Is the prototype ready to present exactly as described in `demo-script.md`?** The core workflow is functional and passed in local simulation, but not exactly as written: fix the Cline causal wording, stale “six months” line, and unsupported DSU-filter diagnosis. Fix the P2 contrast issue for the stated accessibility threshold.
- **What blocks a full “yes”?** CDX-4 through CDX-7. None is a workflow blocker; CDX-5–7 can cause a presenter to state unsupported or inaccurate claims, and CDX-4 misses the specified contrast threshold.
