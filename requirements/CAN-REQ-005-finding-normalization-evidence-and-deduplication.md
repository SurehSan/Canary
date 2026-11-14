# CAN-REQ-005: Finding Normalization, Evidence, and Deduplication

**Status:** Proposed · **Priority:** Local demo prototype · **Source:** Project Plan §§4, 5, 6, 7, 11

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

## Prototype design decisions
- Prefer exact CVE/advisory identifiers, then affected product plus vendor identifier, then canonical URL; use normalized title similarity only to propose a duplicate for human review, never as sole proof. Preserve distinct source references and dates under a canonical finding.
- Authorized users can confirm or undo a proposed grouping; record the correction in history. Meaningful source updates revise the current finding while preserving prior values.
- Retain normalized metadata, citations, and only short source excerpts needed for the demo where terms permit. Avoid storing full articles. Local records persist until the explicit demo reset; see CAN-REQ-015.
