# CAN-REQ-005: Finding Normalization, Evidence, and Deduplication

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§4, 5, 6, 7, 11

## Purpose
Turn collected records into traceable findings that can be compared, updated, and shown without losing their evidence.

## Requirements
1. Normalize source items into a common finding record with title, event type, affected products/versions where known, severity/source ratings where supplied, publication time, discovery time, and source references.
2. Preserve source-specific values and attribution; Canary-generated interpretation must be labeled as such.
3. Link every finding to one or more original source URLs and retain supporting evidence metadata.
4. Detect likely duplicate reports and link them to a canonical finding while retaining the distinct sources and dates.
5. Update an existing finding when meaningful new source information arrives and retain a change history.
6. Represent missing, conflicting, or unverified values explicitly; do not infer confirmed facts from absence.

## Acceptance criteria
- A user can inspect a finding's source links, timestamps, and source-provided facts.
- Two reports of the same event can be recognized as related without losing their separate citations.
- Conflicting source claims remain visible as conflicting or uncertain.
- An update changes the current view and preserves a record of what changed.

## Dependencies
CAN-REQ-004.

## Open decisions
- Canonical identity and duplicate matching policy, including human correction capability.
- How much source text may be stored and for how long, subject to source terms and CAN-REQ-015.
