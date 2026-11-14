# Acceptance criteria

## Hospital breach scenario

Given Hospital A reports that an exposed application allowed unauthorized access to medical records, an analyst validates the report and marks it approved, and Hospital B has declared a similar patient-record system:

1. Canary identifies Hospital B as a candidate recipient and shows the matching factors to an analyst.
2. The analyst can restrict the notification to the healthcare sector and hide Hospital A’s identity and patient details.
3. Hospital B receives one notification containing the incident summary, urgency, source citations, date, and why the event may apply.
4. The notification links to a questionnaire about exposed interfaces, authentication, authorization, logging, monitoring, vendor access, and data protection.
5. The questionnaire supports unknown answers and saves progress without losing prior responses.
6. After completion, Canary proposes action items such as reviewing access controls, checking logs, validating vendor permissions, rotating exposed secrets, and testing detection. Each item includes rationale, priority, owner, due date, and verification evidence.
7. A Hospital B responder can edit and approve the plan; an administrator can assign owners and mark an item complete only with evidence or an explicit reviewer note.
8. The audit log records incident version, notification decision, recipients, AI model and sources used, plan edits, approvals, and evidence uploads.
9. If the incident is withdrawn or corrected, Hospital B receives a linked correction and the prior version remains auditable.

## Release gates

- No cross-tenant data is returned in authorization tests.
- 100% of material generated claims in the regression set have valid citations or are explicitly labeled unknown/inference.
- Critical notification tests demonstrate durable delivery, retry, deduplication, and correction behavior.
- Security tests cover upload handling, prompt injection, SSRF, XSS, CSRF, rate limiting, and broken object-level authorization.
- A human reviewer can reconstruct why each notification and action item was produced.
- A tenant can export and delete its data according to its configured retention policy.
