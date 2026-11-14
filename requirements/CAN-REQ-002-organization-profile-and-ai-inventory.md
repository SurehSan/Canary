# CAN-REQ-002: Organization Profile and AI Asset Inventory

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§3, 5, 6, 10

## Purpose
Capture enough customer context to make threat alerts relevant and explain why a finding may apply.

## Requirements
1. An authorized user can record organization name, industry, organization size/location where relevant, and monitoring interests.
2. An authorized user can maintain an AI inventory with, at minimum, product/tool or provider name and optional product category, version, business owner/team, and criticality.
3. Inventory entries can represent models, LLM APIs, AI-enabled products, agents, coding assistants, and AI libraries.
4. Users can record vendor data access or related notes only when authorized to provide that information; fields should be optional and purpose clear.
5. Users can create, edit, and remove inventory entries and mark information as unknown or unconfirmed rather than inventing a value.
6. The system records when profile/inventory information was last updated and uses the organization context only within that organization.

## Acceptance criteria
- An organization can save and later edit its profile and AI inventory.
- Inventory items can be linked to teams and criticality when supplied.
- A missing version is represented as unknown and does not become a positive match.
- A different organization cannot access this organization's profile or inventory.

## Dependencies
CAN-REQ-001.

## Open decisions
- Required versus optional profile fields and inventory import/export format.
- Whether the MVP supports integrations or manual entry only.
- Data retention and deletion behavior are governed by CAN-REQ-015.
