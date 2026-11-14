# Codex Final Validation Guide: Changes Since the Runtime Verification

Your [runtime verification](codex-verification-report.md) checked commit
`28a2868`. Since then, `main` has moved to `e63ded3` (pushed to `origin/main`).
This pass validates **only what changed**, then re-runs the regression to show
that nothing else broke. The evidence rule is the same as last time: a check is
**Pass** only if you observed it in this session. Reading the code is not
evidence, and anything you could not run is **Blocked**, with the reason.

## 1. What changed (commit range `28a2868..e63ded3`)

| Commit | Change | Section |
|---|---|---|
| `b01905c` | **CDX-3 fix.** New `pipeline.assess_org` and `pipeline.assess_backlog`. An organization is now assessed against every finding its enabled sources already collected, on four triggers: organization creation, inventory/profile edits, enabling a source, and every refresh or scheduler cycle. Tests: `tests/test_cdx3_new_org.py` (6). | 4A |
| `760c65a` | **Branding.** The logo was turned into transparent web assets in `canary/static/brand/` by `design/make_brand_assets.py`. A favicon and header mark were added, plus a logo hero on the sign-in page and a logo-derived palette (canary `#ffcc00`, amber `#f2aa00`, navy `#0a1a36`, cream `#fbf9ec`) with light and dark modes. CSS class names are unchanged. Tests: `tests/test_branding.py` (4). | 4B |
| `a36c0d0` | **Guide links** show the source name instead of "Cited source" (test in `tests/test_guide_unit.py`). The **README** and `.env.example` record that real email was verified through Gmail SMTP, and that the university Microsoft 365 tenant rejects SMTP AUTH (`535 5.7.139`). **Concept documents** (`documents/sureh.md`, `documents/CANARY_Project_Plan.md`) now use primary-sourced claims and drop the "43%" figure. New **demo script**: `documents/demo-script.md`. | 4C, 4D, 4E |
| `75ec5cc` | The user committed `design/logo.png`. | — |

Not changed: the scoring, notification safety ordering, workflows, guides,
plans, and questionnaire logic you verified last time.

## 2. Required first step: keep your scripts from sending real email

**The repository root now contains the user's `.env` with a real Gmail sender
and App Password.** `run.py` loads `.env` with `os.environ.setdefault`, so a
variable that is already present in the environment wins, *even if it is an
empty string*. Any variable that is absent gets filled from `.env`.

Your `tests/codex/http_walkthrough.py` and `tests/codex/scheduler_smoke.py`
remove every `CANARY_*` variable before starting `run.py`. **As written, they
would therefore pick up the real Gmail settings.** The "no SMTP" run would send
real email to the team inbox, and the capture run would sign in to the local
capture server with the real Gmail username and App Password.

Before running either script:

1. Update **your own** scripts (they are in `tests/codex/`, so you may edit
   them) so that the environment given to the subprocess **explicitly sets
   every email variable**:
   - **No-SMTP run:** `CANARY_SMTP_HOST=""`, `CANARY_SMTP_USERNAME=""`,
     `CANARY_SMTP_PASSWORD=""`, `CANARY_MAIL_FROM=""`,
     `CANARY_EMAIL_ALLOWLIST=""`, `CANARY_TEST_RECIPIENTS=""`.
   - **Capture run:** the capture host and port, `CANARY_SMTP_STARTTLS=0`,
     `CANARY_SMTP_SSL=0`, `CANARY_SMTP_USERNAME=""`,
     `CANARY_SMTP_PASSWORD=""`, a placeholder `CANARY_MAIL_FROM`, and your
     `CANARY_EMAIL_ALLOWLIST` and `CANARY_TEST_RECIPIENTS`.
   - **Scheduler smoke:** the same values as the no-SMTP run, plus
     `CANARY_LIVE_SOURCES=0`.
2. **Prove it before any run.** In a subprocess built with that environment,
   run `python -c "import run; run.load_dotenv(); from canary import create_app; a = create_app({'START_SCHEDULER': False}); print(a.config['SMTP_HOST'], bool(a.config['SMTP_PASSWORD']), a.config['EMAIL_ALLOWLIST'])"`.
   Expected: `None False set()` for the no-SMTP run, and the capture host,
   `False`, and your allowlist for the capture run.
3. **Do not open, print, copy, or edit `.env`.** Do not rename or move it
   either. Never put any value from it into the report.

Also note that the scripts reset `instance/canary.sqlite`, the user's local
demo database. That is acceptable, but run `python run.py --reset` when you
finish, and say so in the report.

