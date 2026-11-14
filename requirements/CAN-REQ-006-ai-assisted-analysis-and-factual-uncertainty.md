# CAN-REQ-006: AI-Assisted Analysis and Factual Uncertainty

**Status:** Proposed · **Priority:** Local demo prototype · **Source:** Project Plan §§6, 7, 11

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

## Prototype design decisions
- Use OpenAI API as the preferred optional analysis provider, as noted. Read the API key only from a local environment secret; never commit, display, or log it. If no key is configured, use deterministic demo analysis for seeded findings and label it clearly. The prototype must remain demonstrable without network/API access.
- Send only source-derived finding fields and the minimum organization context needed for relevance; exclude credentials and sensitive vendor data. Treat retrieved text as untrusted, constrain output to a schema, validate citations against supplied source references, and leave unsupported values unknown.
- Present generated analysis as a draft for human review. Authorized users can correct it, with prior value, editor, timestamp, and reason recorded. Prototype analysis should be manually checked against the demo case; it is not a validated security classifier.
- Disclose that API calls are subject to the configured provider's terms and retention settings. No regulated or sensitive customer data may be entered in this local demo.
