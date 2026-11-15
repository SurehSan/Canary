"""Finding analysis — CAN-REQ-006.

The prototype ships a deterministic demo analysis so it works without an API
key or network. Source text is treated as untrusted data: it is never
interpreted as instructions, and only curated, citation-checked claims are
emitted. Code (scoring.py), not the analysis, decides match state and
priority; the analysis supplies classified inputs and never asserts exposure.
"""

REQUIRED_SECTIONS = ("what_happened", "source_supported", "org_context", "unknowns",
                     "interpretation", "conflicts")

from .fixtures import CHECK_POINT_URL, GHSA_OOM_URL, GHSA_STATE_URL, PHP_NET_URL, THN_URL

PHP_AFFECTED = [">=5.4.0,<8.2.0", ">=8.2.0,<8.2.35", ">=8.3.0,<8.3.36", ">=8.4.0,<8.4.27", ">=8.5.0,<8.5.12"]

# Curated, manually checked claims for the seeded finding, keyed by source URL (checked 2026-11-14).
CURATED = {
    "php2shell": {
        "title": "PHP2Shell: unauthenticated remote code execution in PHP (CVE-2026-109618, CVE-2026-109619)",
        "event_type": "Software vulnerability (unauthenticated remote code execution)",
        "impact_class": "critical_cvss",
        "affected_products": [{"product_key": "php", "versions": PHP_AFFECTED}],
        # First matching rule wins: exploitation status depends on which sources have been collected.
        "exploitation": [
            {"if_any": [CHECK_POINT_URL], "status": "active_in_wild",
             "reason": "Check Point reports confirmed in-the-wild exploitation of PHP2Shell between October 30 and "
                       "November 4, 2026. Nothing ties an attack to this organization."},
            {"if_any": [THN_URL], "status": "claimed_in_wild_unverified",
             "reason": "News coverage reports exploitation attempts attributed to third parties (Cloudflare, "
                       "watchTowr); no primary source has confirmed exploitation yet. Nothing ties an attack to "
                       "this organization."},
        ],
        "exploitation_default": ("unknown", "The collected advisories do not report exploitation."),
        "what_happened": "The PHP project fixed two critical memory-safety flaws that let an unauthenticated "
                         "attacker run code on servers running PHP 5.4 through 8.5.",
        "claims": [
            (PHP_NET_URL, "PHP 8.5.12, 8.4.27, 8.3.36 and 8.2.35 fix two critical vulnerabilities (CVE-2026-109618, "
                          "CVE-2026-109619) that can allow unauthenticated remote code execution."),
            (PHP_NET_URL, "The PHP project says there are no complete mitigations; updating is the only safe choice."),
            (PHP_NET_URL, "PHP 8.1 and older no longer receive updates from the PHP project."),
            (GHSA_OOM_URL, "CVE-2026-109618: out-of-memory handling can interrupt PHP while request data is only "
                           "partially initialized, and cleanup may then treat the invalid data as valid."),
            (GHSA_STATE_URL, "CVE-2026-109619: request-owned internal state can survive after its memory is freed and "
                             "be used by a later request on the same worker."),
            (CHECK_POINT_URL, "Check Point reports active in-the-wild exploitation between October 30 and November 4, "
                              "2026, used for initial access to internet-facing gateways."),
            (CHECK_POINT_URL, "Check Point says a couple of dozen unpatched systems, in a single region, were "
                              "compromised in the incidents it observed."),
        ],
        "conflicts": [
            {"topic": "Exploitation in the wild", "sources": [THN_URL], "unless_any": [CHECK_POINT_URL],
             "statement": "The Hacker News reports exploitation attempts attributed to Cloudflare and watchTowr, but "
                          "no break-in of a specific server had been confirmed and the PHP advisories do not mention "
                          "exploitation. Treated as unverified until a primary source confirms it."},
        ],
        "unknowns": [
            "Whether this organization's systems were targeted or compromised has not been established.",
            "Whether the portal's PHP build includes a vendor backport of the fix has not been checked.",
        ],
        "interpretation": [
            "An internet-facing service on a PHP version inside the affected range should be treated as urgent "
            "patch work.",
            "This is a triage recommendation, not evidence of exposure or compromise.",
        ],
        "industries": [],
        "technique_tags": [],
        "framework": "CIS Controls v8, Safeguard 7.4 (application patch management)",
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
                     for c in spec["conflicts"]
                     if all(u in by_url for u in c["sources"]) and not any(u in by_url for u in c.get("unless_any", []))]
        status, reason = spec.get("exploitation_default", ("unknown", "No exploitation evidence analyzed."))
        for rule in spec.get("exploitation", []):
            if any(u in by_url for u in rule["if_any"]):
                status, reason = rule["status"], rule["reason"]
                break
        analysis = {
            "what_happened": [spec["what_happened"]],
            "source_supported": claims,
            "org_context": org_context,
            "unknowns": list(spec["unknowns"]),
            "interpretation": list(spec["interpretation"]),
            "conflicts": conflicts,
            "event_type": spec["event_type"],
            "impact_class": spec["impact_class"],
            "exploitation_status": status,
            "exploitation_reason": reason,
            "framework": spec.get("framework"),
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
            "framework": None,
        }
    analysis.update(provider="demo", label="Demo analysis (deterministic) — AI-generated draft for human review")
    validate_analysis(analysis, ids)
    return analysis


CORRECTABLE_SECTIONS = {"what_happened": "What happened", "source_supported": "Source-supported",
                        "org_context": "Organization context", "unknowns": "Unknown",
                        "interpretation": "Canary interpretation"}


def section_texts(analysis, section):
    return [c["text"] if isinstance(c, dict) else c for c in analysis.get(section, [])]


def apply_corrections(analysis, corrections):
    """Overlay human corrections (oldest first) on a generated analysis without mutating it.

    A correction applies where the current text equals its prior value, so a correction made against an
    earlier analysis version stops applying once that text no longer appears (it stays in history).
    Returns a copy with a "corrected" map {(section, new_text): correction}.
    """
    out = {k: (list(v) if isinstance(v, list) else v) for k, v in analysis.items()}
    out["corrected"] = {}
    for corr in corrections:
        section = corr["section"]
        entries = out.get(section, [])
        for i, entry in enumerate(entries):
            text = entry["text"] if isinstance(entry, dict) else entry
            if text == corr["prior_value"]:
                entries[i] = dict(entry, text=corr["new_value"]) if isinstance(entry, dict) else corr["new_value"]
                out["corrected"][(section, corr["new_value"])] = corr
        out[section] = entries
    return out


def corrections_for(db, org_id, finding_id):
    return [dict(r) for r in db.execute(
        "SELECT c.*, u.display_name AS editor FROM analysis_corrections c LEFT JOIN users u ON u.id=c.editor_id"
        " WHERE c.org_id=? AND c.finding_id=? ORDER BY c.id", (org_id, finding_id))]


def validate_analysis(analysis, source_ids):
    for section in REQUIRED_SECTIONS:
        if section not in analysis:
            raise AnalysisError(f"missing section: {section}")
    for claim in analysis["source_supported"]:
        cites = claim.get("citations") or []
        if not cites or not set(cites) <= set(source_ids):
            raise AnalysisError(f"claim cites unknown or no source: {claim.get('text')!r}")
    return analysis
