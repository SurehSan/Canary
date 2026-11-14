# Codex Verification Guide: Runtime Pass

Your [first review](codex-review-report.md) was a static read of the code. This
pass is the **runtime verification** the
[implementation plan](implementation-plan.md) assigns to Codex for the
5:30–8:00 timeboxes:

- run the unit and integration tests;
- start the app from a clean state;
- perform the full Fernwood walkthrough;
- check all 16 requirements against evidence;
- report pass, fail, or blocked with that evidence.

Since the first review, Claude fixed CDX-1, CDX-2, and one bug the new gap
tests found, and built the four missing features (section 2).

**Rule for this pass:** a requirement or step is **Pass** only if you observed
it in this session, through command output, an HTTP response, a database query,
or the browser. Reading the code is not evidence. If you cannot do a step,
mark it **Blocked** and give the reason.

## 1. Ground rules (unchanged)

- Do not edit application files under `canary/` or Claude's tests under
  `tests/`. Put any tests or helper scripts you write in `tests/codex/`.
- Do not push. If you can, commit on a branch named `review/codex-runtime`. If
  `.git` is read-only again, leave your files uncommitted and say so in the
  report. If Git rejects the folder's ownership, use
  `git -c safe.directory="C:/Users/DSU Student/Desktop/Canary" <command>` for
  each command. Do not change global Git config.
- Email: send real email only to a team-owned address that is listed in
  `CANARY_EMAIL_ALLOWLIST`. No team SMTP account exists, so expect
  **real inbox delivery to be Blocked**. Section 5 explains how to verify the
  full SMTP path with a local capture server instead.
- Never paste secrets into the report or a commit.

## 2. What changed since your first review

`main` is now at merge commit `28a2868`. The slice-4 commits, in order:

| Commit | Change | Verify |
|---|---|---|
| `683f075` | **CDX-1:** the outage simulation is now per organization (`org_sources.simulate_failure`; simulated runs carry `collection_runs.org_id`). **CDX-2:** SMTP failures store only the exception type and numeric code. Grouping and the follow-up step now say they affect every organization. | Walkthrough steps W3 and W16 |
| `d4aa0dc` | Tests for your review gaps (20-route cross-org matrix, retry/digest allowlist, digest batch retry, plan edge cases, hostile RSS, size cap). Fix: the collector commits before network I/O, and SQLite uses a busy timeout and WAL mode. | Sections 3 and 7 |
| `996b6ef` | Local registration, create organization, simulated invite, role change (001); profile and inventory editing (002); analysis correction with provenance (006); the **Privacy and data flows** page (015). | Walkthrough steps W12–W15 |

## 3. Environment and automated suite

Run these in PowerShell from the repository root. Record every output in
report section 1.

```powershell
python --version                      # development used C:\Anaconda\python.exe 3.13.5
python -c "import flask, pytest; print(flask.__version__, pytest.__version__)"
Get-ChildItem env:CANARY_* -ErrorAction SilentlyContinue   # should list nothing for this pass
Test-Path .env                                             # False expected; run.py loads .env if it exists
python -m pytest -p no:cacheprovider -q                    # expected: 168 passed (about 1 minute)
```

Tests are hermetic: they ignore `.env` and use temporary databases and the
local SMTP capture server. If any test fails, copy the failure output into the
report under that test's requirement. Do not fix it.

Test files and the requirements they cover:

| File | Tests | Requirements |
|---|---|---|
| `test_access.py` | 8 | 001, 002, 015, 016 |
| `test_slice.py` | 13 | 003, 004, 005, 006, 007, 008, 013, 014 |
| `test_scoring.py`, `test_normalize.py`, `test_analysis.py`, `test_workflow.py` | 12, 7, 8, 4 | 007, 005, 006, 008 |
| `test_notify_unit.py`, `test_notifications.py`, `test_scheduler.py` | 7, 16, 2 | 009, 007 (override), 014, 015 |
| `test_live.py` | 6 | 003, 004 |
| `test_guide_unit.py`, `test_guide_plan.py` | 6, 18 | 010, 011, 012, 013, 014 |
| `test_review_fixes.py`, `test_review_gaps.py` | 4, 31 | 003, 009, 012, 015, plus the CDX fixes |
| `test_slice4_features.py` | 25 | 001, 002, 006, 015 |
| `test_e2e_fernwood.py` | 1 | whole walkthrough |

