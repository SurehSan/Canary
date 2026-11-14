# CAN-REQ-006: AI-Assisted Analysis and Factual Uncertainty

**Status:** Proposed · **Priority:** MVP · **Source:** Project Plan §§6, 7, 11

## Purpose
Use language models to help classify and explain findings while keeping evidence and uncertainty clear.

## Requirements
1. Analysis identifies event type, entities/products, affected versions, industries, exploitation claims, and relevant dates when supported by input evidence.
2. Generated summaries distinguish source-confirmed facts from model interpretation, assumptions, and unknowns.
3. Claims include links or references to the supporting source evidence where possible.
4. The system identifies when sources conflict or evidence is insufficient and requests human verification rather than presenting an unsupported conclusion as fact.
5. The model must not claim an organization is exposed or compromised solely from an industry match or headline.
6. Analysis results are reviewable and can be corrected by authorized users; material updates are recorded.

## Acceptance criteria
- A generated finding summary includes what happened, what is known, what is uncertain, and source references.
- Unsupported fields are left unknown or explicitly marked unverified.
- Prompted or malformed source text cannot instruct the model to disclose customer context or change system behavior (treat source content as untrusted input).
- A user correction is reflected in the record with provenance.

## Dependencies
CAN-REQ-005.

## Open decisions
- Model/provider, prompt and evaluation approach, human review gates, and handling of model/provider data retention.
