# CAN-REQ-001: Organization Accounts, Authentication, and Roles

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§3, 8, 10

## Purpose
Provide a company workspace where multiple people can use Canary with permissions appropriate to their responsibilities.

## Scope
Create an organization, authenticate members, invite users, assign roles, and enforce permissions within the organization. SSO is optional and not required for the first demonstrable MVP unless selected as an implementation decision.

## Requirements
1. A user can register and sign in using the selected authentication mechanism.
2. An authenticated user can create an organization and become its initial administrator.
3. An administrator can invite a person to the organization and assign or change that person's role.
4. The system supports the conceptual roles Administrator, Safety, Cybersecurity, Executive, and Employee. Permissions may be refined during implementation, but must be explicit and enforced server-side.
5. A user can belong to one or more organizations only if the chosen data model explicitly scopes all access to the selected organization.
6. A user can revoke a member's access; revoked users cannot access that organization's data.
7. Authentication and authorization failures do not disclose whether another organization's records exist.

**Note**: Only include "Administrator" and "Cybersecurity Lead" roles within the Prototype build.

## Acceptance criteria
- A new user can create an organization and access its workspace.
- An administrator can invite a second user and assign a role.
- Users with different roles receive only the capabilities assigned to those roles.
- A member removed from an organization can no longer read or modify its protected data.
- Automated authorization checks cover cross-organization access attempts.

## Dependencies
None. Provides identity and organization context for most other requirements.

## Open decisions
- Authentication provider and password/SSO support for MVP.
- Exact permission matrix for each role, invitation expiry, and whether one user may join multiple organizations.
- MFA requirement and recovery process.
