# AI and knowledge requirements

## Knowledge pipeline

AIK-001. Canary shall ingest only configured sources, including incident reports, vendor advisories, government guidance, standards, and approved internal documents.

AIK-002. Ingestion shall preserve the original content, source URL or document identifier, author, publication date, retrieval date, jurisdiction, and access permissions.

AIK-003. The pipeline shall extract claims, affected technologies, threat techniques, data types, controls, indicators, and recommended mitigations. Each extracted item shall link back to an exact source passage or document location.

AIK-004. The system shall detect duplicates, conflicting claims, stale content, and unsupported extraction. Conflicts shall be surfaced for analyst review rather than silently resolved.

## Retrieval and generation

AIK-010. Retrieval shall be tenant-aware and shall never return content a user is not authorized to see.

AIK-011. Generated summaries, relevance explanations, questions, and recommendations shall be grounded in retrieved evidence. The response shall distinguish source facts, reasonable inferences, and unknowns.

AIK-012. Every material recommendation shall cite its source, source date, confidence, applicability assumptions, and suggested verification evidence.

AIK-013. If evidence is insufficient or conflicting, the AI shall say so and request human review. It shall not invent incident details, controls, legal obligations, or certainty.

AIK-014. The AI shall not provide exploit instructions, credentials, patient data, or unnecessary sensitive incident details. It shall redact or summarize sensitive material according to sharing restrictions.

AIK-015. Prompt-injection defenses shall treat retrieved documents and user uploads as untrusted data, keep system instructions separate, and prevent content from changing permissions or executing tools without explicit authorization.

## Safety and evaluation

AIK-020. Analysts shall be able to inspect retrieved passages and the reasoning factors behind a notification or plan item.

AIK-021. The product shall log model version, prompt or policy version, retrieval set, output, reviewer decision, and timestamp for each consequential AI result.

AIK-022. Before release, evaluations shall measure citation correctness, unsupported-claim rate, relevance precision, false-negative rate for critical notifications, sensitive-data leakage, and consistency across equivalent profiles.

AIK-023. Model or source changes shall be versioned, rollbackable, and tested against a fixed regression set of incidents and organization profiles.
