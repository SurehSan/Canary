# Canary Showcase: The 5-Minute Story

This is the order to present Canary in, and what each step proves. For exact
clicks, setup, and fallbacks, use the run sheet in [demo-script.md](demo-script.md).
Run it with `CANARY_PRESENTATION_MODE=1`.

**The story in one line:** a real, critical PHP vulnerability hits a five-person
startup with no security team. Canary matches it to the exact server, holds back
until attacks are confirmed, escalates the moment they are, and turns it into a
fix guide and a human-approved plan, without anyone claiming the company was
hacked.

**The real event:** **PHP2Shell**, CVE-2026-109618 and CVE-2026-109619. These are
two critical flaws (CVSS v4.0 9.2) that let an unauthenticated attacker run code
on servers running PHP 5.4–8.5. PHP fixed them on 21 Oct 2026 (8.5.12, 8.4.27,
8.3.36, 8.2.35), and Check Point confirmed in-the-wild attacks on 12 Nov 2026.

**Cast** (the company, people, and systems are fictional):

| Who | Role | Signs in as |
|---|---|---|
| Wyatt, CTO | Administrator: settings, notifications, final approval | `wyatt` (normal window) |
| Sureh, backend engineer | Cybersecurity Lead: investigates and drafts the response | `sureh` (private window) |
| Fernwood Labs | Startup whose customer billing portal runs **PHP 8.3.30** | — |

All passwords are `demo`. Have the email inbox open in a third window: the alert
goes to the address `.env` maps to **Koewen** (`CANARY_TEST_RECIPIENTS`). To have it
reach a second person as well, give them an address and add a routing rule for
them under **Notifications → Recipients and routing** *before* step 3.

---

## 1. The problem (0:00 – 0:30)

**Do:** nothing yet; stay on the sign-in page with the logo.

**Say:** "On October 21, PHP shipped emergency fixes for two critical flaws that
let anyone on the internet run code on a PHP server. Within days attackers were
trying them; on November 12 Check Point confirmed real break-ins. Small teams
rarely have anyone watching for this. Everything you'll see is a sample company;
the vulnerability and the sources are real."

**Shows:** why Canary exists, and the honest framing up front.

## 2. Canary knows your stack (0:30 – 1:00)

**Do:** sign in as Wyatt → **Organization**.

**Point at:** the **Customer billing portal (PHP-FPM)**, version **8.3.30**,
marked Critical.

**Shows:** Canary works from *your* systems, not generic news. Versions are
recorded exactly, and missing facts would stay **Unknown** rather than being
guessed.

## 3. Catch the threat (1:00 – 2:15)

**Do:** **Sources → Refresh sources now**, then open the **PHP2Shell** alert.

**Point at, in this order:**
1. **Four reports, one finding.** The PHP advisory is the primary record. GitHub's
   two advisories attach automatically through matching CVE numbers. The news
   article matches only by name, so it's a *proposed* grouping that a person
   confirms.
2. **Confirmed match.** 8.3.30 is below 8.3.36, the fixed release for that branch.
3. **87/100, yet P2 High.** Scroll to **Priority factors**: every point is
   explained. 87 is in P1 range, but P1 requires *confirmed* active exploitation,
   and so far there are only third-party reports of attempts, flagged as
   **unverified**.

**Shows:** curated intake, CVE-based deduplication, exact version matching, and
explainable scoring. Most importantly, **it doesn't overreact or overclaim**: a
score is triage, not proof of compromise.

## 4. Tell the right person, then escalate (2:15 – 3:30)

**Do:** **Notifications → Run processing cycle (P1/P2)** and show the P2 email in
the inbox. Then **Sources → Presenter tools → Deliver later exploitation report
(Check Point)**, reopen the alert, and refresh the inbox.

**Point at:**
- The P2 email: why it matters to Fernwood, what's known and unknown, and links.
- After Check Point's report: **P1 Critical, 95/100**, the P1 rule met, and
  "Updated evidence".
- The **P1 update email arrived immediately**, without waiting for a cycle.

