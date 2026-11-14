"""Seeded demo data: source catalog, offline source records, organizations.

Source records below point at REAL public articles. Titles, URLs, and dates
are preserved exactly; excerpts are short paraphrases written for this demo,
not copies of the articles. Everything about Fernwood Labs and Prairie Valley
Medical Center is fictional.
"""

# CAN-REQ-003: fixed starter catalog (global). Tier: A primary/standards,
# B reputable press or secondary research, C vendor blog.
SOURCE_CATALOG = [
    {"key": "thehackernews", "name": "The Hacker News", "type": "RSS",
     "url": "https://feeds.feedburner.com/TheHackersNews", "tier": "B",
     "topics": "Security news, AI threats", "method": "Public RSS feed"},
    {"key": "csa", "name": "CSA research notes", "type": "Public web",
     "url": "https://labs.cloudsecurityalliance.org/", "tier": "B",
     "topics": "AI safety and cloud security research", "method": "Public research index"},
    {"key": "ghsa", "name": "GitHub Security Advisories", "type": "API",
     "url": "https://api.github.com/advisories", "tier": "A",
     "topics": "Package advisories (npm, PyPI)", "method": "Documented public REST API (unauthenticated, rate-limited)"},
    {"key": "owasp-genai", "name": "OWASP GenAI Security Project", "type": "Public web",
     "url": "https://genai.owasp.org/", "tier": "A",
     "topics": "OWASP Top 10 for LLM Applications", "method": "Public project pages"},
]

# Offline fixture records returned by the demo collector (no network needed).
SOURCE_ITEMS = [
    {"source_key": "thehackernews",
     "url": "https://thehackernews.com/2026/07/new-hallusquatting-attack-could-trick.html",
     "title": "New HalluSquatting Attack Could Trick AI Coding Assistants Into Installing Botnet Malware",
     "published_at": "2026-07-08",
     "excerpt": "Researchers describe chaining model hallucination of resource names with indirect "
                "prompt injection so AI coding assistants fetch and run attacker-registered code. "
                "No in-the-wild exploitation is reported; no CVE applies.",
     "source_note": None},
    {"source_key": "csa",
     "url": "https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/04/CSA_research_note_slopsquatting-ai-supply-chain_20260419-csa-styled-1.pdf",
     "title": "Slopsquatting: AI Code Hallucinations Fuel Supply Chain Attacks",
     "published_at": "2026-04-19",
     "excerpt": "Research note on attackers pre-registering package names that LLMs fabricate "
                "(npm, PyPI) and on AI agents resolving such packages autonomously.",
     "source_note": "Self-labeled “Unofficial AI-assisted Research”; not an official CSA-reviewed publication."},
]

# Follow-up evidence introduced later in the walkthrough (CAN-REQ-005 update).
FOLLOWUP_ITEMS = [
    {"source_key": "followup",
     "url": "https://xygeni.io/blog/slopsquatting-evolution/",
     "title": "Slopsquatting Evolution: From AI Curiosity to Agent RCE",
     "published_at": "2026-09-18",
     "excerpt": "Vendor blog timeline of slopsquatting from 2023 experiments to 2026 agent "
                "remote-code-execution research. Page shows an updated date only.",
     "source_note": "Vendor blog (promotes its own product). Date shown is the page's updated date."},
]
