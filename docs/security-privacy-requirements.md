# Security and privacy requirements

SEC-001. Canary shall encrypt data in transit with modern TLS and encrypt sensitive data at rest using managed keys. Secrets shall be stored in a secret manager and never in source code or logs.

SEC-002. Tenant authorization shall be enforced server-side for every object and action. Client-side filtering is not a security control.

SEC-003. Administrative actions, incident access, notification decisions, exports, AI outputs, plan changes, and permission changes shall be recorded in tamper-evident audit logs.

SEC-004. Logs shall avoid patient identifiers, credentials, full incident attachments, and model prompts containing sensitive data. Sensitive values shall be redacted before observability systems receive them.

SEC-005. The system shall support data classification, retention schedules, legal holds, deletion requests, export requests, and configurable incident sharing scopes.

SEC-006. A reporter shall be able to publish an anonymized or sector-level lesson while keeping raw incident material restricted to approved analysts.

SEC-007. Uploaded documents and URLs shall be malware-scanned, size-limited, content-type validated, and isolated from executable processing.

SEC-008. External AI providers shall receive only the minimum data needed for the task. Provider retention, training use, location, and subprocessors shall be configurable and documented.

SEC-009. The service shall rate-limit authentication, ingestion, notification, and AI endpoints; protect against CSRF, SSRF, injection, XSS, and broken object-level authorization.

SEC-010. Backups shall be encrypted, access-controlled, tested for restoration, and covered by a documented recovery-point and recovery-time objective.

SEC-011. The team shall maintain a threat model, dependency scanning, vulnerability management, security reviews for releases, and a tested incident-response procedure.

SEC-012. Canary shall present guidance as risk-management assistance, not legal or compliance certification. Jurisdiction-specific obligations require authoritative sources and human review.