**Shows:** alerts reach the right person, at a cadence set by priority (P1
immediately, P2 next cycle, P3/P4 in a daily digest), only at approved addresses.
Canary re-evaluates as evidence changes and says why.

## 5. Guide the fix (3:30 – 4:20)

**Do:** in Sureh's window, open the alert → **Assign** to Sureh → **Under
investigation** → **Get a step-by-step guide**.

**Point at:**
1. Five ordered steps: confirm the version, **upgrade to 8.3.36** and restart the
   workers, apply the PHP project's **interim setting** until then, check for
   signs of compromise, and rotate keys only if something is found.
2. **One targeted question:** "Is the Customer billing portal (PHP-FPM)
   reachable from the internet?" Answer **Unknown**.
3. The compromise check stays **conditional** instead of Canary assuming an
   answer.

**Shows:** guidance specific to this vulnerability and this company, with no
questionnaire needed first. When a fact is missing, Canary asks once and doesn't
invent the answer.

## 6. A human decides (4:20 – 4:50)

**Do:** **Create contingency plan from this guide** → **Submit for review**. Then,
in Wyatt's window: **Plans** → open it → tick the confirmation → **Approve**.

**Point at:**
- Only the stages that apply (Detection, Containment, Recovery, Review), each
  with an owner. Koewen owns the interim mitigation and the exposure check.
- Sureh *can't* approve; only the Administrator can.
- The note that approval **executes nothing** on Fernwood's systems.

**Shows:** AI drafts and people decide. Roles are enforced.

## 7. Close (4:50 – 5:10)

**Do:** **Audit**.

**Say:** "Everything is on the record: the escalation, who picked it up, what they
answered, and who approved what, and when. PHP2Shell went from patch to confirmed
attacks in about two weeks, and Canary kept a team with no security person one
step ahead the whole way."

**Shows:** accountability, and the one-line value of the product.

---

## If you have one more minute

| Show | How | What it proves |
|---|---|---|
| **Human correction** | On the alert, **Correct** a line of the analysis with a reason | People can fix the AI; the original text is kept, with who changed it and why. |
| **Tenant isolation** | Sign in as `priya` (another organization) and open the Fernwood alert's URL | **Not found.** Organizations never see each other's data, and Prairie Valley (no PHP) gets no alert. |
| **Honest failure** | Notifications → **Presenter tools** → **Simulate delivery failure** → **Send delivery check** | It shows **Failed (Simulated)**, then **Sent** after **Retry**. Canary never pretends an email went out. |
| **The questionnaire link** | **Questionnaire** | The 72-hour patching question (CIS Controls v8, Safeguard 7.4) is answered **No**, weighted up by the open PHP2Shell alert, and part of the score. |

## Likely questions and straight answers

- **Is this real data?** The vulnerability, CVEs, fixed versions, and advisories
  are real and linked. Fernwood, its people, and its billing portal are a sample
  workspace.
- **Was Fernwood hacked?** No, and Canary never says so. The portal runs an
  affected version; the plan includes checking for signs of compromise.
- **Why was it P2 at first if it scored 87?** Canary's P1 rule needs confirmed
  active exploitation *and* a confirmed match to a critical system. The early
  exploitation reports were unverified, so it waited for a primary source.
- **Does it fetch live news?** It can (The Hacker News RSS, opt-in). For the demo
  it uses stored copies of the real advisories and articles, so it works without
  internet.
- **Could it patch the server itself?** No, by design. It recommends; people
  approve; nothing is executed on customer systems.
- **Is it production-ready?** No. It's a local prototype with no compliance
  claims. Hosting, SSO, and CSRF protection are on the roadmap.

## Before you start

- Open a new terminal, then run `python run.py --reset` and `python run.py` (a
  fresh demo state).
- Open three windows: Wyatt (normal), Sureh (private/incognito), and the inbox
  mapped to Koewen in `.env`. Add any extra routing rules now; a reset clears them.
- Check that the alert reads **87/100, P2 High** after Refresh. If it says 95/P1,
  the Check Point report was already delivered: reset.
- Rehearse once: the whole path takes about 5 minutes once you know the clicks.
