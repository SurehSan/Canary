# CAN-REQ-015: Security, Privacy, Retention, and Safe Data Handling

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§7, 8, 11

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

## Open decisions
- Hosting/security baseline, encryption/key management, retention durations, deletion guarantees, incident response, model provider terms, and regulatory scope.