Then add **at least these independent checks** in `tests/codex/`. Write your
own assertions; do not copy Claude's tests:

1. CDX-1 from the other direction. Fernwood turns on an outage for **GitHub
   Security Advisories**, which both organizations enable. Prairie Valley's
   sources page must not show Failed for it, and Fernwood must not receive new
   items from it during that run.
2. Unknown version with an exact product key. No seeded finding lists affected
   products, so call `canary.scoring.match_state` directly with a finding whose
   `affected_products` names the inventory item's `product_key` and lists
   versions, while the item's version is `None`. The state must be `possible`,
   never `confirmed` (CAN-REQ-002 and 007 acceptance criteria).
3. Correction provenance appears in email. Correct an analysis statement, then
   cause a **material** update (the follow-up step `POST /sources/followup`
   adds a source); a correction alone does not send email. The update email
   received by the capture server must contain the corrected text.
4. Invite → revoke → re-invite. The role and status are correct each time, and
   the audit log has each step.

## 4. Start the app from a clean state

```powershell
python run.py --reset
$env:CANARY_SCHEDULER = "0"     # deterministic walkthrough; the scheduler gets its own check in section 7
python run.py                   # http://127.0.0.1:5000 ; every demo account uses the password "demo"
```

Use a browser if you have one. Otherwise drive the app over HTTP with a
cookie-keeping session: `requests` 2.32 is installed in this Python, and every
action is a form POST listed in the README route table. Say which method you
used. The README route table gives each form field name.

The seeded alert scores 65 on the real clock until 2027-01-04. If you run later
than that, set `$env:CANARY_FIXED_NOW = "2026-11-14T15:00:00+00:00"` before
starting the app, and note it in the report.

## 5. Email setup for the walkthrough

There are three states to observe, all confirmed against the current code:

| Configuration | Expected notification status |
|---|---|
| No `.env`, and Sureh has no test address | **Blocked**: "No test address is configured for this recipient." |
| No `.env`, and an address entered for Sureh | **Rejected**: "the test allowlist is empty or malformed" (no SMTP connection) |
| Local capture server + allowlist (below) | **Sent**; the capture console prints the subject `[CANARY DEMO - TEST] P2 · Possible match · HalluSquatting: …` |

To exercise the full SMTP path without a real inbox, save this script as
`tests/codex/smtp_capture_cli.py`:

```python
import sys, time
sys.path.insert(0, ".")
from tests.smtp_capture import CaptureServer

server = CaptureServer()
print(f"Capture SMTP listening on 127.0.0.1:{server.port}", flush=True)
seen = 0
try:
    while True:
        time.sleep(1)
        while seen < len(server.messages):
            m = server.messages[seen]
            seen += 1
            print(f"[{seen}] to={m['rcpts']} subject={m['msg']['Subject']}", flush=True)
            print(m["msg"].get_content()[:600], flush=True)
except KeyboardInterrupt:
    server.close()
```

Run it in a second terminal (`python tests\codex\smtp_capture_cli.py`), then
start the app in the first terminal like this:

```powershell
$env:CANARY_SMTP_HOST = "127.0.0.1"; $env:CANARY_SMTP_PORT = "<port printed>"; $env:CANARY_SMTP_STARTTLS = "0"
$env:CANARY_MAIL_FROM = "canary-demo@team.example"; $env:CANARY_EMAIL_ALLOWLIST = "sureh-test@team.example"
python run.py
```

