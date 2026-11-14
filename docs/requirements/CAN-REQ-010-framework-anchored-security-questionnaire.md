# CAN-REQ-010: Framework-Anchored Security Questionnaire

**Status:** Proposed · **Priority:** MVP · **Source:** sureh.md; Project Plan §§7a, 10

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

## Open decisions
- Which framework/version and which questions ship in the MVP; assessment cadence and scoring model.
