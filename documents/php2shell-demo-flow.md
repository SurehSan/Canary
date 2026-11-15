# Local Demo Flow: PHP2Shell Alert for Fernwood Labs

> **DEMO PROTOTYPE.** Fernwood Labs, Ledgerly, its people, systems, inventory,
> and investigation outcome are fictional. The PHP2Shell vulnerability and the
> sources linked below are real; preserve their claims, links, and publication
> dates. Clearly label any seeded or simulated record in the application.
>
> This flow replaced the earlier HalluSquatting scenario on 2026-11-14.

## Demo organization

Fernwood Labs is a fictional five-person startup building **Ledgerly**, an AI
bookkeeping agent for small businesses. Customers pay through a **billing portal**
that runs on **PHP 8.3.30 under PHP-FPM**. No evidence shows that the portal has
been attacked.

| Prototype role | Person (fictional) | Demo responsibility |
|---|---|---|
| Administrator | Wyatt, CTO | Workspace and source settings; plan approval |
| Cybersecurity Lead 1 | Sureh, backend engineer | Initial investigation and guide |
| Cybersecurity Lead 2 | Koewen, platform engineer | Interim mitigation and internet-exposure check |

Real notification messages go only to the team's allowlisted, team-owned test
addresses, mapped to the fictional recipients above.

## The real event (sources checked 2026-11-14)

**PHP2Shell** is two critical PHP vulnerabilities, **CVE-2026-109618** (RCE via
out-of-memory corruption) and **CVE-2026-109619** (RCE via stale global state).
Both are rated CVSS v4.0 9.2, allow unauthenticated remote code execution, and
affect PHP 5.4 through 8.5.

