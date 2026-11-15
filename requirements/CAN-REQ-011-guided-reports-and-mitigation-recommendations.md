# CAN-REQ-011: Step-by-Step Threat Guide and Mitigation Techniques

**Status:** Proposed · **Priority:** Local demo prototype · **Source:** sureh.md; Project Plan §§1, 6, 7a, 10

## Purpose
Turn a threat or supported scenario into a clear, ordered guide that helps an organization assess relevance and work through appropriate mitigation techniques. The output should guide a user through decisions and actions, rather than present a single undifferentiated list of recommendations.

## User flow
1. The user opens a relevant alert or selects a supported scenario and requests a guide.
2. Canary uses available evidence and organization context to draft ordered steps, including techniques for assessing and mitigating the threat.
3. Each step explains what to do, why it matters, and what information or evidence the user should check.
4. If missing organization context prevents Canary from making a step clear or appropriately tailored, Canary asks a small, targeted follow-up question. It uses the security questionnaire capability in CAN-REQ-010 only for this clarification.
5. Canary incorporates the answer and presents the revised guide for human review.
6. The user can edit steps, mark progress, or use the reviewed guide as the basis for a contingency plan under CAN-REQ-012.

## Requirements
1. A user can request a step-by-step guide from an alert or supported scenario.
2. Present actions in a sensible sequence. Steps may cover validation, containment or mitigation, recovery, and follow-up as relevant to the specific threat; do not force irrelevant stages.
3. Each step includes an action, the reason it matters, relevant evidence or conditions to check, and a mitigation technique where applicable.
4. Tailor the guide using confirmed finding facts, explicit uncertainty, and available organization profile and inventory data.
5. Do not require or launch a general questionnaire before generating the initial guide. Ask questionnaire questions only when a specific missing or ambiguous fact materially prevents the guide from being clear or relevant.
6. Any clarification question must be targeted to the identified gap, explain briefly why the answer is needed, and allow “unknown” or “not applicable” where meaningful. Do not ask for information already available in the organization's context.
7. If the user cannot answer, continue with a clearly labeled conditional step or state the limitation; do not assume an answer.
8. Distinguish source-supported facts, organization-provided answers, generated guidance, and unknowns. Keep source references available at the relevant steps.
9. Label the guide as AI-generated draft guidance for human review. Do not claim exposure or compromise without supporting evidence, and do not execute actions on customer systems.
10. Avoid unsafe or overly specific operational instructions when evidence is insufficient; direct the user to authoritative vendor or organizational guidance where appropriate.
11. Authorized users can edit steps and record progress or completion, preserving relevant change history.

## Acceptance criteria
- A user can generate a guide from an alert without first completing the general security questionnaire.
- The guide presents ordered, actionable steps, each with a rationale and relevant checks or mitigation technique.
- If relevant context is missing, Canary asks only a targeted clarification question and explains why it matters.
- If the user answers “unknown,” the guide remains useful by showing a conditional action or explaining the limitation without inventing facts.
- Steps distinguish confirmed facts from assumptions and link to supporting evidence where available.
- A user can edit the draft and record progress before using it as a basis for an approved contingency plan.

## Dependencies
CAN-REQ-006 and CAN-REQ-007. CAN-REQ-010 is used conditionally when targeted questionnaire clarification is needed; it is not a prerequisite for generating a guide. CAN-REQ-012 may consume the reviewed guide to create a contingency plan.

## Prototype design decisions
- Each guide step has Draft, In progress, Done, or Deferred status and displays action, rationale, evidence/checks, technique, source/framework links, and any condition that must be verified. Keep the guide editable and preserve changes in history.
- Generate the initial guide directly from the alert; ask only a targeted question when a missing fact materially changes guidance. Ask one at a time, accept Unknown/Not applicable, and retain conditional steps when unanswered. The hallusquatting flow demonstrates the production install-permission question.
- Link to relevant OWASP Top 10 for LLM Applications (2025 edition) guidance and authoritative vendor/advisory sources. Label all generated content “AI-generated draft for human review.” Do not execute actions or claim exposure.
- Guide export is outside the local prototype; users can view and edit it in the application and create a linked plan.

## Amendment 2026-11-14: PHP2Shell demo scenario
The demo guide covers PHP2Shell in five steps:

1. Confirm the PHP version, including vendor backports.
2. Upgrade to a fixed release and restart the workers.
3. Apply the interim `session.upload_progress.enabled = 0` until then.
4. Check for signs of compromise.
5. Rotate secrets only if indicators are found.

The targeted question is "Is the Customer billing portal (PHP-FPM) reachable from the internet?" (Yes / No /
Unknown). It is not asked when the inventory already records the answer.
