# CAN-REQ-004: External Source Collection

**Status:** Proposed · **Priority:** Local demo prototype · **Source:** Project Plan §§7, 10

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

## Prototype design decisions
- Use a local hourly scheduler and administrator-triggered manual refresh. Support only the source-specific RSS/API/public adapters in the CAN-REQ-003 starter catalog. Run collection centrally once and associate resulting findings with organizations whose source and monitoring settings match.
- Retry transient failures up to three times with short bounded backoff; record each attempt and expose terminal failures to the administrator. No latency guarantee is made. Preserve original URL, available publication/update time, retrieval time, and outcome.
- Store normalized metadata and source links; retain only short excerpts required for analysis where source terms permit. Do not bypass access controls or reproduce full articles. Deduplicate repeat collection through CAN-REQ-005 identity rules.
