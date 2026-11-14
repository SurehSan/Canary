# CAN-REQ-007: Organization Relevance and Priority Assessment

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§5, 6, 7

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

## Open decisions
- Scoring rubric and thresholds, default escalation policy, and whether customer overrides affect future assessments.

**Note:** Scoring rubric and thresholds should be more established within the design phase.
