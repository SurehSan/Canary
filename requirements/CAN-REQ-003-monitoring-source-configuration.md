# CAN-REQ-003: Monitoring Source Configuration

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §7

## Purpose
Let Canary monitor a curated set of sources selected for trust and customer priorities.

## Requirements
1. Canary provides a documented, maintainable set of recommended source definitions for the initial supported feeds.
2. A source definition identifies its name, type, canonical URL/API, topic coverage, and retrieval method; operational status and last successful check are visible to administrators.
3. Authorized administrators can enable or disable supported sources for their organization and select monitoring areas.
4. The system supports source-level configuration without allowing customers to bypass access restrictions or cause arbitrary unsafe fetching.
5. Source configuration distinguishes collection frequency from notification frequency.
6. A source's terms, rate limits, and permitted use are reviewed before enabling production collection.

## Acceptance criteria
- An administrator can see enabled sources and their most recent check status.
- Disabling a source stops future scheduled collection for that organization as applicable.
- A source outage or rate-limit condition is visible and does not appear as a successful empty result.
- No source configuration performs authenticated, paywalled, or access-control-bypassing retrieval.

## Dependencies
CAN-REQ-001. Collection behavior is defined in CAN-REQ-004.

## Open decisions
- Exact initial source list and whether sources are global defaults, per-organization subscriptions, or both.
- Supported source types and customer ability to add sources.
- Initial polling intervals. The plan's frequency examples are proposals, not service guarantees.
