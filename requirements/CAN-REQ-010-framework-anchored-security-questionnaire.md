# CAN-REQ-010: Framework-Anchored Security Questionnaire

**Status:** Proposed · **Priority:** Local demo prototype · **Source:** sureh.md; Project Plan §§7a, 10

## Purpose
Capture a small amount of structured security-practice context and map identified gaps to recognized guidance.

## Requirements
1. Provide a concise questionnaire about how the organization builds and uses AI, with questions mapped to NIST AI RMF and/or OWASP Top 10 for LLM Applications.
2. For each question, display its framework mapping and enough context for a non-specialist to answer.
3. Allow answers such as unknown or not applicable where appropriate; do not force unsupported claims.
4. Save answers, respondent, and assessment date within the organization's workspace.
5. Allow periodic reassessment while preserving prior assessment history.
6. Questionnaire results may inform report recommendations. Threat-based weighting must be explainable and must not rewrite a user's answer.

## Acceptance criteria
- Each question has a traceable framework mapping.
- Authorized users can complete and later review an assessment.
- A new assessment does not erase the prior one.
- Any changed weighting displays why a gap has changed in priority.

## Dependencies
CAN-REQ-001, CAN-REQ-002.

## Prototype design decisions
- Pin the prototype's concise question set to OWASP Top 10 for LLM Applications (2025 edition) so the hallusquatting demo's explicit LLM03 Supply Chain mapping stays stable. Include cited mappings and plain-language explanations; do not imply that this is a complete framework assessment. A later framework update is a separately reviewed design change, not an automatic remapping.
- Use Yes / No / Partial / Unknown / Not applicable answers. Save respondent and assessment date; allow a new assessment without overwriting prior answers. No automatic reassessment schedule: show a reminder/date field only.
- Do not produce a compliance score. Show answered control gaps and their threat-related recommendation weight transparently; changes in weighting never rewrite the user's answer.

## Amendment 2026-11-14: PHP2Shell demo scenario
The question set adds one non-LLM question for the demo: "Are critical security patches applied to
internet-facing systems within 72 hours?", mapped to **CIS Critical Security Controls v8, Safeguard 7.4**
(application patch management). Fernwood's initial assessment answers **No**. It drives the questionnaire-gap
factor for PHP2Shell and the explained threat weighting. The OWASP LLM questions are unchanged.
