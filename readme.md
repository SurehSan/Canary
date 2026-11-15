# Canary — local demo prototype

> **Demo data.** Fernwood Labs, Prairie Valley Medical Center, their people,
> inventory, and outcomes are fictional. The demo threat, **PHP2Shell**
> (CVE-2026-109618, CVE-2026-109619), and its sources are real, linked with their
> original dates.
> Not production-hardened; no HIPAA or other compliance claim.

Planning documents: [implementation plan](documents/implementation-plan.md) ·
[design](design/design.md) · [requirements](requirements/README.md) ·
[Fernwood demo flow](documents/php2shell-demo-flow.md) ·
[methodology](methodology.md)

## Run the demo

These steps take you from a fresh copy of the repository to the running demo.
Run every command from the project folder (the one containing `run.py`).

**1. Check Python.** You need Python 3.12 or newer (`python --version`). With
Anaconda, Flask and pytest are already installed, so you can skip step 2.

**2. Install the dependencies** (optional virtual environment first):

```bash
python -m venv .venv
.venv\Scripts\activate              # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt     # the app only needs Flask
```

**3. (Optional) Set up real test email.** Without this the demo still runs
completely; emails just show as **Blocked** in the app. To send real test
email:

- Copy [.env.example](.env.example) to `.env`, which git ignores and never commits.
- Fill in a Gmail sender: username and From set to the Gmail address, and the
  password set to a [Gmail App Password](https://myaccount.google.com/apppasswords),
  **not** your normal password.
- Add the team-owned inbox that should receive the tests to
  `CANARY_EMAIL_ALLOWLIST` and `CANARY_TEST_RECIPIENTS` (for example
  `sureh=you@school.edu`).
- Set `CANARY_SCHEDULER=0` so email goes out only when you click.
- Optional: `CANARY_PRESENTATION_MODE=1` for a product-like look when presenting
  (see the environment variable table). Tell the audience once that the workspace
  and people are fictional.

Keep each setting on one line, with no comments after the value. University
Microsoft 365 accounts can't be used as the sender because they block SMTP
sign-in (error 535). See [Test email safety](#test-email-safety-can-req-009).

**4. Reset and start the app:**

```bash
python run.py --reset    # fresh demo data; also maps the test inbox from .env
python run.py            # leave this terminal open
```

**5. Open http://127.0.0.1:5000** and sign in. Every demo account uses the
password `demo`. Use a normal window for `wyatt` and a **private/incognito**
window for `sureh`, because one browser window holds one signed-in person.

| Username | Person | Organization | Role |
|---|---|---|---|
| `wyatt` | Wyatt, CTO | Fernwood Labs | Administrator |
| `sureh` | Sureh, backend engineer | Fernwood Labs | Cybersecurity Lead |
| `koewen` | Koewen, platform engineer | Fernwood Labs | Cybersecurity Lead |
| `priya` | Priya, IT director | Prairie Valley Medical Center | Administrator |

**6. Follow the demo script:** [documents/demo-script.md](documents/demo-script.md)
has an 8-minute and a 3-minute walkthrough, with clicks, talking points, and
fallbacks. In short: as Wyatt, **Sources → Refresh sources now** → open the
**PHP2Shell** alert (**Confirmed match, 87/100, held at P2**) → **Notifications →
Run processing cycle** (the P2 email) → **Presenter tools → Deliver later
exploitation report (Check Point)** (escalates to **P1, 95/100**, with an immediate
update email). Then, as Sureh: assign the alert →
**Get a step-by-step guide** → **Create contingency plan** → submit. Finally, as
Wyatt, approve the plan.

**7. Stop or start over.** Press **Ctrl+C** in the terminal to stop. Run
`python run.py --reset` and then `python run.py` to start again from clean
data; you'll need to sign in again.

**If something doesn't work**

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Run step 2, or activate the virtual environment you installed into. |
| Port 5000 busy ("Only one usage of each socket address", or "Address already in use" on macOS/Linux) | Another copy is still running. Stop it with Ctrl+C in its terminal, or close that terminal. |
| The alert's score isn't 65 | The source-recency points change after 2027-01-04. Add `CANARY_FIXED_NOW=2026-11-14T15:00:00+00:00` to `.env` and reset. |
| Email shows **Blocked** | No sender or no test address is configured; see step 3. **Rejected** means the address isn't on the allowlist. |
| Email shows **Failed (code 535)** | The SMTP provider refused the sign-in: check the App Password, or don't use a university Microsoft 365 account as the sender. |
| Email says **Sent** but hasn't arrived | The mail server accepted it. Check Junk/Quarantine; first messages from a new sender are often filtered. |

**Command reference**

```bash
python run.py                         # start at http://127.0.0.1:5000 (creates and seeds instance/canary.sqlite on first run)
python run.py --reset                 # delete ALL records and restore the seed state
pip install -r requirements-dev.txt   # adds pytest, requests (Codex scripts), Pillow (logo asset script)
python -m pytest                      # run the test suite (213 tests)
python design/make_brand_assets.py    # regenerate logo assets from design/logo.png
```

### Environment variables (all optional)

Copy [.env.example](.env.example) to `.env` (git-ignored; read only by
`run.py`, never by tests). Existing environment variables take precedence.

| Variable | Purpose | Default |
|---|---|---|
| `CANARY_SECRET_KEY` | Flask session key | random per process (sessions end on restart) |
| `CANARY_DATABASE` | SQLite file path | `instance/canary.sqlite` (git-ignored) |
| `CANARY_FIXED_NOW` | Freeze "now" (ISO 8601) for reproducible scores | real clock |
| `CANARY_SCHEDULER` | `1` runs the background schedule (P1/P2 queue every minute, collection hourly, digest daily) | `1` |
| `CANARY_SMTP_HOST`, `_PORT`, `_USERNAME`, `_PASSWORD`, `_STARTTLS`, `_SSL` | SMTP provider for real test email | unset = sends are **Blocked** |
| `CANARY_MAIL_FROM` | From address | unset = Blocked |
| `CANARY_EMAIL_ALLOWLIST` | Comma-separated team-owned addresses, always allowed for every organization and not removable in the app | empty = **every recipient rejected** unless an Administrator adds one |
| `CANARY_ALLOWLIST_DOMAINS` | Comma-separated domains an Administrator may add addresses on, in **Notifications → Allowlist** (per organization, confirmation required, audited) | the domains used in `CANARY_EMAIL_ALLOWLIST`; if both are empty, in-app additions are off |
| `CANARY_TEST_RECIPIENTS` | `user=addr,...` maps demo people to test addresses at seed/reset | none |
| `CANARY_BASE_URL` | Link base in emails | `http://127.0.0.1:5000` |
| `CANARY_PRESENTATION_MODE` | `1` = product-like UI for presenting: no demo banner or "fictional" tags, test accounts not listed on sign-in, scripted events moved to an Administrator-only **Presenter tools** panel; emails use a clean `[Canary · Test]` tag and a one-line sample-workspace footer. Truthfulness text (AI-generated draft, triage is not proof) stays | `0` (full demo labels, as CAN-REQ-009/016 require by default) |
| `CANARY_LIVE_SOURCES` | `1` also reads The Hacker News public RSS (AI-related items only, ≥15 min apart) | `0` (offline fixtures only) |

The SMTP password is read from the environment only. It is never stored in the
database, shown on a page, or written to the audit log (a test checks this).

### Test email safety (CAN-REQ-009)

Each send runs these checks in order: (1) the recipient must have a test
address, or the send is **Blocked**; (2) the address must be on the
organization's allowlist (`CANARY_EMAIL_ALLOWLIST` plus any team-owned addresses
an Administrator added under **Notifications → Allowlist** on a permitted
domain), or it is **Rejected** with no SMTP connection;
(3) SMTP must be configured, or it is **Blocked**; (4) the "Simulate delivery
failure" demo switch produces **Failed (simulated)** with no SMTP contact;
(5) otherwise the app sends through SMTP and records **Sent** only if the server
accepted the message, or **Failed** with the SMTP error. There is no
production mode and no mock-inbox fallback. Unchanged reassessments are
**Suppressed**; material changes (priority, relevance, exploitation status,
affected products, or source evidence) send an **Update**. Automated tests use
a local SMTP capture server ([tests/smtp_capture.py](tests/smtp_capture.py)).
**Real inbox delivery was verified on 2026-11-14.** Sending through Gmail SMTP
(an App Password) to a team-owned university inbox on the allowlist, the delivery
check and the P2 alert email were both accepted and received, and an
address off the allowlist was rejected before any send. Use a Gmail
(or similar) sender: the team's university Microsoft 365 tenant disables SMTP
AUTH (`535 5.7.139 SmtpClientAuthentication is disabled for the Tenant`), which
the app correctly records as **Failed** (code 535). Gmail settings:
`CANARY_SMTP_HOST=smtp.gmail.com`, port 587, STARTTLS on, username and From both
set to the Gmail address, and the password set to a Gmail App Password (not the
account password).

## Technical decisions (recorded per the implementation plan)

| Decision | Choice | Why |
|---|---|---|
| Runtime | Python 3.13 (Anaconda), Flask 3.1, Jinja2 server-rendered pages | Already installed; no Node on the machine; smallest reliable local path |
| Storage | SQLite via stdlib `sqlite3`, schema in [canary/schema.sql](canary/schema.sql) | Single local file; reset = drop + reseed |
| Tests | pytest; Flask test client; temp DB per test; `FIXED_NOW=2026-11-14T15:00Z` | Deterministic scores and dates |
| Auth | Local demo accounts, werkzeug password hashes, session cookie; roles `admin`, `lead` | CAN-REQ-001 prototype scope (no SSO/MFA) |
| Collection | Offline fixture adapter holding real article metadata; per-source runs, 3 attempts with bounded backoff | Demo must work without network |
| Analysis | Deterministic, curated, citation-checked demo analysis; no API key needed | CAN-REQ-006 fallback; optional OpenAI provider is later work |
| Match/priority | Pure functions in [canary/scoring.py](canary/scoring.py) | Code, not the model, decides match state and priority |
| Brand | Logo from [design/logo.png](design/logo.png); web-sized transparent copies in `canary/static/brand/` built by `python design/make_brand_assets.py`; palette in [canary/static/canary.css](canary/static/canary.css) (canary `#ffcc00`, amber `#f2aa00`, navy `#0a1a36`, cream `#fbf9ec`; light and dark modes) | Matches the Canary logo; one script regenerates every size |

## Data model and interface contract (for test authors)

Org-scoped tables carry `org_id`; every org-scoped query filters on the
**selected** organization, and records outside it return **404** (no
disclosure). Global tables hold central collection output.

| Table | Scope | Notes |
|---|---|---|
| `users`, `memberships(org_id,user_id,role,status)` | membership per org | `role ∈ {admin, lead}`, `status ∈ {active, revoked}`; revoked = immediate loss of access |
| `organizations`, `inventory_items` | org | `inventory_items.version` NULL = **Unknown**; `capabilities` JSON tags drive technology matching |
| `source_catalog`, `org_sources(org_id,source_id,enabled)` | global / org | Fixed catalog; `simulate_failure` is a labeled demo switch |
| `collection_runs` | global | `outcome ∈ {success, success_no_new, failed}`, `attempts`, `new_items`, `error` |
| `findings`, `source_items`, `finding_revisions` | global | `source_items.canonical_url` UNIQUE (idempotent re-collection); `group_status ∈ {primary, exact, proposed, confirmed}` |
| `analyses`, `relevance`, `alerts` | org | `relevance`: `match_state`, `score`, `priority`, `factors` JSON, override columns; one alert per (org, finding) |
| `questions`, `assessments`, `answers` | global / org | OWASP LLM Top 10 (2025) mapping; answers Yes/No/Partial/Unknown/Not applicable; assessments are append-only |
| `audit_events` | org (NULL = system) | actor, action, target, summary, before/after JSON, timestamp |

Pure logic entry points (unit-testable without the app):

- `canary.scoring.match_state(finding, inventory, org_industry) -> {state, evidence}`
- `canary.scoring.score_priority(impact_class=, exploitation_status=, match_state=, criticalities=, sources=, as_of=, questionnaire_answer=, duplicate_without_new_info=) -> {factors, score, priority, p1_gate_met, p1_gate_reason}`
- `canary.normalize.canonical_url / extract_identifiers / detect_technique / classify_duplicate`
- `canary.analysis.build_demo_analysis(finding, source_items, match)`, `validate_analysis(analysis, source_ids)`
- `canary.workflow.check_transition(current, new, note)`

HTTP routes (form posts; session cookie auth):

| Route | Who | Purpose |
|---|---|---|
| `POST /login`, `POST /logout`, `GET /orgs`, `POST /orgs/select` | any | demo sign-in and org selection (non-member org → 404) |
| `GET /` | member | dashboard; counts expose `data-count="new-alerts|requires-action|high-priority|open-alerts"` |
| `GET /organization`, `POST /members/<user_id>/revoke` | member / admin | profile, inventory, members, questionnaire history |
| `GET /sources`, `POST /sources/refresh`, `POST /sources/<id>/toggle`, `POST /sources/<id>/simulate-failure` | member / admin | source status and settings |
| `GET /alerts?priority=&status=&category=&since=&unread=1`, `GET /alerts/<id>` | member | alert list and detail |
| `POST /alerts/<id>/assign` (`assignee_id`), `POST /alerts/<id>/status` (`status`, `note`) | admin, lead | investigation; invalid transition → 400 |
| `POST /alerts/<id>/grouping/<item_id>/confirm|undo` | admin, lead | review a proposed duplicate grouping |
| `POST /alerts/<id>/override` (`priority`, `match_state`, `reason` required) | admin, lead | reviewer override for this finding only |
| `POST /sources/followup` | admin | demo step: attach Check Point's exploitation advisory as additional evidence (refused until the finding is collected) |
| `GET /notifications` | member | SMTP/allowlist status, recipients, routing rules, delivery log |
| `POST /notifications/recipients` (`user_id`, `email`), `POST /notifications/rules` (`user_id`, `category`), `POST /notifications/rules/<id>/delete` | admin | recipient mapping and routing |
| `POST /notifications/process`, `POST /notifications/digest` | admin | run the P1/P2 processing cycle / the P3/P4 daily digest now |
| `POST /notifications/simulate-failure`, `POST /notifications/<id>/retry`, `POST /notifications/test` (`email`) | admin | demo failure switch, retry (max 3 attempts), delivery check to any address (rejected unless allowlisted) |
| `GET /audit`, `POST /demo/reset` | member / admin | audit history; full reset |

`notifications.status ∈ {pending, sent, failed, rejected, blocked, suppressed}`,
`kind ∈ {new, update, test}`, `cadence ∈ {immediate, prompt, digest, manual}`,
`simulated = 1` marks a demo-simulated failure. `collection_runs.adapter` is
`Offline fixture adapter (demo)` or `Live RSS`, and `outcome` also allows
`skipped` (live fetch inside the minimum interval).

### Priority rubric (CAN-REQ-007)

Severity 0–25, exploitation 0–25, inventory match 0–20 (Confirmed 20, Possible
12, Industry-only 5), asset criticality 0–15 (Critical 15, High 10, Medium 6,
Low 3), source reliability/recency 0–10 (best tier A5/B4/C2 + corroboration
2 sources +2 / 3+ +3 + newest source ≤30d 4 / ≤180d 3 / ≤365d 2), questionnaire
gap 0–5 (No 5, Partial/Unknown 3, unanswered 2), duplicate penalty −10. Bands:
80+ P1, 60–79 P2, 35–59 P3, else P4. P1 also requires active exploitation and a
Confirmed match to a Critical asset. Version ranges such as `>=8.3.0,<8.3.36` are
supported; an Unknown version is never Confirmed. Seeded Fernwood result for
PHP2Shell (billing portal on PHP 8.3.30): after Refresh, 25 + 12 (exploitation
attempts reported, unverified) + 20 + 15 + 10 + 5 = **87 → held at P2** (the P1
gate isn't met). After the Check Point report, exploitation is confirmed:
25 + 20 + 20 + 15 + 10 + 5 = **95 → P1**. Source reliability stays at its 10-point
cap until well into 2027, so these numbers don't drift.

## Walkthrough

Scenario: [documents/php2shell-demo-flow.md](documents/php2shell-demo-flow.md).
Presenter script: [documents/demo-script.md](documents/demo-script.md).

1. Sign in as `wyatt`. The dashboard shows 0 alerts.
2. **Organization**: profile, inventory (billing portal on **PHP 8.3.30**,
   Critical), two Cybersecurity Leads, and the initial **No** for the 72-hour
   patching question (CIS Controls v8, Safeguard 7.4).
3. **Sources**: five catalog sources, cadences, and **Refresh sources now**.
   Optionally simulate an outage first; the refresh then shows **Failed** after 3
   attempts, not an empty success.
4. Refresh. The php.net advisory, two GitHub advisories, and a THN article become
   one finding, "PHP2Shell: unauthenticated remote code execution in PHP
   (CVE-2026-109618, CVE-2026-109619)". The GitHub advisories are **exact**
   matches (CVE); the THN article is a **proposed** grouping (matched by name)
   that a Lead can confirm or undo.
5. Open the alert: **Confirmed match, 87/100, P2 High**. It shows every factor,
   why it's held at P2 (the P1 gate needs confirmed exploitation), the
   source-supported claims with citations, the organization context, the
   unknowns, the interpretation, and the **unverified** exploitation note.
6. **Notifications → Run processing cycle**: the P2 email goes to Koewen's
   allowlisted address (or shows as Blocked or Rejected). **Send delivery check**
   to an address off the allowlist is rejected before sending.
7. **Presenter tools → Deliver later exploitation report (Check Point)**: a fifth
   source, confirmed exploitation, **P1 Critical, 95/100**, "Updated evidence",
   and an **Update** email sent **immediately** ("priority P2->P1").
8. As `sureh`: assign the alert and move it to **Under investigation**. Then
   **Get a step-by-step guide**: five steps (confirm the version, upgrade to
   8.3.36, interim `session.upload_progress.enabled = 0`, look for signs of
   compromise, and rotate keys only if indicators are found). The targeted
   question is "Is the Customer billing portal (PHP-FPM) reachable from the
   internet?"; answer **Unknown** and step 4 stays conditional.
9. **Create contingency plan from this guide**: "Critical PHP remote code
   execution (PHP2Shell)" with Detection, Containment, Recovery, and Review.
   Koewen owns the interim mitigation and exposure check. **Submit for review**;
   Sureh can't approve. As `wyatt`, tick the confirmation and **Approve**.
10. Close out as `sureh`: Mitigation in progress → Resolved and verified (with a
    note). **Questionnaire**: a new assessment with **Yes** for the 72-hour patch
    target; the original **No** stays in history. **Audit** shows every step.
11. As `priya`: Prairie Valley (no PHP) has no alert, and Fernwood alert URLs
    return 404.
12. Footer: **Reset demo data** (or **Reset workspace** in presentation mode)
    restores the seed state.

The automated version of this walkthrough is
[tests/test_e2e_fernwood.py](tests/test_e2e_fernwood.py).

## Requirement coverage status

| Req | Status after slice 4 |
|---|---|
| 001 | Demo accounts plus local registration, create organization (creator becomes Administrator), simulated invite of an existing account, role change (last Administrator protected), revocation, server-side role checks, 404 on other organizations' records |
| 002 | Profile editing (Admin; name and industry required, others optional/Unknown), inventory add/edit/remove (Admin, Lead) with Unknown/Unconfirmed versions, capability tags, optional data-access notes; changes are audited and rescore alerts |
| 003 / 004 | Catalog, enable/disable, manual + hourly collection, run log with adapter, retries, simulated outage, optional live THN RSS with min-interval skip, collected-items list |
| 005 | Canonical finding, exact/proposed grouping, confirm/undo, revisions, follow-up evidence update |
| 006 | Deterministic demo analysis with citations, unknowns, conflicts; human corrections with prior value, editor, timestamp, and reason, shown in place, carried into emails, kept across re-analysis. Optional OpenAI provider not built (deterministic demo analysis is the documented fallback) |
| 007 | Match states with version-range matching, full rubric, P1 gate (demonstrated by the PHP2Shell P2 → P1 escalation), factor display, reviewer override with reason |
| 008 | List, filters, unread, assignment, all statuses with transition rules and note requirement, update indicator |
| 009 | Allowlist-before-send, routing by category/member, P1 immediate / P2 cycle / P3–P4 digest, suppression, updates, failure + retry, delivery log, test labels. Real inbox delivery verified 2026-11-14 via Gmail SMTP to an allowlisted team inbox |
| 010 | OWASP LLM 2025 and CIS Controls v8 (Safeguard 7.4) mapped questions with help text, Yes/No/Partial/Unknown/N/A, append-only assessments, explained threat weighting (answers never rewritten), reassessment rescoring |
| 011 | Guide from alert (no questionnaire needed), 5 ordered steps with rationale/checks/technique/basis/links, one targeted question with Unknown, conditional step, step status + edits audited, limited generic guide for unknown threats |
| 012 | Plan from guide, applicable stages only, owners, review/due dates, Draft → In review → Approved (Admin only, explicit confirmation) → Archived, approved version preserved on edit, version history |
| 013 | Dashboard counts from records (incl. open plans, plans awaiting approval, waiting guide questions), source health |
| 014 | Audit events for login, membership, sources, collection, alerts, grouping, overrides, notifications, guide answers/progress/edits, plan lifecycle, questionnaire |
| 015 | Org scoping (20-route cross-org test), per-org demo simulations, local-only binding, reset, secrets env-only, sanitized SMTP errors, in-app **Privacy and data flows** page |
| 016 | Demo banner, fictional labels, source notes, reset, simulation labels; organizations created (or sources enabled) after collection are assessed against already-collected findings, so a new organization can complete the workflow (CDX-3) |

## Known limitations

- No CSRF tokens and no explicit SameSite cookie setting. Acceptable only for this
  loopback-only demo (agreed in the Codex review). Required before any shared or
  hosted use.

- Offline fixture records are the default. Live mode covers only The Hacker
  News RSS; CSA, GitHub Security Advisories, and OWASP GenAI stay offline.
  Live items that match no curated technique get a minimal "unverified" analysis
  and usually no alert.
- Real SMTP delivery was verified once (Gmail SMTP to an allowlisted team inbox). University Microsoft 365 accounts cannot send because SMTP AUTH is disabled tenant-wide.
- Session key is random per process unless `CANARY_SECRET_KEY` is set.
- The audit log is an application history, not tamper-proof.
- Grouping confirm/undo changes a global finding, which affects every
  organization that receives it. It is audited under the acting organization.
