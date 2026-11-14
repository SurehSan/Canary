Problem: AI tools ship faster than teams can secure them. In February 2026, a crafted GitHub issue prompt-injected the AI issue-triage bot of the Cline coding assistant and led to an unauthorized npm release of its CLI ([Cline post-mortem](https://cline.bot/blog/post-mortem-unauthorized-cline-cli-npm), Feb 24, 2026). IBM's 2026 Cost of a Data Breach study found one in four malicious breaches were AI-enabled, a 56% increase over the previous year ([IBM newsroom](https://newsroom.ibm.com/2026-07-29-ibm-study-one-in-four-malicious-breaches-are-ai-enabled,-costing-companies-6-million-on-average), Jul 29, 2026). Small teams have no one whose job is to track this.

Solution: Canary is an AI-specific alert system and plan generator. It tracks new vulnerabilities and exploits, tells you which ones affect your project, and walks you through fixing them.

Curated intake: a trusted-source list set by your priorities, plus AI filtering and ranking.
Persistent context: remembers your stack, team, and past assessments, so alerts are specific to you.
Framework-anchored questionnaire: maps your gaps to a standard (NIST AI RMF / OWASP LLM Top 10), reweighted by current threats.
Guided report: prioritized mitigations with a short explanation of each risk, so the team learns as it fixes.

Sources checked 2026-11-14 (CAN-REQ-016). Both statements above come from primary sources. Do not use the widely repeated "shadow AI in 43% of breaches" figure: it appears only in secondary write-ups (which describe it as 43% of breached *organizations*), and IBM's public report page and press release do not state it. Also avoid "compromised 4,000 machines": that number is not in Cline's post-mortem.