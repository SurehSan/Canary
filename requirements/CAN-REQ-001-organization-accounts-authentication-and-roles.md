# CAN-REQ-001: Organization Accounts, Authentication, and Roles

**Status:** Proposed · **Priority:** Local demo prototype · **Source:** Project Plan §§3, 8, 10

## Purpose
Provide a company workspace where multiple people can use Canary with permissions appropriate to their responsibilities.

## Scope
Create an organization, authenticate members, invite users, assign roles, and enforce permissions within the organization. The local prototype uses demo authentication; external identity providers and SSO are outside its scope.

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

## Prototype design decisions
- Use local demo accounts with seeded credentials and no external identity provider, SSO, MFA, or account recovery flow. Clearly mark this authentication as demo-only.
- Support Administrator and Cybersecurity Lead only, as specified in the requirement note. Administrators create organizations, manage members and source settings, and approve plans. Cybersecurity Leads can investigate and assign alerts, edit guides and draft plans, and recommend approval; they cannot manage membership or approve plans.
- An Administrator may invite another demo user by selecting a seeded account; invitations are simulated and do not send email. Support membership revocation and show that the revoked account loses access.
- Users may belong to multiple demo organizations. Every query and mutation must be scoped to the currently selected organization; demonstrate isolation with two fictional organizations. MFA/recovery are outside the local prototype boundary.
