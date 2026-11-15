# Canary Showcase: The 5-Minute Story

This is the order to present Canary in, and what each step proves. For exact
clicks, setup, and fallbacks, use the run sheet in [demo-script.md](demo-script.md).
Run it with `CANARY_PRESENTATION_MODE=1`.

**The story in one line:** a five-person startup with no security team uses Canary
to turn a brand-new AI attack into a scored alert, a real email, a tailored fix
guide, and a human-approved plan, without anyone claiming it was hacked.

**Cast** (the people and company are fictional; the threat research is real):

| Who | Role | Signs in as |
|---|---|---|
| Wyatt, CTO | Administrator: settings, notifications, final approval | `wyatt` (normal window) |
| Sureh, backend engineer | Cybersecurity Lead: investigates and drafts the response | `sureh` (private window) |
| Fernwood Labs | Startup building *Ledgerly*, an AI bookkeeping agent | — |

All passwords are `demo`. Have the email inbox open in a third window: the alert
goes to the address `.env` maps to **Sureh** (`CANARY_TEST_RECIPIENTS`). To have it
reach a second person as well, give them an address and add a routing rule for
them under **Notifications → Recipients and routing** *before* step 3.

---

## 1. The problem (0:00 – 0:30)

**Do:** nothing yet; stay on the sign-in page with the logo.

**Say:** "AI tools ship faster than teams can secure them. In February, Cline
disclosed that its AI issue-triage bot could be hijacked through a GitHub issue
title, and an exposed release token was used to push an unauthorized version of
its CLI. IBM's 2026 breach study found one in four malicious breaches were
AI-enabled, up 56% in a year. Small teams rarely have anyone watching for this.
Everything you'll see is a sample company; the threat research is real."

**Shows:** why Canary exists, and the honest framing up front.

## 2. Canary knows your stack (0:30 – 1:00)

**Do:** sign in as Wyatt → **Organization**.

**Point at:** the AI inventory. The coding assistant has auto-install **on**; the
runtime agent's version is **Unknown**.

**Shows:** Canary works from *your* context, not generic news. Missing facts stay
**Unknown** and are never guessed, which matters in the next step.

## 3. Catch the threat (1:00 – 2:15)

**Do:** **Sources → Refresh sources now**, then open the **HalluSquatting** alert.

**Point at, in this order:**
1. **Two real reports, one finding.** The Hacker News and a CSA research note,
   with their links and dates, are grouped into one alert instead of two.
2. **Possible match · 65/100 · P2 High.** Scroll to **Priority factors**: every
   point is explained (severity, exploitation evidence, inventory match, asset
   criticality, source quality, questionnaire gap).
3. **Why it's not P1.** P1 needs active exploitation *and* a confirmed match to a
   critical asset; neither is true here.
4. **Facts vs. unknowns.** The analysis separates what the sources say, what's
   specific to Fernwood, what's still unknown, and Canary's interpretation. It
   also flags that the two sources **disagree** about real-world exploitation.

**Shows:** curated intake, deduplication, organization-specific relevance, and
explainable scoring. Most importantly, **it doesn't overclaim**: a score is
triage, not proof that Fernwood was compromised.

## 4. Tell the right person (2:15 – 3:00)

**Do:** **Notifications → Run processing cycle (P1/P2)**, then switch to the inbox.

**Point at:** the real email, tagged `[Canary · Test]`: the priority, why it
matters to Fernwood, what's known and unknown, and the source links. Back in the
app, **Send delivery check** to an address that isn't approved: it's
**Rejected** before anything is sent.

**Shows:** alerts reach the right person by role, on a schedule set by priority
(P1 immediately, P2 next cycle, P3/P4 in a daily digest), and only to approved
addresses. A failed delivery is always reported as failed, never as sent.

## 5. Guide the fix (3:00 – 4:00)

**Do:** in Sureh's window, open the alert → **Assign** to Sureh → **Under
investigation** → **Get a step-by-step guide**.

**Point at:**
1. Five ordered steps, each with *why it matters*, *what to check*, a technique,
   and links to the sources and OWASP guidance.
2. **One targeted question:** "Does the Python runtime agent framework have
   permission to install packages in production?" Answer **Unknown**.
3. Step 4 stays **conditional** instead of Canary assuming an answer.

**Shows:** guidance tailored to this threat and this company, not a generic
checklist, with no questionnaire required first. When a fact is missing, Canary
asks once and doesn't invent the answer.

## 6. A human decides (4:00 – 4:40)

**Do:** **Create contingency plan from this guide** → **Submit for review**. Then,
in Wyatt's window: **Plans** → open it → tick the confirmation → **Approve**.

**Point at:**
- Only the stages that apply (Detection, Containment, Recovery, Review), each
  with an owner. Koewen owns the runtime-permission check.
- Sureh *can't* approve; only the Administrator can.
- The note that approval **executes nothing** on Fernwood's systems.

**Shows:** AI drafts and people decide. Roles are enforced, and Canary never acts
on a customer's systems by itself.

## 7. Close (4:40 – 5:00)

**Do:** **Audit**.

**Say:** "Every step is on the record: who picked it up, what they answered, who
approved what, and when. HalluSquatting was only published in July. Fernwood has
no security person, and Canary still turned a research article into a P2 alert,
a tailored fix guide, and an approved plan in one afternoon."

**Shows:** accountability, and the one-line value of the product.

---

## If you have one more minute

Pick one; each takes about 30 seconds.

| Show | How | What it proves |
|---|---|---|
| **New evidence** | Sources → **Presenter tools** → **Deliver later follow-up report** → Notifications → **Run processing cycle** | A third source attaches to the same finding, the alert is marked "Updated evidence", and an **Update** email goes out. |
| **Human correction** | On the alert, **Correct** a line of the analysis with a reason | People can fix the AI; the original text is kept, with who changed it and why. |
| **Tenant isolation** | Sign in as `priya` (another organization) and open the Fernwood alert's URL | **Not found.** Organizations never see each other's data. |
| **Honest failure** | Notifications → **Presenter tools** → **Simulate delivery failure** → **Send delivery check** | It shows **Failed (Simulated)**, then **Sent** after **Retry**. Canary never pretends an email went out. |

## Likely questions and straight answers

- **Is this real data?** The threat research is real and linked. Fernwood, its
  people, and its inventory are a sample workspace.
- **Does it use AI?** The analysis and guides are AI-style drafts clearly marked
  for human review. In this build they come from a deterministic template, so the
  demo is repeatable; a live model provider is the next step.
- **Does it fetch live news?** It can (The Hacker News RSS, opt-in). For the
  demo it uses stored copies of the real articles, so it works without internet.
- **Could it take action automatically?** No, by design. It recommends; people
  approve; nothing is executed on customer systems.
- **Is it production-ready?** No. It's a local prototype with no compliance
  claims. Hosting, SSO, and CSRF protection are on the roadmap.

## Before you start

- Run `python run.py --reset`, then `python run.py` (a fresh demo state).
- Open three windows: Wyatt (normal), Sureh (private/incognito), and the inbox
  mapped to Sureh in `.env`. Add any extra routing rules now; a reset clears them.
- Check that the score reads **65/100** (it changes after 2027-01-04; see
  demo-script.md).
- Rehearse once: the whole path takes about 5 minutes once you know the clicks.
