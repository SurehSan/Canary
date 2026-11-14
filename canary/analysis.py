"""Finding analysis — CAN-REQ-006.

The prototype ships a deterministic demo analysis so it works without an API
key or network. Source text is treated as untrusted data: it is never
interpreted as instructions, and only curated, citation-checked claims are
emitted. Code (scoring.py), not the analysis, decides match state and
priority; the analysis supplies classified inputs and never asserts exposure.
"""

REQUIRED_SECTIONS = ("what_happened", "source_supported", "org_context", "unknowns",
                     "interpretation", "conflicts")

THN_URL = "https://thehackernews.com/2026/07/new-hallusquatting-attack-could-trick.html"
CSA_URL = ("https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/04/"
           "CSA_research_note_slopsquatting-ai-supply-chain_20260419-csa-styled-1.pdf")
XYGENI_URL = "https://xygeni.io/blog/slopsquatting-evolution/"

# Curated, manually checked claims for the seeded technique, keyed by source URL.
CURATED = {
    "package-hallucination-squatting": {
        "title": "HalluSquatting: hallucinated package names used to hijack AI coding agents",
        "event_type": "AI supply-chain attack technique",
        "impact_class": "code_execution_no_cvss",
        "exploitation_status": "research_demonstrated",
        "exploitation_reason": ("Technique demonstrated by researchers with harmless payloads; THN reports no "
                                "in-the-wild HalluSquatting exploitation. Nothing ties a malicious package to this organization."),
        "what_happened": "Researchers showed AI coding assistants can be led to fetch and run attacker-registered "
                         "code under names that models commonly hallucinate.",
        "claims": [
            (CSA_URL, "Language models can produce package names that do not exist."),
            (CSA_URL, "Attackers can pre-register those hallucinated names on public registries such as npm and PyPI."),
            (THN_URL, "An AI coding agent that fetches an attacker-registered resource may run the attacker's code."),
            (THN_URL, "No CVE applies; the weakness is in how agents trust names."),
            (XYGENI_URL, "Earlier hallucinated npm package names continued to receive install attempts from agents in 2026."),
        ],
        "conflicts": [
            {"topic": "In-the-wild exploitation",
             "statement": "The CSA research note asserts real-world malicious slopsquatting packages with many downloads, "
                          "while The Hacker News reports no in-the-wild exploitation of HalluSquatting specifically. "
                          "The CSA note is self-labeled unofficial AI-assisted research. Treated as unverified.",
             "sources": [CSA_URL, THN_URL]},
        ],
        "unknowns": [
            "No specific malicious package is tied to this organization.",
            "Whether any malicious package was installed has not been established.",
            "Affected product versions: not specified by sources (technique-level finding).",
        ],
        "interpretation": [
            "Automatic dependency installation by AI agents is a relevant risk factor for investigation.",
            "This is a triage recommendation, not evidence of exposure or compromise.",
        ],
        "industries": [],
        "technique_tags": ["auto_install_packages", "agent_runtime"],
        "owasp": "LLM03:2025 Supply Chain",
    },
}


class AnalysisError(ValueError):
    pass


def build_demo_analysis(finding, source_items, match):
    """Return a schema-valid analysis using only the supplied source items."""
    by_url = {s["url"]: s["id"] for s in source_items}
    ids = set(by_url.values())
    spec = CURATED.get(finding.get("technique"))
    org_context = [f"{e['item_name']}: {e['reason']}" for e in match.get("evidence", []) if e.get("item_name")] \
        or ["No inventory item matched this finding."]
    if spec:
        claims = [{"text": text, "citations": [by_url[url]]} for url, text in spec["claims"] if url in by_url]
        conflicts = [{"topic": c["topic"], "statement": c["statement"],
                      "citations": [by_url[u] for u in c["sources"] if u in by_url]}
                     for c in spec["conflicts"] if all(u in by_url for u in c["sources"])]
        analysis = {
            "what_happened": [spec["what_happened"]],
            "source_supported": claims,
            "org_context": org_context,
            "unknowns": list(spec["unknowns"]),
            "interpretation": list(spec["interpretation"]),
            "conflicts": conflicts,
            "event_type": spec["event_type"],
            "impact_class": spec["impact_class"],
            "exploitation_status": spec["exploitation_status"],
            "exploitation_reason": spec["exploitation_reason"],
            "owasp": spec["owasp"],
        }
    else:
        # Untrusted text is only cited by reference; it is not summarized or obeyed.
        first = source_items[0]
        analysis = {
            "what_happened": ["A source published an item that has not been analyzed; open the source to review it."],
            "source_supported": [{"text": "Source published this item (title shown as data only).",
                                  "citations": [first["id"]]}],
            "org_context": org_context,
            "unknowns": ["Event type, affected products/versions, severity, and exploitation are unverified."],
            "interpretation": ["Insufficient evidence for interpretation; human review required."],
            "conflicts": [],
            "event_type": "Unknown",
            "impact_class": "unknown",
            "exploitation_status": "unknown",
            "exploitation_reason": "No exploitation evidence analyzed.",
            "owasp": None,
        }
    analysis.update(provider="demo", label="Demo analysis (deterministic) — AI-generated draft for human review")
    validate_analysis(analysis, ids)
    return analysis


def validate_analysis(analysis, source_ids):
    for section in REQUIRED_SECTIONS:
        if section not in analysis:
            raise AnalysisError(f"missing section: {section}")
    for claim in analysis["source_supported"]:
        cites = claim.get("citations") or []
        if not cites or not set(cites) <= set(source_ids):
            raise AnalysisError(f"claim cites unknown or no source: {claim.get('text')!r}")
    return analysis
