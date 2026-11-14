# Canary — local demo prototype

> **Demo data.** Fernwood Labs, Prairie Valley Medical Center, their people,
> inventory, and outcomes are fictional. The HalluSquatting / slopsquatting
> sources are real public articles, linked with their original dates.
> Not production-hardened; no HIPAA or other compliance claim.

Planning documents: [implementation plan](documents/implementation-plan.md) ·
[design](design/design.md) · [requirements](requirements/README.md) ·
[Fernwood demo flow](documents/hallusquatting-demo-flow.md) ·
[methodology](methodology.md)

## Quick start

Requires Python 3.12+ with Flask 3 and pytest (both ship with Anaconda). No
other dependencies, no network access, and no API key are needed.

```bash
python run.py            # http://127.0.0.1:5000  (creates + seeds instance/canary.sqlite on first run)
python run.py --reset    # delete ALL records and restore the seed state
python -m pytest         # run the test suite
```

Demo accounts (fictional, demo-only authentication, password `demo` for all):

| Username | Person | Organization | Role |
|---|---|---|---|
| `wyatt` | Wyatt, CTO | Fernwood Labs | Administrator |
| `sureh` | Sureh, backend engineer | Fernwood Labs | Cybersecurity Lead |
| `koewen` | Koewen, platform engineer | Fernwood Labs | Cybersecurity Lead |
| `priya` | Priya, IT director | Prairie Valley Medical Center | Administrator |

### Environment variables (all optional)

| Variable | Purpose | Default |
|---|---|---|
| `CANARY_SECRET_KEY` | Flask session key | random per process (sessions end on restart) |
| `CANARY_DATABASE` | SQLite file path | `instance/canary.sqlite` (git-ignored) |
| `CANARY_FIXED_NOW` | Freeze "now" (ISO 8601) for reproducible scores | real clock |
| `CANARY_SCHEDULER` | `1` runs the local hourly collection thread, `0` disables | `1` |

SMTP and model-provider variables arrive with the notification slice; secrets go
only in a local `.env` (git-ignored) and are never logged.

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
| `GET /audit`, `POST /demo/reset` | member / admin | audit history; full reset |

### Priority rubric (CAN-REQ-007)

Severity 0–25, exploitation 0–25, inventory match 0–20 (Confirmed 20, Possible
12, Industry-only 5), asset criticality 0–15 (Critical 15, High 10, Medium 6,
Low 3), source reliability/recency 0–10 (best tier A5/B4/C2 + corroboration
2 sources +2 / 3+ +3 + newest source ≤30d 4 / ≤180d 3 / ≤365d 2), questionnaire
gap 0–5 (No 5, Partial/Unknown 3, unanswered 2), duplicate penalty −10. Bands:
80+ P1, 60–79 P2, 35–59 P3, else P4. P1 also requires active exploitation and a
Confirmed match to a Critical asset. Seeded Fernwood result:
16 + 8 + 12 + 15 + 9 + 5 = **65 → P2, Possible match** (as of 2026-11-14; the
recency term drops by 1 once the newest source is more than 180 days old,
after 2027-01-04, which still leaves P2).

## Walkthrough so far (slice 1)

1. Sign in as `wyatt`. The dashboard shows the **Demo data** banner and 0 alerts.
2. **Organization**: profile, inventory (runtime agent version **Unknown**),
   two Cybersecurity Leads, and the initial **No** answer for LLM03.
3. **Sources**: four catalog sources, cadences, and **Refresh sources now**.
   Optionally press **Simulate outage** on GitHub Security Advisories first; the
   refresh then shows it as **Failed** after 3 attempts, not as an empty success.
4. Refresh. THN and CSA are grouped under one finding: “HalluSquatting:
   hallucinated package names used to hijack AI coding agents.” The CSA link is a
   **proposed** grouping (shared technique alias) that a Lead can confirm or undo.
5. Open the alert: Possible match, 65/100, P2 High, every factor, why it is
   not P1, source-supported claims with citations, organization context,
   unknowns, Canary interpretation, and the THN/CSA exploitation **conflict**.
6. Sign in as `sureh`, assign the alert to yourself, and move it to **Under
   investigation**. The dashboard and audit history update from saved records.
7. Sign in as `priya`: Prairie Valley has no alert, and Fernwood alert URLs
   return 404.

## Requirement coverage status

| Req | Slice 1 status |
|---|---|
| 001 | Demo accounts, roles, org selection, server-side role checks, revocation. **Pending:** create org, simulated invite, role change |
| 002 | Profile and inventory with Unknown values (read-only). **Pending:** edit forms |
| 003 / 004 | Catalog, enable/disable, manual + hourly collection, run log, retries, simulated outage. Live RSS/API adapters not built (offline fixtures, labeled) |
| 005 | Canonical finding, exact/proposed grouping, confirm/undo, revisions. **Pending:** Xygeni follow-up evidence step |
| 006 | Deterministic demo analysis with citations, unknowns, conflicts. **Pending:** user correction UI, optional OpenAI provider |
| 007 | Match states, full rubric, P1 gate, factor display. **Pending:** override with reason |
| 008 | List, filters, unread, assignment, all statuses with transition rules and note requirement |
| 009 | **Pending** (SMTP allowlist slice) |
| 010 | Seeded questions and assessment history (read-only). **Pending:** new assessment form |
| 011 / 012 | **Pending** (guide, plan, approval) |
| 013 | Dashboard counts from records, source health (Failed/Stale/Never checked). **Pending:** open plans, guide steps |
| 014 | Audit events for login, membership, sources, collection, alerts, grouping |
| 015 | Org scoping, 404 on cross-org access, local-only binding, reset. **Pending:** data-flow disclosure page |
| 016 | Demo banner, fictional labels, source notes, reset |

## Known limitations

- Collection reads stored fixture records; no live network fetching yet.
- Session key is random per process unless `CANARY_SECRET_KEY` is set.
- The audit log is an application history, not tamper-proof.
- Grouping confirm/undo changes a global finding, which affects every
  organization that receives it. It is audited under the acting organization.
