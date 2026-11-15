# Canary Demo Script

A click-by-click script for presenting the local Canary prototype. It follows
the [Fernwood demo flow](php2shell-demo-flow.md), built around the real
**PHP2Shell** vulnerability. The main path runs **about 8 minutes**; a
**3-minute** cut is at the end.

Fernwood Labs, its people, and its systems are fictional. The PHP2Shell
vulnerability and every linked source are real. Say so once at the start, and
don't claim that Fernwood was attacked or compromised.

## Before the demo (10 minutes ahead)

1. In the project folder, confirm that `.env` has the Gmail sender settings and
   App Password, and that `CANARY_SCHEDULER=0` and `CANARY_PRESENTATION_MODE=1`
   are set. With the scheduler off, P2 email goes out only when you click **Run
   processing cycle**, so you control the timing. (P1 email always goes out
   immediately.) Presentation mode hides the demo labels. The scripted events
   (the Check Point report, outages, delivery failure) are in a collapsed
   **Presenter tools** panel at the bottom of Sources and Notifications, visible
   to Administrators only. The sign-in page doesn't list accounts: use `wyatt`
   and `sureh`, and every password is `demo`.
2. Open a new terminal (VS Code loads `.env` into new terminals), then run
   `python run.py --reset` and `python run.py`. Leave the terminal open.
3. Open **three browser windows**:
   - **Window A** (normal): http://127.0.0.1:5000, signed in as `wyatt`.
   - **Window B** (private/incognito): the same URL, signed in as `sureh`.
   - **Window C**: the inbox `.env` maps to Sureh (`CANARY_TEST_RECIPIENTS`),
     with the Junk folder one click away.
4. Do a quick test: in Window A, go to Notifications → **Send delivery check** to
   that inbox and confirm it arrives. Then reset again (step 2) and sign both
   windows back in, so the demo starts clean.
5. Zoom both app windows to about 125% so the room can read them.

## Main path (about 8 minutes)

| Time | Window | Do | Say |
|---|---|---|---|
| 0:00 | — | — | "On October 21, PHP shipped emergency fixes for two critical flaws, called PHP2Shell, that let anyone on the internet run code on a PHP server. Within days attackers were trying them, and on November 12 Check Point confirmed real break-ins. A five-person startup has nobody watching for this. Canary does. Everything you'll see is a sample company; the vulnerability and the sources are real." |
| 0:30 | A | **Organization** | "Fernwood Labs builds an AI bookkeeping product. Customers pay through a billing portal on **PHP 8.3.30**, and it's marked Critical. Canary knows the exact version, because the team recorded it. If they hadn't, it would stay **Unknown** and Canary would never guess." |
| 1:00 | A | **Sources** → **Refresh sources now** | "Curated public sources: the PHP project, GitHub's advisory database, and security news. Collection runs separately from notifications. Each source shows its real outcome; an outage shows as **Failed**, never as an empty success." |
| 1:30 | A | **Alerts** → open the **PHP2Shell** alert | "Four reports become one finding. The PHP advisory is the primary record. GitHub's two advisories attach automatically, because the CVE numbers match exactly. The news article only matches by name, so it's a *proposed* grouping that a person confirms." |
| 2:00 | A | Scroll to **Why this may matter** and **Priority factors** | "It's a **Confirmed match**: 8.3.30 is below 8.3.36, the fix for that branch. The score is **87 out of 100**, which is in P1 range, but it's held at **P2 High**. P1 requires *confirmed* active exploitation, and right now there are only third-party reports of attempts, flagged here as unverified. Every point is explained, and a score is triage, not proof the portal was attacked." |
| 3:00 | A | **Notifications** → **Run processing cycle (P1/P2)** | "The P2 alert goes to Sureh, the Cybersecurity Lead. Only approved addresses can receive email." |
| 3:15 | C | Refresh the inbox and open the email | "The P2 email: priority, why it matters to Fernwood, what's known and unknown, and the source links." |
| 3:40 | A | **Sources** → **Presenter tools** → **Deliver later exploitation report (Check Point)** | "Now it's November 12. Check Point publishes an advisory confirming real attacks." |
| 4:00 | A | Open the alert again | "Canary escalates on its own: **P1 Critical, 95 out of 100**. The P1 rule is now met, because exploitation is confirmed *and* this is a confirmed match on a critical system. It's marked **Updated evidence**." |
| 4:15 | C | Refresh the inbox | "And the P1 update email arrived immediately, without waiting for a cycle: 'priority P2 to P1'." |
| 4:30 | A | Notifications → **Send delivery check** to `someone@example.com` | "An address that isn't approved is **Rejected** before anything is sent." |
| 4:45 | B | Open the alert → **Assign** to Sureh → **Under investigation** | "Sureh picks it up. Every change is attributed and time-stamped." |
| 5:15 | B | **Get a step-by-step guide** | "Five ordered steps, each with why it matters, what to check, and links: confirm the version, upgrade to 8.3.36, apply the PHP project's interim setting until then, check for signs of compromise, and rotate keys only if something is found. It asks **one** targeted question…" |
| 5:45 | B | Answer **Unknown** to "Is the billing portal reachable from the internet?" | "…and if we don't know, the compromise check stays conditional. Canary doesn't invent the answer." |
| 6:15 | B | **Create contingency plan from this guide** → **Submit for review** | "The guide becomes a plan with only the stages that apply. Koewen owns the interim mitigation and the exposure check. Sureh can recommend the plan but **can't approve it**." |
| 6:45 | A | **Plans** → open it → tick the confirmation → **Approve** | "Only the Administrator approves, and approval executes nothing on Fernwood's systems." |
| 7:15 | A | **Audit** | "Everything is on the record: the escalation, the assignment, the guide answer, and who approved what, and when." |
| 7:40 | — | — | "PHP2Shell went from patch to confirmed attacks in about two weeks. Fernwood has no security person, and Canary matched it to the exact server, held it at P2 until attacks were confirmed, escalated it to P1 the moment they were, and turned it into a fix guide and an approved plan." |