## 3. Automated suite

```powershell
python -m pytest -p no:cacheprovider -q -o addopts=      # expected: 183 passed
```

This count includes your 4 tests in `tests/codex/` and the 11 new ones (6
CDX-3, 4 branding, 1 guide-link label). Tests are hermetic: they never read
`.env`. Confirm that with the next check.

- **Hermetic check:** with `.env` in place, the suite must neither send email
  nor contact the network. Run it once with outbound network blocked or a
  firewall rule, if your environment allows that. Otherwise, mark this check
  Blocked and confirm that every test's `create_app` config passes
  `SMTP_HOST: None` or the capture server.

## 4. Targeted checks

### 4A. CDX-3: new organizations (CAN-REQ-016, 001, 002, 003)

Run all of these over HTTP against the running app, with email neutralized as
described in section 2.

| # | Steps | Expected |
|---|---|---|
| A1 | Reset; `wyatt` refreshes sources. Register a new user, create an organization, add an inventory item with tags `ai_coding_agent, auto_install_packages` and High criticality | The new organization has **1 alert** (Possible match) **immediately**, without another refresh. This is your original CDX-3 reproduction. |
| A2 | Continue: guide → plan → submit → approve (as the new organization's Administrator) | Plan **Approved**. CAN-REQ-016 "a new demo organization can complete the workflow… through approved plan" passes. |
| A3 | A new organization with **no** inventory | The relevance row is No known match, and there are **0 alerts**. No alert is created without an inventory match. |
| A4 | A new organization disables The Hacker News and CSA, then re-enables CSA | Re-enabling triggers assessment. Record what you see. Disabling a source does **not** remove findings the organization already knew about; Claude ruled that disabling only stops future collection, per CAN-REQ-003. Report a finding if you think that ruling is wrong. |
| A5 | After A1, sign in as `wyatt` and as `priya` | Fernwood still has exactly 1 alert; Prairie Valley has 0. The new organization's records are **Not found** to both, and vice versa. |
| A6 | Run a refresh twice | No duplicate alerts or relevance rows for any organization (check `UNIQUE(org_id, finding_id)`). |

### 4B. Branding (CAN-REQ-016 labels, general quality)

| # | Check | Expected |
|---|---|---|
| B1 | `GET /static/brand/{canary-logo-256.png, canary-logo-512.png, canary-mark-64.png, favicon-32.png, favicon.ico, apple-touch-icon.png}` | All return 200 with image content types. Every file except the 512-px logo is under 120 KB. |
| B2 | `/login`, `/`, `/alerts/<id>` HTML | A favicon `<link rel="icon">` on every page; the header `<img>` uses `alt=""` (decorative, next to the "Canary" text); the sign-in hero has descriptive alt text. |
| B3 | **Contrast.** Compute WCAG 2.1 ratios from the CSS tokens in `canary/static/canary.css`, in both light and dark modes | Body text on its background ≥ 4.5:1; `--muted` text ≥ 4.5:1; link color ≥ 4.5:1; navy on the canary banner and primary button ≥ 4.5:1; the priority badge text color on each of `--p1`…`--p4` ≥ 4.5:1; top-bar nav text on the navy bar ≥ 4.5:1. Report every pair below the threshold as a finding with its measured ratio. |
| B4 | Screenshots (optional, if you have a headless browser) | Light and dark versions of `/login`, the dashboard, an alert, and a guide. Confirm the logo has no cream halo on the navy bar, and nothing overflows at 1280 px or 390 px wide. |
| B5 | `python design/make_brand_assets.py` | Regenerates the six files without errors. The `git diff` shows either no change or only byte-level PNG differences (no visual change). |

### 4C. Guide link labels (CAN-REQ-011)

| # | Check | Expected |
|---|---|---|
| C1 | After a reset, create the HalluSquatting guide | Step links read "The Hacker News", "CSA research notes", and the OWASP link. No link reads "Cited source". |
| C2 | Reset → refresh → run the Xygeni follow-up step (it attaches to the existing HalluSquatting finding) → *then* create the guide | Step 5's links include "Additional evidence (demo follow-up)" (Xygeni) and "The Hacker News". A guide created *before* the follow-up step keeps the labels it stored; that is expected, not a defect. |

### 4D. Email configuration notes (CAN-REQ-009, 015)

| # | Check | Expected |
|---|---|---|
| D1 | Read the README "Test email safety" section and `.env.example` | They describe the Gmail route and the 535 5.7.139 tenant block, and warn that the first occurrence of a variable wins and that inline comments are not stripped. |
| D2 | Verify those two `.env` behaviors in **a temporary copy in a scratch directory**, never the real `.env`: write a sample file with a blank `CANARY_MAIL_FROM=` followed by a filled one, and a value followed by `# comment`, then call `run.load_dotenv(path)` | The first occurrence wins, and the comment stays inside the value. This confirms the documentation is accurate. If you think the loader itself should change, report it as a finding. |
| D3 | Real inbox delivery | **Do not send real email yourself.** The user verified it on 2026-11-14 (README). Mark it "Verified by user (not re-run)". |

### 4E. Documentation claims (CAN-REQ-016)

| # | Check | Expected |
|---|---|---|
| E1 | Search the whole repository (excluding the requirement text and review documents) for `43%`, `4,000`, and `issue title` | Each appears only inside a note that explains why it is *not* used. Nothing presents it as fact, including `canary/` templates and `documents/demo-script.md`. |
| E2 | If you have network access, open the two cited primary sources: the [Cline post-mortem](https://cline.bot/blog/post-mortem-unauthorized-cline-cli-npm) and the [IBM press release](https://newsroom.ibm.com/2026-07-29-ibm-study-one-in-four-malicious-breaches-are-ai-enabled,-costing-companies-6-million-on-average) | `sureh.md` and the project plan state exactly what those pages say: a crafted issue prompt-injected the AI triage bot and led to an unauthorized npm release on 2026-02-17; one in four malicious breaches were AI-enabled, a 56% increase. Mark Blocked if there is no network. |

### 4F. Demo script dry run

Follow [demo-script.md](demo-script.md) **main path** over HTTP, with email
going to the capture server rather than a real inbox. For each row, confirm
that every factual statement in the "Say" column matches what the page shows:

- Unknown version;
- four sources and their outcomes;
- 65/100, P2 High, Possible match, and the not-P1 reason;
- the conflict notice;
- the test-labeled email;
- the off-allowlist address Rejected;
- the Unknown answer leaving step 4 conditional;
- the Lead's approval refused and the Administrator's approval accepted;
- the audit entries.

Then do the same for the "Extras" and "If something goes wrong" rows. In
particular, check:

- **Simulate delivery failure → Send delivery check:** expected Failed
  (Simulated), then Retry → Sent.
- **Priya pasting a Fernwood alert URL:** expected Not found.

Report any script line that doesn't match the app as a defect **in the
script**.

## 5. Regression

After completing section 2, re-run your scripts:

```powershell
python tests\codex\http_walkthrough.py     # W1–W17, both runs; your new-organization check should now PASS
python tests\codex\scheduler_smoke.py      # 3 minutes of active use with the scheduler on; no "database is locked"
python run.py --reset                      # leave the user's demo database clean
```

Expected: W1–W17 pass in both runs, as before. W8 is Blocked in the no-SMTP run,
as before. The new-organization check that failed as CDX-3 now passes.

## 6. Ground rules (unchanged)

- Don't edit `canary/` or Claude's tests; report defects instead. You may edit
  files in `tests/codex/` only.
- Don't push. Commit on `review/codex-final` if `.git` is writable; otherwise,
  leave your files uncommitted and say so.
- Use `git -c safe.directory="C:/Users/DSU Student/Desktop/Canary" …` if Git
  rejects the folder's ownership.
- Leave the user's untracked `.vscode/` folder alone.

## 7. Report

Write `documents/codex-final-validation-report.md` with these sections:

1. **Environment and commands**, with real output, including the section 2
   proof lines (the printed config, never `.env` values).
2. **Suite result** (expected 183 passed) and the hermetic check.
3. **Targeted checks** A1–A6, B1–B5, C1–C2, D1–D3, E1–E2, and F (main path and
   extras): Pass, Fail, or Blocked for each, with evidence.
4. **Regression:** W1–W17 for both runs, the new-organization check, and the
   scheduler smoke test.
5. **Defects** in your earlier format, numbered from **CDX-4**, each graded by
   what a presenter or user would experience, with a failing test in
   `tests/codex/` for every High or Blocker.
6. **Verdict:**
   - Can CAN-REQ-016's new-organization criterion move from Fail to Pass?
   - Is every acceptance criterion now Pass, Simulated, or "Verified by user"?
   - Is the prototype ready to present as described in `demo-script.md`?
   - List anything that blocks a "yes".
