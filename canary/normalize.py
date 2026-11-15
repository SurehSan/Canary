"""Finding identity and duplicate detection — CAN-REQ-005.

Order of evidence: exact advisory identifier, then canonical URL. A shared
technique alias (curated taxonomy) only *proposes* a grouping for human
review; it is never sole proof.
"""
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "fbclid", "gclid"}
ID_PATTERN = re.compile(r"\b(CVE-\d{4}-\d{4,}|GHSA(?:-[0-9a-z]{4}){3})\b", re.IGNORECASE)

# Curated technique taxonomy: aliases that name the same attack technique.
TECHNIQUES = {
    "package-hallucination-squatting": {
        "label": "Package/name hallucination squatting",
        "aliases": ["hallusquatting", "slopsquatting", "package hallucination", "hallucinated package"],
    },
    "php2shell": {
        "label": "PHP2Shell (PHP remote code execution)",
        "aliases": ["php2shell", "cve-2026-109618", "cve-2026-109619"],
    },
}


def canonical_url(url):
    parts = urlsplit(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if k.lower() not in TRACKING_PARAMS])
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ""))


def extract_identifiers(text):
    seen = []
    for match in ID_PATTERN.findall(text or ""):
        ident = match.upper()
        if ident not in seen:
            seen.append(ident)
    return seen


def detect_technique(title, excerpt):
    text = f"{title} {excerpt}".lower()
    for key, spec in TECHNIQUES.items():
        if any(alias in text for alias in spec["aliases"]):
            return key
    return None


def classify_duplicate(item, existing):
    """Return {"finding_id", "status": "exact"|"proposed", "basis"} or None."""
    for f in existing:
        shared = [i for i in item.get("identifiers", []) if i in f.get("identifiers", [])]
        if shared:
            return {"finding_id": f["finding_id"], "status": "exact",
                    "basis": f"Same advisory identifier {shared[0]}"}
    for f in existing:
        if item.get("canonical_url") in f.get("canonical_urls", []):
            return {"finding_id": f["finding_id"], "status": "exact", "basis": "Same canonical URL"}
    for f in existing:
        tech = item.get("technique")
        if tech and tech == f.get("technique"):
            label = TECHNIQUES[tech]["label"]
            return {"finding_id": f["finding_id"], "status": "proposed",
                    "basis": f"Shared technique ({label}) from curated alias list; proposed grouping awaiting human review"}
    return None
