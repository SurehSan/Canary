# Codex Review Guide: Canary Local Prototype

You are reviewing and verifying the Canary local demo prototype that Claude
built from [the implementation plan](implementation-plan.md). Your job, as set
in the plan, covers test planning, test implementation, verification, and
reporting. **Do not edit application files** under `canary/`. Report defects
instead; Claude fixes them unless a fix is explicitly handed to you.

## 1. Ground rules

- **Do not push.** All merges so far are local to `main`. Make your own commits
  on a branch named `review/codex-<date>`.
- **Put your tests in `tests/codex/`.** Reuse fixtures from
  [tests/conftest.py](../tests/conftest.py) and the SMTP capture server in
  [tests/smtp_capture.py](../tests/smtp_capture.py). Do not modify Claude's
  existing tests. If you think one is wrong, report it as a finding.
- **Email safety:** automated tests must use the local capture server only.
  Never configure a real SMTP host in tests, and never send to an address that
  is not team-owned. No team SMTP account exists yet, so mark real inbox
  delivery as **Blocked: no SMTP configuration**. Do not mark it as passed.
- **Network:** the default build makes no network calls. Only
  `CANARY_LIVE_SOURCES=1` fetches the public THN RSS feed; at most run that once
  by hand. Tests must inject `HTTP_GET` (see
  [tests/test_live.py](../tests/test_live.py)).
- **Judge against the spec, not the screens.** The sources of truth are the
  [design](../design/design.md),
  [CAN-REQ-001–016](../requirements/README.md), and the
  [Fernwood demo flow](hallusquatting-demo-flow.md). The plan says: "do not mark
  a requirement complete solely because a screen exists."

## 2. Scope

| Item | Value |
|---|---|
| Review range | `git diff 00b3d5a..main` (00b3d5a is the last commit before implementation) |
| Slices | Slice 1: vertical slice and access control. Slice 2: notifications and live RSS. Slice 3: guide, plan, questionnaire |
| Not yet built (slice 4) | analysis correction UI (006), profile/inventory editing (002), create organization, simulated invite, and role change (001), privacy/data-flow disclosure page (015) |
| Implementation notes | [readme.md](../readme.md): stack, schema, routes, scoring rubric, walkthrough, coverage table, limitations |

## 3. Setup

```bash
python --version                  # 3.12+ (Anaconda 3.13 used during development)
python -m pytest                  # expected: 108 passed
python run.py --reset             # restore seed state
python run.py                     # http://127.0.0.1:5000, demo password "demo" for every account
```

Accounts: `wyatt` (Fernwood Administrator), `sureh` and `koewen` (Fernwood
Cybersecurity Leads), `priya` (Prairie Valley Administrator). To get
reproducible scores during manual testing, set
`CANARY_FIXED_NOW=2026-11-14T15:00:00+00:00`.

## 4. Code map

| Module | Responsibility | Requirements |
|---|---|---|
| [canary/auth.py](../canary/auth.py) | demo login, active-membership check on every request, `role_required` | 001, 015 |
| [canary/views.py](../canary/views.py) | dashboard, organization, sources, alerts, override, grouping, notifications, audit, reset | 001–009, 013–016 |
| [canary/work_views.py](../canary/work_views.py) | guides, plans, questionnaire | 010–012 |
| [canary/collector.py](../canary/collector.py), [canary/live.py](../canary/live.py) | fixture and live collection, retries, rate-limit skip, ingest | 003, 004 |
| [canary/normalize.py](../canary/normalize.py) | canonical URL, identifiers, technique aliases, duplicate classification | 005 |
| [canary/analysis.py](../canary/analysis.py) | deterministic cited analysis, conflicts, citation validator | 006 |
| [canary/scoring.py](../canary/scoring.py) | match state, 0–100 rubric, P1 gate | 007 |
| [canary/pipeline.py](../canary/pipeline.py) | per-organization analysis, relevance, alert creation and updates | 006–008 |
| [canary/workflow.py](../canary/workflow.py) | alert transitions and required notes | 008 |
| [canary/notify.py](../canary/notify.py), [canary/delivery.py](../canary/delivery.py) | message content, allowlist, fingerprint, queue, SMTP, digest | 009 |
| [canary/guides.py](../canary/guides.py), [canary/plans.py](../canary/plans.py) | guide templates and the targeted question; plan templates and versions | 011, 012 |
| [canary/schema.sql](../canary/schema.sql), [canary/seed.py](../canary/seed.py) | schema, fictional seed, reset | 002, 015, 016 |