The console may show `�` in place of `·` in the subject. That is only the
console's encoding.

Run the walkthrough **twice**: once with no email configuration, to record the
Blocked and Rejected states, and once with the capture server, to record Sent,
Update, simulated failure plus retry, and the digest. In the report, label the
capture-server results as "local SMTP capture, not a real inbox".

## 6. Walkthrough checklist

Start each run from `python run.py --reset`. W1–W11 follow
[hallusquatting-demo-flow.md](hallusquatting-demo-flow.md); W12–W17 cover
slice 4 and the safeguards. Fill in the **Result** column (Pass / Fail /
Blocked) and the **Evidence** column (what you observed).

| # | Who | Action | Expected | Req |
|---|---|---|---|---|
| W1 | wyatt | Sign in; open Organization | Demo data banner; inventory lists the Python runtime agent framework with version **Unknown** (Critical); members Sureh and Koewen (Cybersecurity Lead) and Wyatt (Administrator); questionnaire history shows **No** for LLM03 | 001, 002, 016 |
| W2 | wyatt | Sources → **Refresh sources now** | Four sources; THN and CSA show Success with 1 new item each, GHSA and OWASP show "Success — no new records"; separate collection and notification cadences are stated | 003, 004 |
| W3 | wyatt, then priya | Wyatt: **Simulate outage** on GHSA, then refresh. Then sign in as Priya and open her dashboard | Fernwood shows GHSA **Failed** after 3 attempts with "Simulated outage (this organization only)"; Prairie Valley's GHSA is **not** Failed (CDX-1). Turn the outage off afterwards | 003, 015 |
| W4 | wyatt | Open the alert | One finding, "HalluSquatting: hallucinated package names used to hijack AI coding agents"; THN 2026-07-08 and CSA 2026-04-19 links; CSA grouping marked **Proposed**, with the cross-organization notice | 005 |
| W5 | wyatt | Read the analysis | Separate Source-supported (cited), Organization context, Unknown, and Canary interpretation sections; a conflict about in-the-wild exploitation; "Demo analysis" label; no claim that Fernwood is exposed | 006 |
| W6 | wyatt | Read relevance | **Possible match · Score 65/100**, **P2 High**; factors 16/8/12/15/9/5 and duplicate penalty 0; text explaining why it is not P1; "not evidence of exposure" | 007 |
| W7 | wyatt | Notifications → **Run processing cycle**; **Send delivery check** to an address not on the allowlist | Run 1 (no email config): **Blocked**; enter an address for Sureh and press **Retry**, and it becomes **Rejected**. Run 2 (capture server): **Sent** to Sureh's test address with the `[CANARY DEMO - TEST]` subject, a test-mode notice in the body, and source links. The delivery check is **Rejected** with no SMTP connection | 009 |
| W8 | wyatt | Run 2 only: **Simulate delivery failure** → send → **Retry** after turning it off | Failed (Simulated) → Sent; attempts 2 | 009 |
| W9 | wyatt | Sources → **Demo step: deliver later follow-up report (Xygeni)** | The alert shows 3 sources and "Updated evidence"; the next processing cycle sends an **Update** (Run 2), or records Blocked/Rejected (Run 1) | 005, 009 |
| W10 | sureh | Assign the alert to self → Under investigation; **Get a step-by-step guide**; answer **Unknown**; mark step 1 in progress | 5 ordered steps, each with why it matters, checks, technique, and links; "AI-generated draft for human review"; step 4 stays conditional; the dashboard counts update | 008, 011, 013 |
| W11 | sureh, then wyatt | **Create contingency plan** → Submit for review; Sureh tries Approve (not possible); Wyatt ticks the confirmation and approves | Stages Detection, Containment, Recovery, Review; Koewen owns the permission check; status **Approved**; version history and the audit log show the approval; "does not execute" notice | 012, 014 |
| W12 | sureh | On the alert, **Correct** an interpretation statement with a reason | Corrected text in place with "Corrected by Sureh, <date>: <reason>"; Correction history shows the original text; audit event `analysis.corrected` | 006, 014 |
| W13 | wyatt | Organization → edit profile (clear Size); add an inventory item with a blank version; edit one item | Size shows Unknown; the new item's version is **Unknown**; the audit log shows before/after | 002, 014 |
| W14 | new user | Sign out → **Create a local demo account** → create an organization → try to demote yourself to Lead → invite `koewen` as a Lead → change his role to Administrator | You are Administrator of the new organization; demoting the **last** Administrator is refused; Koewen can open the organization; invite and role change are audited | 001 |
| W15 | any | Footer → **Privacy and data flows** | Reflects the actual configuration (SMTP status, Live RSS on or off, no model provider); retention until reset; no compliance claim | 015 |
| W16 | priya | Request a Fernwood alert, guide, and plan by URL id, and POST to one of their actions | **Not found** each time; Fernwood's records are unchanged | 001, 015 |
| W17 | sureh, wyatt | Mitigation in progress → Resolved and verified (with note); new questionnaire assessment answering **Yes**; then the footer **Reset demo data** | The original **No** stays in history; the audit log shows the whole flow; after reset, no alerts or plans remain, and the seed organizations are back | 008, 010, 014, 016 |