- [php.net, 21 Oct 2026](https://www.php.net/archive/2026.php): PHP 8.5.12,
  8.4.27, 8.3.36 and 8.2.35 fix both flaws. "There are no complete mitigations,
  updating is the only safe choice." PHP 8.1 and older get no updates from the
  PHP project.
- GitHub security advisories
  [GHSA-w8hw-w9fx-j79w](https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w)
  and
  [GHSA-6wmf-4rv5-p3rp](https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp)
  (21 Oct 2026).
- [The Hacker News, 21 Oct 2026](https://thehackernews.com/2026/10/php-issues-emergency-patches-for-two.html):
  exploitation *attempts* reported by Cloudflare and watchTowr; no confirmed
  break-in had been reported at the time.
- [Check Point, 12 Nov 2026](https://blog.checkpoint.com/security/security-advisory-active-exploitation-of-php2shell-and-local-privilege-escalation/):
  **confirmed in-the-wild exploitation** from October 30 to November 4, 2026,
  used for initial access to internet-facing gateways. This is the follow-up
  evidence in step 3.

## Before the demo

- Start Canary locally and select Fernwood Labs.
- Configure outbound email through the team's chosen SMTP provider using local
  environment secrets, with an explicit allowlist of team-owned addresses.
- Seed the two Cybersecurity Leads (Sureh, Koewen) and the Administrator (Wyatt).
- Seed the inventory. The new item is **Customer billing portal (PHP-FPM)**:
  product PHP, version **8.3.30** (known), Critical. The AI items stay: coding
  assistant, Python runtime agent framework, LLM API provider, and package
  sources.
- Enable PHP security announcements, The Hacker News, CSA research notes,
  GitHub Security Advisories, and OWASP GenAI.
- Save an initial questionnaire assessment with **No** for "Are critical
  security patches applied to internet-facing systems within 72 hours?", mapped
  to CIS Controls v8 Safeguard 7.4 (fictional demo context).

## Walkthrough

### 1. Organization and role setup: CAN-REQ-001, 002

Wyatt opens the workspace, profile, and inventory. The billing portal runs a
**known** PHP version, 8.3.30. Show the two Cybersecurity Leads and the
role-specific actions. The other seeded organization can't read Fernwood's
records.

### 2. Source configuration and collection: CAN-REQ-003, 004

Wyatt opens Sources and shows the enabled sources, last-check status, and the
separate collection and notification cadences. **Refresh sources now** collects
the php.net advisory, both GitHub advisories, and the THN article. Each source
shows its outcome; a failure shows as Failed, never as an empty success.

### 3. Normalize and deduplicate: CAN-REQ-005

The four reports become **one** finding: "PHP2Shell: unauthenticated remote code
execution in PHP (CVE-2026-109618, CVE-2026-109619)".

- The php.net advisory is the primary record.
- Both GitHub advisories attach as **exact** matches through their CVE IDs.
- The THN article matches only by name ("PHP2Shell"), so it's a **proposed**
  grouping that a person can confirm or undo.

Later, **Presenter tools → Deliver later exploitation report (Check Point)**
attaches Check Point's advisory as a fifth source (see step 5b).

### 4. Evidence-backed analysis: CAN-REQ-006

The analysis separates:

- **Source-supported:** the fixed versions, "no complete mitigations", and what
  each CVE does, with citations.
- **Organization context:** the billing portal's PHP 8.3.30 is inside the
  affected range.
- **Unknown:** whether Fernwood's systems were targeted or compromised, and
  whether a vendor backport is installed.
- **Conflicting or unverified:** THN reports exploitation attempts from third
  parties; no primary source has confirmed them yet.
- **Canary interpretation:** an internet-facing service on an affected PHP
  version is urgent patch work. A triage score isn't evidence of compromise.

### 5. Relevance and priority: CAN-REQ-007

**a. Initial alert.** It's a **Confirmed match**, because the exact product is
PHP and 8.3.30 is below the 8.3 branch's fix, 8.3.36. The score is 25 severity +
12 exploitation (attempts reported, unverified) + 20 match + 15 Critical asset +
10 source reliability and recency + 5 questionnaire gap = **87/100**. That's in
the P1 band, but **priority is held at P2 High**: the P1 rule requires credible
active exploitation *and* a Confirmed match to a Critical asset, and exploitation
isn't confirmed yet.

**b. Escalation.** When Check Point's advisory arrives, exploitation becomes
confirmed in the wild (20 points). The score is now **95/100**, the P1 gate is
met, and the alert becomes **P1 Critical**, marked "Updated evidence".

### 6. Real test email: CAN-REQ-009

The cybersecurity-category alert routes to Sureh's test inbox.

- At step 5a it's a **P2**, sent on the next processing cycle
  (**Run processing cycle**).
- At step 5b the escalation to **P1** sends an **Update** email
  **immediately**: "priority P2->P1".

Each message is test-labeled and includes the priority, the match, why it
matters to Fernwood, what's known and unknown, and the source links. A
non-allowlisted address is rejected before sending.

### 7. Alert investigation and dashboard: CAN-REQ-008, 013

Sureh opens the alert, self-assigns it, and moves it to **Under
investigation**. The dashboard counts update from saved records.

### 8. Targeted guide: CAN-REQ-011

Sureh requests a guide directly from the alert. It has five steps:

1. Confirm the PHP version on every internet-facing service (check the package
   changelog for backports).
2. Upgrade PHP to a fixed release (8.3.36 for the 8.3 branch) and restart every
   PHP-FPM worker.
3. Until then, set `session.upload_progress.enabled = 0` in php.ini or the FPM
   pool configuration and restart the workers. This is a partial mitigation
   listed by the PHP advisory.
4. If the portal was reachable from the internet while it ran an affected
   version, look for signs of compromise.
5. Rotate the payment provider API key only if step 4 finds indicators.

The guide asks one targeted question: "Is the Customer billing portal (PHP-FPM)
reachable from the internet?" (Yes / No / Unknown). Sureh answers **Unknown**,
so step 4 stays conditional.

### 9. Human-reviewed contingency plan: CAN-REQ-012

"Critical PHP remote code execution (PHP2Shell)" has these stages:

- **Detection:** check versions and logs.
- **Containment:** upgrade to 8.3.36 or later and restart the workers. Koewen
  applies the interim setting and confirms internet exposure.
- **Recovery:** rebuild and rotate secrets if indicators are found.
- **Review:** adopt a 72-hour patch target (CIS Safeguard 7.4).

The plan moves from **Draft** to **In review**, and Wyatt approves it. Approval
executes nothing.

### 10. Audit history and close-out: CAN-REQ-008, 010, 014

The portal is upgraded to 8.3.36 and no indicators are found. The alert moves
through **Mitigation in progress** to **Resolved and verified**, with a note. A
new questionnaire assessment answers **Yes** for the 72-hour patch target; the
original **No** remains in history.

### 11. Privacy, isolation, and reset: CAN-REQ-015, 016

Show organization scoping, the allowlist, the delivery log, the privacy page, and
the reset. The prototype makes no compliance claim.

## Takeaway

> PHP2Shell went from patch to confirmed attacks in about two weeks. Fernwood has
> no security person, and Canary still matched it to the exact server, held it at
> P2 until exploitation was confirmed, escalated it to P1 the moment it was, and
> turned it into a tailored fix guide and an approved plan.