## 5. Review focus

Check these deliberately. They are the input classes and failure modes that
the existing tests do not exercise, or where Claude is least confident.

1. **Global state changed by one organization's admin.** These need a ruling on
   whether one organization can affect another:
   - `POST /sources/<id>/simulate-failure` flips `source_catalog.simulate_failure`,
     which is a **global** row.
   - `POST /sources/followup` and grouping confirm/undo change **global**
     `findings` and `source_items`.
   - Collection runs are global as well.

   Write a test in which Priya (Prairie Valley) triggers each one, then check
   what Fernwood sees. Check every org-scoped route for a missing `org_id`
   filter too.
2. **Cross-organization access.** Every route that takes an id
   (`/alerts/<id>`, `/guides/<id>`, `/plans/<id>`, `/notifications/<id>/retry`,
   `/members/<id>/revoke`, `/alerts/<id>/grouping/<item_id>/…`) must return 404
   for another organization's records, on both GET and POST. Only a few are
   tested today.
3. **Revocation mid-session.** A revoked member's existing session must lose
   access on the next request, including POST routes and any owner or assignee
   dropdowns that still list them.
4. **Email safety ordering** in `delivery._precheck` / `dispatch`:
   - An address off the allowlist must never open an SMTP connection, including
     on **retry** and for **digest** batches.
   - A missing address must be Blocked; a malformed allowlist must reject
     everyone.
   - Check whether an SMTP error message or exception text can leak
     `CANARY_SMTP_PASSWORD` into `notifications.error` or the audit log (for
     example, an authentication failure).
   - Check that a digest retry updates the whole batch consistently.
5. **No CSRF protection.** All state-changing routes are form POSTs without
   tokens, and Flask's default `SESSION_COOKIE_SAMESITE` is unset. The app binds
   to 127.0.0.1 only. Grade this against CAN-REQ-015 for a local demo and
   record a ruling.
6. **Untrusted feed parsing.** [canary/live.py](../canary/live.py) uses
   `xml.etree.ElementTree` (no defusedxml is installed). Check entity expansion
   and oversized input (the read is capped at 2 MB), and confirm that
   `javascript:` and other non-http(s) links are dropped and that every title
   and excerpt is autoescaped.
7. **Scoring determinism.** The seeded result (Possible, 65, P2) depends on the
   current date: the recency term changes after 2027-01-04. Verify the rubric
   against CAN-REQ-007 for all of these:
   - each band boundary;
   - the P1 gate when the score is 80 or more;
   - "Unknown version can never be Confirmed";
   - an industry-only match;
   - the −10 duplicate penalty, which is implemented but never triggered by the
     pipeline. Is that a gap?
8. **Update and suppression logic** in `pipeline.assess_for_org`
   (`_analysed_version`) and `delivery.enqueue_for_alert`:
   - Does a grouping confirmation, re-collection, or new questionnaire
     assessment ever send a duplicate email, or fail to send a genuine update?
   - Does a reviewer override survive a later reassessment?
9. **Plan lifecycle edges.**
   - An edit with no changes must not create a version.
   - An archived plan must not be editable.
   - The approved-version snapshot must stay unchanged after later edits.
   - Owners must be active members, including after one is revoked.
10. **Scheduler concurrency.** The background thread and request handlers share
    one SQLite file. Run the app with `CANARY_SCHEDULER=1` and a short
    `NOTIFY_CYCLE_SECONDS`, if you can do that without editing application files
    (otherwise report it as untested), and look for `database is locked` errors.
11. **Labels and claims (CAN-REQ-015/016).**
    - Nothing may say Fernwood is exposed or compromised.
    - Simulated items (outage, delivery failure, Xygeni demo step, demo
      analysis) must be visibly labeled.
    - Prairie Valley must be labeled fictional.
    - The IBM 43% and GitHub issue-title claims must not appear anywhere in the
      app.

## 6. Claude's rulings to evaluate

These are the decisions Claude made on the user's behalf. For each, say whether
it still satisfies the spec.

