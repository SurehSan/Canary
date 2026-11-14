# CAN-REQ-015: Security, Privacy, Retention, and Safe Data Handling

**Status:** Proposed · **Priority:** Local demo prototype · **Source:** Project Plan §§7, 8, 11

## Purpose
Protect customer information and ensure collection and processing practices match the product's stated boundaries.

## Requirements
1. Enforce organization-level data isolation in all storage and application access paths.
2. Protect authentication secrets and customer data using appropriate access controls and encryption in transit and at rest, subject to deployment capabilities.
3. Collect only information needed for Canary's functions; clearly identify optional organization data and vendor data-access notes.
4. Define retention and deletion behavior for organization profile data, inventory, assessments, alerts, plans, and audit records.
5. Do not include customer data in model prompts or external services unless required for the feature and covered by the selected provider's data handling terms; minimize and protect any such data.
6. Respect source terms, copyright, privacy laws, rate limits, robots rules where applicable, and access restrictions. Do not bypass paywalls or authentication.
7. Provide clear product language that a priority score is not proof of exposure and generated response plans require authorized human review.
8. Do not claim HIPAA or other regulatory compliance based on the project concept alone. If handling regulated data is contemplated, compliance and contractual requirements need explicit implementation review.

## Acceptance criteria
- Access controls prevent cross-tenant reads and writes.
- A documented retention/deletion policy exists before production customer data is stored.
- Third-party data flows (including model and email providers) are inventoried and configured to minimize customer data exposure.
- No data collection mechanism circumvents source access controls.
- Product UI labels potential exposure and AI-generated plans appropriately.

## Dependencies
Applies across all requirements; architecture choices should be reviewed against this requirement from the start.

## Prototype design decisions
- Run locally on one developer machine with fictional/demo data only. Do not expose the app or database publicly and do not enter real patient, customer, credential, or other regulated data. The local prototype is not production-hardened and makes no HIPAA/compliance claim.
- Enforce organization scoping in application queries and mutations. Keep optional model API keys and SMTP credentials in local environment secrets, excluded from version control and logs. Minimize prompt/email data and disclose provider processing/retention terms. Check every email recipient against the CAN-REQ-009 team-owned test allowlist before sending.
- Store local data until the user invokes a full reset; reset removes seeded and user-entered organizations, findings, assessments, plans, and audit records. No backup or recovery guarantee is provided by the prototype.
- Use only approved public source methods, respect applicable rate limits/terms, retain source links and necessary metadata, and avoid full-text article storage. Document collection and model data flows in the design.
- Before any hosted or real-customer use, separately define encryption/key management, backups, incident response, deletion guarantees, provider contractual terms, retention periods, and regulatory scope. These remain explicit production prerequisites, not prototype claims.
