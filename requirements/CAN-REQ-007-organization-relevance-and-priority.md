# CAN-REQ-007: Organization Relevance and Priority Assessment

**Status:** Proposed · **Priority:** Local demo prototype · **Source:** Project Plan §§5, 6, 7

## Purpose
Help teams triage findings using their supplied context without overstating exposure.

## Requirements
1. Assess relevance using available evidence about affected technology, organization inventory, industry, monitoring interests, system importance, exploitation status, source reliability, recency, and duplication.
2. Assign a configurable four-level triage priority: P1 Critical, P2 High, P3 Medium, or P4 Informational.
3. Show the factors and evidence that contributed to the relevance and priority assessment.
4. Distinguish confirmed inventory matches, possible matches, industry-only relevance, and no known match.
5. Treat priority as a recommendation; it must not assert confirmed exposure or compromise without evidence.
6. Allow authorized reviewers to adjust priority or relevance state and capture the reason.

## Acceptance criteria
- A user can see why a finding was assigned its priority and what inventory evidence was used.
- An industry-only match is labeled as potential relevance, not confirmed exposure.
- Unknown versions do not create a confirmed affected-version match.
- A reviewer can override a recommendation and the override is visible.

## Dependencies
CAN-REQ-002, CAN-REQ-006.

## Prototype design decisions
- Code assigns match state. Confirmed requires an exact product match and a known inventory version overlapping the source's affected-version range. Possible means a product/technology match exists but version, deployment, or installation evidence is incomplete. Industry-only is context without an inventory match; No known match means no supported relationship. Unknown versions can never produce Confirmed.
- Compute a visible 0–100 triage score from severity (0–25), exploitation evidence (0–25), inventory match (0–20), asset criticality (0–15), source reliability/recency (0–10), and relevant questionnaire gap (0–5); subtract 10 for a confirmed duplicate with no new material information. Map 80–100 to P1, 60–79 to P2, 35–59 to P3, and 0–34 to P4. Show factor values and source/context evidence.
- P1 additionally requires credible active exploitation and a Confirmed match to a Critical asset; otherwise cap at P2. For the demo, hallusquatting is P2 / Possible because research describes the technique but no malicious package is tied to Fernwood. Priority is triage guidance, never evidence of exposure.
- Authorized users may override match or priority for the current finding only, with a required reason. Overrides do not silently change the scoring rules or future assessments. Initial default routing is P1 immediate test email, P2 prompt test email, P3/P4 daily digest; all email is restricted to the CAN-REQ-009 team-owned address allowlist.
