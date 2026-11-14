# CAN-REQ-004: External Source Collection

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§7, 10

## Purpose
Collect public security advisories and AI-related threat information reliably and respectfully.

## Requirements
1. Scheduled collection retrieves new or changed records from enabled, approved sources using their documented APIs, RSS, or permitted access methods.
2. Collection records source identifier, original URL, publication/update time when supplied, retrieval time, and retrieval outcome.
3. Collection is resilient to transient failures and records retries or errors without silently dropping them.
4. Requests respect source rate limits and terms of use.
5. Store only content needed for Canary's workflow; prefer factual fields, metadata, and source links over republishing entire articles.
6. Collection frequency is configurable independently from alert delivery frequency and is not represented as real-time unless the source supports it.

## Acceptance criteria
- A new source record can be collected and its original URL and available dates are preserved.
- A failed request is distinguishable from a successful check with no new records.
- Re-running collection over the same source data does not create uncontrolled repeated copies.
- Collection obeys configured rate limits and does not bypass technical or contractual access restrictions.

## Dependencies
CAN-REQ-003.

## Open decisions
- Job scheduler, retry policy, latency target, supported formats, and source-specific adapters.
- Whether collection is global and shared or performed per organization.
