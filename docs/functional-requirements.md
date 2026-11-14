# Functional requirements

## Roles and tenancy

FR-001. The system shall isolate each organization’s users, profiles, incidents, plans, and evidence by tenant.

FR-002. Roles shall include organization administrator, security/privacy responder, plan contributor, read-only viewer, incident reporter, and Canary analyst. Permissions shall be least-privilege and configurable by tenant administrators.

FR-003. The system shall support SSO or email-based authentication with MFA for administrators and responders.

## Organization profile

FR-010. An administrator shall record industry, jurisdictions, sites, critical systems, data classes, AI models and vendors, deployment environments, integrations, and notification preferences.

FR-011. Users shall be able to mark profile fields as verified, unknown, or outdated. The system shall show when each field was last reviewed.

## Incident intake and review

FR-020. An authorized reporter shall submit an incident with title, date, affected sector, attack or failure type, affected assets and data classes, observed impact, mitigations, indicators, sources, and sharing restrictions.

FR-021. The system shall accept structured fields and supporting documents or URLs, scan uploads for malware, and record provenance for every extracted fact.

FR-022. An analyst shall classify severity, confidence, incident status, affected technologies, applicability, disclosure level, and recommended recipient segments before publication.

FR-023. The system shall support draft, under review, approved, published, superseded, and withdrawn incident states. Withdrawals shall trigger correction notices.

## Relevance and notification

FR-030. For each approved incident, Canary shall calculate an explainable relevance score using organization profile, technology exposure, geography, sector, data type, severity, and notification preferences.

FR-031. The system shall show the matching factors and uncertainty to an analyst before sending notifications.

FR-032. Notifications shall include a concise summary, why the recipient was selected, affected risk areas, urgency, source links, recommended first steps, and a link to the guided review.

FR-033. Delivery shall support in-app notifications and email at minimum. The system shall record delivery, bounce, open, acknowledgement, snooze, unsubscribe, and escalation events.

FR-034. Tenants shall configure severity thresholds, quiet hours, escalation contacts, and digest frequency. Critical notifications may bypass quiet hours when an administrator has enabled that policy.

## Guided assessment and action plan

FR-040. A recipient shall complete a tailored questionnaire covering exposure, controls, evidence, business impact, and existing mitigations. The system shall allow “unknown” and save progress.

FR-041. Questions shall adapt based on prior answers and the organization profile, while preserving a visible explanation for each question’s relevance.

FR-042. Canary shall generate a draft action plan containing risk statement, evidence gap, recommended control, priority, owner, due date, dependencies, verification method, and source rationale.

FR-043. Users shall edit, approve, reject, defer, assign, and comment on plan items. A plan shall have statuses draft, approved, in progress, blocked, complete, and accepted-risk.

FR-044. Completion shall require evidence or a reviewer note. Accepted risks shall require an approver, rationale, review date, and expiration date.

FR-045. The system shall provide progress dashboards, overdue reminders, export to PDF/CSV, and an immutable history of plan changes.

## Knowledge and correction

FR-050. The system shall maintain source, publication date, retrieval date, jurisdiction, reliability, and licensing metadata.

FR-051. Analysts shall be able to correct extracted facts, merge duplicate incidents, mark stale guidance, and publish updates linked to the original notification.

FR-052. Users shall be able to report an incorrect recommendation or irrelevant notification. Feedback shall be triaged and auditable.
