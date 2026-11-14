# Local Demo Flow: HalluSquatting Alert for Fernwood Labs

> **DEMO PROTOTYPE.** Fernwood Labs, Ledgerly, its people, assets, inventory,
> and investigation outcome are fictional. The HalluSquatting/slopsquatting
> sources linked below are real; preserve their claims, links, and publication
> dates. Clearly label any seeded or simulated record in the application.

## Demo organization

Fernwood Labs is a fictional five-person startup building **Ledgerly**, an AI
bookkeeping agent for small businesses. In this scenario, coding agents can
install packages automatically, while the runtime agent's installation
permissions are not yet confirmed. No evidence shows that a malicious package
was installed.

| Prototype role | Person (fictional) | Demo responsibility |
|---|---|---|
| Administrator | Wyatt, CTO | Workspace and source settings; plan approval |
| Cybersecurity Lead 1 | Sureh, backend engineer | Initial investigation and guide |
| Cybersecurity Lead 2 | Koewen, platform engineer | Independent inventory/runtime-permission check |

Real notification messages go only to the team's preconfigured, team-owned
test email addresses. Those addresses are mapped to the fictional recipients
above. The characters' names and the fictional company are not real people or
email accounts.

## Before the demo

- Start Canary locally and select the seeded Fernwood Labs organization. Show
  the **Demo data** label.
- Configure outbound email through the team's chosen SMTP-compatible provider
  using local environment secrets. Set an explicit allowlist of team-owned
  test recipient addresses. Do not commit credentials or include them in logs.
- Confirm test mode is active. Every email must be addressed only to an
  allowlisted test inbox and include **[CANARY DEMO - TEST]** in the subject
  and a test-mode label in the body. There is no production-send switch.
- Seed two Cybersecurity Leads, Sureh and Koewen, and one Administrator, Wyatt.
  The invitations are simulated; no invite email is sent.
- Seed inventory: AI coding assistant with auto-install on (High criticality);
  Python runtime agent framework with version Unknown (Critical); LLM API
  provider (Critical); package sources PyPI and npm.
- Enable The Hacker News, CSA research notes, GitHub Security Advisories, and
  OWASP GenAI. Collection can be triggered manually and has a local hourly
  schedule. Notification timing is independent: P1 immediate, P2 in the next
  local processing cycle, P3/P4 in the daily digest.
- Save an initial questionnaire assessment with **No** for “Are AI-suggested
  dependencies reviewed before install?” mapped to OWASP LLM03:2025 Supply
  Chain. This answer is fictional demo context.

## Walkthrough

### 1. Organization and role setup — CAN-REQ-001, 002

Wyatt opens Fernwood's workspace and reviews its profile and AI inventory.
Show the two Cybersecurity Leads, role-specific actions, and that the inventory
version is explicitly Unknown. The other seeded organization, if shown, cannot
read Fernwood's records.

### 2. Source configuration and collection — CAN-REQ-003, 004

Wyatt opens source settings and shows enabled sources, last-check status, and
the separate collection and notification cadences. Trigger a local refresh.
The collector records retrieval outcome, original URL, available publication
date, and retrieval time. If a source fails, show it as a failure, not an
empty successful check.

The demo source set includes:

