# Product requirements

## Product definition

Canary helps organizations learn from verified AI and cybersecurity incidents. When a hospital reports a medical-record breach, Canary identifies organizations with similar exposure, sends an appropriately scoped notification, explains the lessons that apply, and guides each recipient through a review and mitigation plan.

The WILDFIRE brief describes Canary as a practical, adaptive AI safety tutor that tracks current events and regulations, assesses project or company risk, teaches threats such as prompt injection, model inversion, distillation, and data leakage, and uses a friendly interface and mascot.

## Primary users

- Security, privacy, and compliance leads at hospitals and other regulated organizations.
- Engineering and IT leads responsible for AI-enabled products or AI-assisted development.
- Smaller organizations without a dedicated AI-risk team.
- Incident reporters and trusted analysts who submit or validate an event.

## User outcomes

Recipients should be able to determine whether an incident is relevant to them, understand the likely exposure, identify evidence they need to check, assign owners, and track mitigation to completion. Reporters should be able to share reusable lessons without exposing unnecessary patient, customer, or company secrets.

## MVP boundaries

The MVP must support incident intake, analyst review, relevance matching, notification delivery, source-linked explanations, guided questionnaires, action plans, ownership and status tracking, and an audit trail. It must not claim to certify compliance, guarantee that an organization is safe, or automatically change production systems.

## Product principles

1. Relevance over volume: notify only organizations whose declared profile and technology exposure make an event plausibly useful.
2. Evidence before confidence: every important claim has a source, timestamp, and confidence level.
3. Human approval for material decisions: analysts approve incidents and organizations approve plans before they become official.
4. Minimum necessary disclosure: recipients see the details needed to act, while reporter identity and sensitive facts remain protected.
5. Explainable guidance: users can see why a question, risk, or recommendation was presented.
6. Actionability: every high-priority risk has an owner, due date, and measurable completion check.
