# Canary Demo Script

A click-by-click script for presenting the local Canary prototype. It follows
the [Fernwood demo flow](hallusquatting-demo-flow.md). The main path runs
**about 8 minutes**; a **3-minute** cut is at the end.

Everything about Fernwood Labs and its people is fictional. The HalluSquatting
sources are real. Say so once at the start, and don't claim that Fernwood was
exposed or compromised.

## Before the demo (10 minutes ahead)

1. In the project folder, confirm that `.env` has the Gmail sender settings and
   App Password, and that `CANARY_SCHEDULER=0` is set. With the scheduler off,
   email goes out only when you click **Run processing cycle**, so you control
   the timing.
2. Run `python run.py --reset`, then `python run.py`. Leave the terminal open.
3. Open **three browser windows**:
   - **Window A** (normal): http://127.0.0.1:5000, signed in as `wyatt` (password `demo`).
   - **Window B** (private/incognito): the same URL, signed in as `sureh`. Two
     people can't share one browser session, so this window needs to be
     private.
   - **Window C**: the DSU inbox (`koewen.hoffman@trojans.dsu.edu`), with the
     Junk folder one click away.
4. Do a quick test: in Window A, go to Notifications → **Send delivery check** to
   the DSU address and confirm it arrives. Then run `python run.py --reset`
   again and sign both windows back in, so the demo starts clean.
5. Zoom both app windows to about 125% so the room can read them.

## Main path (about 8 minutes)

| Time | Window | Do | Say |
|---|---|---|---|
| 0:00 | — | — | "AI tools ship faster than teams can secure them. In February 2026, a crafted GitHub issue prompt-injected the AI triage bot of the Cline coding assistant and led to an unauthorized release of its CLI. IBM's 2026 breach study found one in four malicious breaches were AI-enabled, up 56% in a year. Small teams have no one watching for this. Canary does." |
| 0:30 | A | **Organization** | "Fernwood Labs is a fictional five-person startup. Here's its AI inventory: a coding assistant with auto-install on, and a runtime agent whose version is **Unknown**. Canary never guesses: unknown stays unknown. Two Cybersecurity Leads, Sureh and Koewen, and an Administrator, Wyatt." |
| 1:00 | A | **Sources** → **Refresh sources now** | "Four curated public sources. Collection is separate from notification. Each source shows its real outcome; an outage shows as **Failed**, never as an empty success." |
| 1:30 | A | **Alerts** → open the HalluSquatting alert | "Two real reports, from The Hacker News and a CSA research note, are grouped into one finding with both links and dates. The grouping is *proposed*: a person confirms it." |
| 2:00 | A | Scroll to **Why this may matter** and **Analysis** | "**Possible match**, 65 out of 100, **P2 High**. Every point is explained. It is **not P1**, because P1 needs active exploitation *and* a confirmed match to a critical asset. The analysis keeps source facts, our context, unknowns, and Canary's interpretation separate, and it flags that the two sources disagree about real-world exploitation. A score is triage, not proof of exposure." |
| 3:15 | A | **Notifications** → **Run processing cycle** | "The P2 alert goes to Sureh's test inbox. All email is labeled as a test, and only allowlisted team addresses can receive it." |
| 3:30 | C | Refresh the inbox and open the email | "Here it is in a real inbox: `[CANARY DEMO - TEST]`, priority, why it matters, what's known and unknown, and the sources. It says plainly that it's a demo, not evidence of an incident." |
| 4:00 | A | **Send delivery check** to `someone@example.com` | "An address that isn't on the allowlist is **Rejected** before anything is sent." |
| 4:15 | B | Open the alert → **Assign** to Sureh → **Under investigation** | "Sureh picks it up. Every change is attributed and time-stamped." |
| 4:45 | B | **Get a step-by-step guide** | "There's no questionnaire to fill in first. Five ordered steps, each with why it matters, what to check, and links. It asks **one** targeted question…" |
| 5:15 | B | Answer **Unknown** | "…and if we don't know, step 4 stays conditional. Canary doesn't invent the answer." |
| 5:45 | B | **Create contingency plan** → **Submit for review** | "The guide becomes a plan with only the stages that apply. Koewen owns the permission check. Sureh can recommend it but **can't approve it**." |
| 6:30 | A | **Plans** → open it → tick the confirmation → **Approve** | "Only the Administrator approves, and approval executes nothing on Fernwood's systems." |
| 7:00 | A | **Audit** | "Everything is in the history: who assigned it, the guide answer, who approved what, and when." |
| 7:30 | — | — | "Six months ago this attack didn't exist. Fernwood has no security person, and Canary still turned a research article into a P2 alert, a tailored fix guide, and an approved plan in one afternoon." |

## Extras if there's time

- **Updated evidence** (Window A, 30s): Sources → **Demo step: deliver later
  follow-up report (Xygeni)** → Notifications → **Run processing cycle**. A
  third source is attached, the alert shows "Updated evidence", and an
  **Update** email arrives.
- **Human correction** (Window B, 30s): on the alert, **Correct** an
  interpretation line with a reason. It shows "Corrected by Sureh", and the
  original text is kept in the history.
- **Organization isolation** (30s): sign in as `priya` (Prairie Valley Medical
  Center) and paste the Fernwood alert's URL. The response is **Not found**.
- **Honest failures** (30s): Notifications → **Simulate delivery failure** →
  **Send delivery check** to the DSU address. It shows **Failed (Simulated)**,
  and nothing reaches the mail server. Turn the switch off, press **Retry**, and
  it shows **Sent**.
- **Privacy and data flows** (footer link, 20s): what leaves the machine,
  retention until reset, and no compliance claim.

## 3-minute version

Hook (0:00) → alert with score and factors (0:30) → Run processing cycle and
show the inbox (1:15) → Sureh's guide with the Unknown answer (1:45) → Wyatt
approves the plan (2:30) → takeaway line (2:50). Do the Refresh and the
assignment before you start talking.

## If something goes wrong

| Problem | Do this |
|---|---|
| The email hasn't arrived after about 30 seconds | Check Junk. If it isn't there, show Notifications → delivery log: **Sent**, with the time Gmail accepted it. Say "Gmail accepted it at 3:15; DSU's filter is holding it." |
| The delivery log says **Failed** | Don't hide it: "Canary never pretends an email was sent." The error is shown as a type and code only, for example 535 (sign-in refused). Continue the demo. |
| No internet | Skip the inbox steps. Everything else works offline: the sources are stored copies of the real articles. |
| A page errors or the data gets messy | In the terminal, press Ctrl+C, then run `python run.py --reset` and `python run.py`. It takes about 5 seconds; sign in again in both windows. |
| The score isn't 65 | It changes after 2027-01-04, as the sources age. Before starting the app, set `CANARY_FIXED_NOW=2026-11-14T15:00:00+00:00` in `.env`. |

## Things not to say

- That Fernwood (or anyone) was exposed or compromised. It's a *possible* match.
- "Shadow AI in 43% of breaches." IBM's public material doesn't state it.
- "4,000 machines compromised" (Cline). That number isn't in Cline's post-mortem.
- That Canary is HIPAA-compliant, production-ready, or real-time.