- [The Hacker News: HalluSquatting](https://thehackernews.com/2026/07/new-hallusquatting-attack-could-trick.html)
- [CSA research note on slopsquatting](https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/04/CSA_research_note_slopsquatting-ai-supply-chain_20260419-csa-styled-1.pdf)
- [Xygeni write-up on slopsquatting](https://xygeni.io/blog/slopsquatting-evolution/), attached later as additional evidence

### 3. Normalize and deduplicate — CAN-REQ-005

The Hacker News and CSA reports are grouped under one canonical finding:
**“HalluSquatting: hallucinated package names used to hijack AI coding
agents.”** Preserve both source links and dates. When the Xygeni item is
introduced later, attach it as a third source to the existing finding. Show
that a user can inspect and correct a proposed grouping.

### 4. Evidence-backed analysis — CAN-REQ-006

Show source-confirmed claims separately from Canary's interpretation and
unknowns:

- **Source-supported:** models can hallucinate package names; attackers can
  register those names; an agent that installs a malicious package may run its
  code.
- **Organization context:** Fernwood's coding assistant has auto-install on;
  the runtime framework version is Unknown.
- **Unknown:** no specific malicious package is tied to Fernwood, and the team
  has not established whether one was installed.
- **Canary interpretation:** automatic dependency installation is a relevant
  risk factor for investigation.

If the optional model API key is unavailable, show the clearly labeled
deterministic demo analysis. Do not invent source facts or state Fernwood is
exposed or compromised.

### 5. Relevance and priority — CAN-REQ-007

Show **Possible match**, not Confirmed: the inventory contains an agent with
automatic installation, but there is no evidence a malicious package was
installed and a product/version match is not established. Show the factors
behind **P2 High**: automatic installation, the LLM03 questionnaire gap,
Critical runtime-agent importance, multiple source references, and no
confirmed active exploitation tied to Fernwood.

For the prototype score, show severity 16/25, exploitation evidence 8/25,
inventory match 12/20, asset criticality 15/15, source reliability/recency
9/10, and questionnaire gap 5/5: total **65/100 (P2)**. No duplicate penalty
applies because this is the initial canonical finding with multiple source
references, not a repeat of a prior finding.

Explain why this is not P1: the prototype's P1 rule requires credible active
exploitation and a Confirmed match to a Critical asset. A score is a triage
recommendation, not proof of exposure.

### 6. Real test email — CAN-REQ-009

Route the cybersecurity-category P2 notification to the configured test
recipient for Sureh. The app records the attempt and outcome. Show the message in
the team's real inbox, including:

- Subject prefixed with **[CANARY DEMO - TEST]**.
- Test-mode label, P2 priority, Possible match, and a concise summary.
- A “Why this may matter to Fernwood” explanation.
- What is known and unknown, plus the preserved source links.
- A clear instruction that the email is a demo notification and not evidence
  of an actual incident.

If email configuration is missing or sending fails, show a visible blocked or
failed delivery state in the app; do not silently fall back to a local mock
inbox or claim the email was sent. Demonstrate that a non-allowlisted address
is rejected before sending.

### 7. Alert investigation and dashboard — CAN-REQ-008, 013

Sureh opens the new alert from the dashboard, reviews evidence and uncertainty,
self-assigns it, and moves it to **Under investigation**. Show the dashboard
count updating from saved records and the source health/status. Koewen is
assigned the parallel check of runtime-agent permissions.

### 8. Targeted guide — CAN-REQ-011

Sureh requests a guide directly from the alert; no general questionnaire is
required first. The draft guide contains ordered steps, rationale, checks,
techniques, and source links:

1. Review recent lockfile and package-manager changes for unfamiliar or
   suspicious dependencies.
2. Turn off automatic package installation for coding agents and require
   human approval for new dependencies.
3. Pin and allowlist dependencies, for example through a lockfile and an
   approved internal mirror.
4. Check whether the runtime agent can install packages in production; if it
   can, restrict that permission and isolate the agent from customer keys.
5. Rotate credentials only if the investigation finds evidence they may have
   been exposed.

The guide asks one targeted clarification:

> Does Ledgerly's runtime agent have permission to install packages in
> production? (Yes / No / Unknown). This determines whether step 4 is an
> immediate action or a precaution to evaluate.

Sureh answers **Unknown**. Step 4 remains conditional until Koewen completes the
check. The guide is labeled **AI-generated draft for human review**. Sureh marks
progress and records the answer.

### 9. Human-reviewed contingency plan — CAN-REQ-012

Sureh converts the guide into **“Malicious dependency via AI agent.”** Use only
applicable stages:

- **Detection:** review lockfiles and package installation history.
- **Containment:** disable automatic installation and revoke agent install
  permission if evidence supports it.
- **Recovery:** rebuild from reviewed, pinned dependencies and rotate keys only
  if exposure is indicated.
- **Review:** add or update the LLM03 dependency-review control.

Sureh owns technical investigation and mitigation; Koewen owns the runtime
permission check; Wyatt reviews and approves. The plan moves from **Draft** to
**In review**. Wyatt, as Administrator, approves it. Show the approval event and
preserved plan version in the audit history. Approval does not execute any
action on Ledgerly.

### 10. Audit history and close-out — CAN-REQ-008, 010, 014

Koewen confirms the runtime agent cannot install packages in production. Sureh
finds no suspicious package in the reviewed lockfiles. The team disables
auto-install for the coding assistant and verifies the setting. The alert
moves through **Mitigation in progress** to **Resolved and verified**, with a
human verification note.

After the team verifies that dependency review is now required, an authorized
respondent creates a **new** questionnaire assessment answering **Yes**. The
original **No** assessment remains unchanged in history. The audit view shows
alert assignment/status changes, guide response and edits, plan approval, and
the new assessment without exposing secrets.

### 11. Privacy, organization isolation, and reset — CAN-REQ-015, 016

Show the Demo data banner, organization scoping, test-email allowlist and
delivery log, and the local reset control. Explain that the prototype uses
fictional data, is not production-hardened, and does not claim HIPAA or other
regulatory compliance. Reset the demo to restore Fernwood's seed state.

## Takeaway

Canary turns public research into a source-backed P2 alert, sends a clearly
marked test email to a real team inbox, guides two Cybersecurity Leads through
an uncertain investigation, and records a human-approved response plan—all in
a local demo prototype without claiming Fernwood was actually exposed.

## The one-line takeaway for judges

> Six months earlier this attack didn't exist. Fernwood had no security
> person, and Canary still turned a research article into a P2 alert, a
> tailored fix guide, and an approved plan in one afternoon.