## Extras if there's time

- **Human correction** (Window B, 30s): on the alert, **Correct** an
  interpretation line with a reason. It shows "Corrected by Sureh", and the
  original text is kept in the history.
- **Organization isolation** (30s): sign in as `priya` (Prairie Valley Medical
  Center) and paste the Fernwood alert's URL. The response is **Not found**.
  Prairie Valley also has no PHP in its inventory, so it gets no alert.
- **Honest failures** (30s): Notifications → **Presenter tools** → **Simulate
  delivery failure** → **Send delivery check**. It shows **Failed (Simulated)**,
  and nothing reaches the mail server. Turn the switch off, press **Retry**, and
  it shows **Sent**.
- **Privacy and data flows** (footer link, 20s): what leaves the machine,
  retention until reset, and no compliance claim.

## 3-minute version

Hook (0:00) → the alert at 87 held at P2, and why (0:30) → Presenter tools →
Check Point report → **P1, 95** and the immediate update email (1:15) → Sureh's
guide with the Unknown answer (2:00) → Wyatt approves the plan (2:30) → takeaway
(2:50). Do the Refresh and the first processing cycle before you start talking.

## If something goes wrong

| Problem | Do this |
|---|---|
| The email hasn't arrived after about 30 seconds | Check Junk. If it isn't there, show Notifications → delivery log: **Sent**, with the time the mail server accepted it. Say "The mail server accepted it and it hasn't reached the inbox yet. Delivery after that point is outside Canary, and the log shows exactly what happened on our side." Don't guess at the cause. |
| The delivery log says **Failed** | Don't hide it: "Canary never pretends an email was sent." The error is shown as a type and code only, for example 535 (sign-in refused). Continue the demo. |
| No internet | Skip the inbox steps. Everything else works offline: the sources are stored copies of the real advisories and articles. |
| A page errors or the data gets messy | In the terminal, press Ctrl+C, then run `python run.py --reset` and `python run.py`. It takes about 5 seconds; sign in again in both windows. |
| The alert isn't 87 / P2 after Refresh | You probably delivered the Check Point report already (it's then 95 / P1). Reset and start again. |

## Things not to say

- That Fernwood's portal was attacked or compromised. It runs an *affected
  version*; nothing shows it was targeted.
- "There's no mitigation at all." The PHP project says there are no *complete*
  mitigations; updating is the only safe choice. The interim setting reduces
  exposure for one of the two flaws.
- "CVSS 10." The PHP project rates both flaws 9.2 (CVSS v4.0). Higher scores
  came from third parties.
- Specific dates for CISA's known-exploited listing. We didn't verify them
  against CISA directly.
- That Canary is HIPAA-compliant, production-ready, or real-time.
