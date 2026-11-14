"""Deterministic relevance (match state) and triage priority — CAN-REQ-007.

Code decides match state and priority; model output only supplies the
classified inputs (impact class, exploitation status), which are shown with
their points so every number is explainable.
"""
from datetime import date

MATCH_LABELS = {
    "confirmed": "Confirmed match",
    "possible": "Possible match",
    "industry_only": "Industry-only relevance",
    "no_match": "No known match",
}

SEVERITY_POINTS = {
    "critical_cvss": (25, "Source-rated critical severity (CVSS 9.0+)"),
    "high_cvss": (20, "Source-rated high severity (CVSS 7.0-8.9)"),
    "code_execution_no_cvss": (16, "Technique can lead to code execution; no CVSS rating published"),
    "data_exposure": (14, "Technique can expose data; no CVSS rating published"),
    "medium_cvss": (12, "Source-rated medium severity (CVSS 4.0-6.9)"),
    "availability": (10, "Availability or reliability impact"),
    "informational": (4, "Informational; no direct impact described"),
    "unknown": (0, "Severity not established by sources"),
}

EXPLOITATION_POINTS = {
    "active_targeting_org": (25, "Human-confirmed exploitation affecting this organization"),
    "active_in_wild": (20, "Credible active exploitation reported in the wild"),
    "claimed_in_wild_unverified": (12, "In-the-wild exploitation claimed by a single secondary source"),
    "research_demonstrated": (8, "Demonstrated in research/proof of concept; no confirmed active exploitation tied to this organization"),
    "theoretical": (3, "Theoretical technique only"),
    "unknown": (0, "No exploitation evidence"),
}

MATCH_POINTS = {"confirmed": 20, "possible": 12, "industry_only": 5, "no_match": 0}
CRITICALITY_POINTS = {"Critical": 15, "High": 10, "Medium": 6, "Low": 3}
TIER_POINTS = {"A": 5, "B": 4, "C": 2}
GAP_POINTS = {"No": 5, "Partial": 3, "Unknown": 3, "Yes": 0, "Not applicable": 0, None: 2}


def band(score):
    if score >= 80:
        return "P1"
    if score >= 60:
        return "P2"
    if score >= 35:
        return "P3"
    return "P4"


PRIORITY_LABELS = {"P1": "P1 Critical", "P2": "P2 High", "P3": "P3 Medium", "P4": "P4 Informational"}


def match_state(finding, inventory, org_industry):
    """Return {"state", "evidence"} for one organization's inventory.

    Confirmed needs an exact product match AND a known version listed as
    affected. Unknown versions can never produce Confirmed.
    """
    affected = {p["product_key"]: p.get("versions") for p in finding.get("affected_products", [])}
    tags = set(finding.get("technique_tags", []))
    evidence, states = [], []
    for item in inventory:
        key, version = item.get("product_key"), item.get("version")
        if key and key in affected:
            versions = affected[key]
            if version and versions and version in versions:
                states.append("confirmed")
                evidence.append(_ev(item, f"Exact product match; inventory version {version} is listed as affected"))
            elif version and versions:
                continue  # known version, not in affected list: not a match
            else:
                states.append("possible")
                why = "inventory version is Unknown" if not version else "source does not list affected versions"
                evidence.append(_ev(item, f"Product match, but {why}; cannot be confirmed"))
            continue
        overlap = tags.intersection(item.get("capabilities") or [])
        if overlap:
            states.append("possible")
            evidence.append(_ev(item, "Technology overlap: " + ", ".join(sorted(overlap))
                                + "; no product/version or installation evidence"))
    if "confirmed" in states:
        state = "confirmed"
    elif states:
        state = "possible"
    elif org_industry and org_industry in finding.get("industries", []):
        state = "industry_only"
        evidence.append({"item_id": None, "item_name": None, "criticality": None,
                         "reason": f"Industry context only ({org_industry}); no inventory match"})
    else:
        state = "no_match"
    return {"state": state, "evidence": evidence}


def _ev(item, reason):
    return {"item_id": item["id"], "item_name": item["name"],
            "criticality": item.get("criticality"), "reason": reason}


def _reliability(sources, as_of):
    if not sources:
        return 0, "No sources"
    best = max(TIER_POINTS.get(s["tier"], 0) for s in sources)
    n = len(sources)
    corroboration = 3 if n >= 3 else 2 if n == 2 else 0
    newest = max(date.fromisoformat(s["published_at"][:10]) for s in sources if s.get("published_at")) \
        if any(s.get("published_at") for s in sources) else None
    age = (as_of - newest).days if newest else None
    recency = 0 if age is None else 4 if age <= 30 else 3 if age <= 180 else 2 if age <= 365 else 0
    pts = min(10, best + corroboration + recency)
    age_txt = f"newest source {age} days old" if age is not None else "no publication date"
    return pts, f"Best source tier {best}/5, {n} source(s) +{corroboration}, {age_txt} +{recency}"


def score_priority(*, impact_class, exploitation_status, match_state, criticalities, sources,
                   as_of, questionnaire_answer, duplicate_without_new_info):
    sev, sev_why = SEVERITY_POINTS[impact_class]
    exp, exp_why = EXPLOITATION_POINTS[exploitation_status]
    mat = MATCH_POINTS[match_state]
    crit_vals = [c for c in criticalities if c in CRITICALITY_POINTS]
    top_crit = max(crit_vals, key=CRITICALITY_POINTS.get) if crit_vals else None
    crit = CRITICALITY_POINTS.get(top_crit, 0)
    rel, rel_why = _reliability(sources, as_of)
    gap = GAP_POINTS.get(questionnaire_answer, 2)
    dup = -10 if duplicate_without_new_info else 0

    factors = [
        {"key": "severity", "label": "Severity", "points": sev, "max": 25, "reason": sev_why},
        {"key": "exploitation", "label": "Exploitation evidence", "points": exp, "max": 25, "reason": exp_why},
        {"key": "inventory_match", "label": "Inventory match", "points": mat, "max": 20,
         "reason": MATCH_LABELS[match_state]},
        {"key": "asset_criticality", "label": "Asset criticality", "points": crit, "max": 15,
         "reason": f"Most critical matched asset: {top_crit}" if top_crit else "No matched asset with known criticality"},
        {"key": "source_reliability", "label": "Source reliability/recency", "points": rel, "max": 10, "reason": rel_why},
        {"key": "questionnaire_gap", "label": "Questionnaire gap", "points": gap, "max": 5,
         "reason": f"Related control answered: {questionnaire_answer or 'not answered'}"},
        {"key": "duplicate_penalty", "label": "Duplicate penalty", "points": dup, "max": 0,
         "reason": "Confirmed duplicate with no new information" if dup else "Not a repeat of a prior finding"},
    ]
    score = max(0, min(100, sum(f["points"] for f in factors)))
    p1_gate = (exploitation_status in ("active_in_wild", "active_targeting_org")
               and match_state == "confirmed" and top_crit == "Critical")
    priority = band(score)
    gate_reason = ("P1 requires credible active exploitation and a Confirmed match to a Critical asset; "
                   + ("gate met." if p1_gate else "gate not met, so this finding cannot be P1."))
    if priority == "P1" and not p1_gate:
        priority = "P2"
    return {"factors": factors, "score": score, "priority": priority,
            "p1_gate_met": p1_gate, "p1_gate_reason": gate_reason}
