# Demo Flow: HalluSquatting Alert for a Small AI Team

> **SIMULATED DEMO.** Fernwood Labs, its team, inventory, and any
> inventory match are fictional (CAN-REQ-016). The HalluSquatting /
> slopsquatting research is real; source links and dates are shown
> unaltered. Verify the primary disclosures before presenting.

## The company: Fernwood Labs (fictional)

A 5-person startup building **"Ledgerly"**, an AI bookkeeping agent for
small businesses that reads invoices and writes to customers' accounting
systems.

Why HalluSquatting is a direct hit for them:

- Their **coding agents run with auto-approved package installs** to
  ship fast. Nobody reviews dependency names.
- Their product is itself an **agent that fetches resources at
  runtime**, the exact path HalluSquatting hijacks.
- A malicious package would run on machines holding **customers'
  accounting API keys**.
- No one on the team owns security.

| Role (CAN-REQ-001) | Person (fictional) | Mock inbox (CAN-REQ-009) |
|---|---|---|
| Administrator | Maya, CTO | team-owned test address |
| Cybersecurity | Dev, backend engineer | team-owned test address |
| Executive | Priya, CEO | team-owned test address |

## Sequence of events

### 1. Setup (before the demo, ~30 s to show)
- Maya creates the Fernwood Labs workspace and invites the team with roles. *(CAN-REQ-001)*
- AI inventory *(CAN-REQ-002)*:
  - Coding agent: AI coding assistant in agent mode, **auto-install: on**, criticality: High.
  - Runtime agent framework: Python agent framework (version: *unconfirmed*), criticality: Critical.
  - LLM API provider, criticality: Critical.
  - Package sources: PyPI and npm.
- Monitoring sources enabled: The Hacker News, CSA research notes, GitHub Security Advisories, OWASP GenAI. Collection runs hourly; notifications are P1 immediately, everything else in a daily digest. *(CAN-REQ-003)*
- Questionnaire is partially answered. *"Are AI-suggested dependencies reviewed before install?"* is answered **No** (OWASP LLM03: Supply Chain). *(CAN-REQ-010)*

### 2. Collection *(CAN-REQ-004)*
- The scheduled job pulls [The Hacker News: HalluSquatting](https://thehackernews.com/2026/07/new-hallusquatting-attack-could-trick.html) and the [CSA slopsquatting note](https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/04/CSA_research_note_slopsquatting-ai-supply-chain_20260419-csa-styled-1.pdf).
- It records the URL, publication date, retrieval time and outcome.

### 3. Normalize and deduplicate *(CAN-REQ-005)*
- Both articles describe the same technique, so they're merged into one finding: **"HalluSquatting: hallucinated package names used to hijack AI coding agents."**
- The [Xygeni write-up](https://xygeni.io/blog/slopsquatting-evolution/), arriving later, is attached as a third source rather than a new alert.

### 4. AI analysis *(CAN-REQ-006)*
- **Source-confirmed:** models hallucinate package names; attackers pre-register them; agents that install automatically can run malicious code.
- **Unknown:** no specific malicious package names are tied to Fernwood's stack; whether any were installed is unknown.
- **Canary's interpretation (labeled):** auto-install agents are the highest-risk configuration.

### 5. Relevance and priority *(CAN-REQ-007)*
- Match state: **Possible match**, not confirmed. Fernwood uses an agent with auto-install on, but there's no evidence a bad package was installed.
- Priority **P2 High**, with these factors shown:
  - Coding agent with auto-install (inventory)
  - Questionnaire gap on LLM03
  - Runtime agent is Critical
  - Multiple reputable sources
  - Exploitation is in research, not confirmed in the wild, which is why it isn't P1.
- Demo moment: the presenter explains why it isn't P1. This shows that uncertainty stays uncertain. *(CAN-REQ-016.5)*

### 6. Notification *(CAN-REQ-009)*
- The cybersecurity category routes to Dev. P2 goes out as a prompt notification, sent to the **mock inbox only**, with the delivery mode shown as *Test*.
- Show the email: summary, P2, possible match, a "why this matters to you" line, and source links.

### 7. Alert triage *(CAN-REQ-008, CAN-REQ-013)*
- The dashboard shows 1 new high-priority alert.
- Dev opens it, reads what is known and unknown, self-assigns it, and sets the status to **Under investigation**.

### 8. Step-by-step guide *(CAN-REQ-011)*
Dev clicks **Get guide**. Canary drafts ordered steps, each with what to do, why, what to check, and the technique:
1. **Check what was installed.** Compare recent lockfile changes made by the agent against known registries, and flag packages that are new, low-download, or recently registered.
2. **Turn off auto-install** for coding agents, and require human approval for new dependencies.
3. **Pin and allowlist** dependencies, for example a lockfile plus an internal mirror or allowlist.
4. **Restrict the runtime agent** so it can't fetch or install packages, and isolate it from customers' accounting keys.
5. **Rotate credentials** if step 1 finds anything suspicious *(conditional step)*.

**Targeted follow-up** (one question only, because a step depends on it):
> *"Does Ledgerly's runtime agent have permission to install packages in
> production? (Yes / No / Unknown). Needed to decide whether step 4 is
> urgent."*

- Dev answers **Unknown**. Step 4 stays as a clearly labeled conditional step "until confirmed".
- The guide is labeled *AI-generated draft for human review*.

### 9. Contingency plan *(CAN-REQ-012)*
- Dev converts the guide into the plan **"Malicious dependency via AI agent"**, with these stages:
  - Detection: lockfile audit
  - Containment: disable auto-install, revoke the agent's install permissions
  - Recovery: rotate keys, rebuild from pinned dependencies
  - Review: add an LLM03 control
- Owners are assigned: Dev for technical work, Maya for approval.
- The plan stays **Draft → In review** until Maya, as Admin, approves it. This shows human approval is required.

### 10. Close out *(CAN-REQ-008, CAN-REQ-014)*
- Dev finds no suspicious packages. The alert status becomes **Mitigation in progress**, and then **Resolved and verified** once auto-install is off.
- The audit trail shows who did what and when: alert created, assigned, guide answer, plan approved, status changes.
- The questionnaire answer is updated to **Yes**, while the earlier assessment is kept in the history. *(CAN-REQ-010.5)*

## The one-line takeaway for judges

> Six months earlier this attack didn't exist. Fernwood had no security
> person, and Canary still turned a research article into a P2 alert, a
> tailored fix guide, and an approved plan in one afternoon.