## 7. Additional runtime checks

1. **Scheduler concurrency** (the CDX focus 10 fix). Start the app with
   `CANARY_SCHEDULER=1` and **without** `CANARY_LIVE_SOURCES`. Use the app
   actively for at least 3 minutes; the notification cycle runs every 60
   seconds. Look for `database is locked` or `Scheduler cycle failed` in the
   console.
2. **Live RSS** (optional; needs network). Run one refresh with
   `CANARY_LIVE_SOURCES=1`. Expected: a "Live RSS" run for The Hacker News
   that is either Success with AI-related items or Failed with an error type.
   Record which. Do not run it repeatedly.
3. **Reset**: compare row counts before and after `python run.py --reset`, for
   example with `sqlite3 instance/canary.sqlite "select count(*) from alerts"`.

## 8. Traceability

For every acceptance criterion in
[CAN-REQ-001–016](../requirements/README.md), record one line: the criterion,
the evidence (test name, walkthrough step, or observation), and a status. Use
one of these statuses:

- **Pass**
- **Fail**
- **Blocked**
- **Simulated**, for behavior intentionally represented by a labeled
  simulation: demo authentication, offline fixture sources, the deterministic
  demo analysis, outage and delivery-failure simulations, and the Xygeni step.

Known items that are not built: the optional OpenAI analysis provider (the
deterministic demo analysis is the documented fallback), real inbox delivery
(no account), and CSRF protection (accepted only within the loopback demo
boundary).

## 9. Report

Write `documents/codex-verification-report.md` with these sections:

1. **Commands run and environment**, with actual output: Python version,
   pytest summary line, environment variables, and browser or HTTP method.
2. **Automated results**: pass/fail counts per test file, and your
   `tests/codex/` tests with their results.
3. **Walkthrough**: the W1–W17 table, filled in for both runs.
4. **Email**: real inbox **Blocked** (no account); local SMTP capture results.
5. **Defects**, in the same `CDX-<n>` format as your first report and
   continuing its numbering from CDX-3. Grade each by what a person running the
   demo would experience, and include a failing test in `tests/codex/` for
   every High or Blocker.
6. **Traceability matrix** (section 8).
7. **Verdict**: is the prototype ready to present under the plan's definition?
   The definition: it starts locally from the documented instructions,
   completes the Fernwood flow end to end, sends test email only to the
   allowlisted address, preserves uncertainty and human approval, and has no
   unresolved blocker in the walkthrough. List anything that prevents a "yes".