1. Stack: Flask, Jinja, SQLite, and pytest, with no new dependencies.
2. Rubric sub-scales were chosen so that the seeded case scores
   16/8/12/15/9/5 = 65. Source tiers: The Hacker News and CSA are B, GitHub
   Security Advisories and OWASP are A, Xygeni is C.
3. The CSA note calls itself "Unofficial AI-assisted Research" and claims
   real-world slopsquatting exploitation, while THN reports no HalluSquatting
   exploitation. This is shown as a **conflict**; exploitation is scored as
   `research_demonstrated` (8/25).
4. The THN/CSA grouping is a **proposed** grouping (curated technique alias)
   that needs a person to confirm or undo it, because the spec forbids treating
   similarity as proof.
5. Offline fixture adapter by default. Live mode adds a separate THN-only
   "Live RSS" run, at most once every 15 minutes (a `skipped` outcome otherwise).
6. Xygeni is an admin "demo step" with `source_id` NULL and tier C, labeled as
   not collected by a catalog source.
7. Notification statuses: Blocked means a missing address or missing SMTP
   configuration. Rejected means the address is off the allowlist. Failed with
   `simulated=1` means the demo failure switch.
8. A reviewer override may set any priority, including P1. A P1 override sends
   immediately.
9. Guide question wording uses the inventory item name. The capability tags
   `install_permission_yes/no` suppress the question.
10. A plan in review cannot be edited. Editing an approved plan returns it to
    Draft and keeps `approved_version`.
11. A new questionnaire assessment rescores the organization's findings.
12. The end-to-end test was written after the features it covers (an
    acceptance test). All other tests were written to fail first.

## 7. Verification checklist

- Build a compact **test matrix** from every acceptance criterion in
  CAN-REQ-001–016. Mark each one: covered by an existing test (name it),
  covered by your new test, manual check, or simulated or not built.
- Run the full **Fernwood walkthrough** by hand from a clean reset, following
  [hallusquatting-demo-flow.md](hallusquatting-demo-flow.md) steps 1–11 and the
  README walkthrough. Note every step that needed a workaround.
- Confirm that the seeded alert reads **Possible match, 65/100, P2 High**, that
  each factor is shown, and that the reason it is not P1 is explained.
- Confirm that a reset deletes everything a user entered and restores the seed
  state.

## 8. Simulations and boundaries (do not report these as defects)

- Demo authentication only: a shared password, no SSO, MFA, or account recovery.
- Collection runs from offline fixture records of real articles. Live RSS is THN
  only and opt-in.
- The analysis is a deterministic demo template; no OpenAI provider is wired in.
- Source outages, delivery failures, and the Xygeni follow-up are labeled demo
  simulations.
- No guide or plan export, no reminders, no automatic actions on customer
  systems.
- The audit log is application history, not tamper-proof storage.

Slice-4 gaps (section 2) **are** reportable as unmet acceptance criteria. Label
them "not built yet".

## 9. Report format

Write your results to `documents/codex-review-report.md` on your branch. The
plan asks for these sections:

1. **Commands run and environment** (OS, Python version, environment variables).
2. **Test results grouped by requirement ID**: test name, pass, fail, or blocked.
3. **Full-demo smoke result**, listing any step that needed manual intervention.
4. **Real email result**: expected to be Blocked (no SMTP configuration), with
   the reason.
5. **Defects**, grouped as Blocker, High, or Medium/Low. Write each one as:

   ```
   ### CDX-<n>: <one-line title>
   Severity: Blocker | High | Medium | Low
   Requirement: CAN-REQ-0xx (acceptance criterion quoted)
   Location: path/to/file.py:<line>
   Steps to reproduce: numbered, starting from `python run.py --reset`
   Expected: …
   Actual: …
   Evidence: failing test name in tests/codex/, or output
   Suggested fix (no code changes): …
   ```

6. **Rulings**: for each item in section 6 and each focus item that needs a
   decision (CSRF, global state), say "stands" or "finding", with the reason.
7. **Requirements represented only by simulation**, plus known limitations.

Grade each finding by what a person using the demo would actually experience,
not by whether the spec mentions that input. Put a failing test in
`tests/codex/` for every High or Blocker finding, so the fix can be shown to
turn it from failing to passing.
