"""Per-organization analysis, relevance, priority, and alert creation — CAN-REQ-006/007/008."""
import json

from .analysis import build_demo_analysis
from .db import audit, now_iso, today
from .scoring import match_state, score_priority


def orgs_for_finding(conn, finding_id):
    rows = conn.execute(
        "SELECT DISTINCT os.org_id FROM org_sources os JOIN source_items si ON si.source_id = os.source_id"
        " WHERE os.enabled = 1 AND si.finding_id = ?"
        " UNION SELECT org_id FROM relevance WHERE finding_id = ?", (finding_id, finding_id))
    return [r[0] for r in rows]


def latest_answer(conn, org_id, technique):
    if not technique:
        return None
    row = conn.execute(
        "SELECT a.answer FROM answers a JOIN assessments s ON s.id = a.assessment_id"
        " JOIN questions q ON q.key = a.question_key"
        " WHERE s.org_id = ? AND q.technique = ? ORDER BY s.created_at DESC, s.id DESC LIMIT 1",
        (org_id, technique)).fetchone()
    return row["answer"] if row else None


def inventory_for(conn, org_id):
    return [dict(r, capabilities=json.loads(r["capabilities"])) for r in
            conn.execute("SELECT * FROM inventory_items WHERE org_id=?", (org_id,))]


def process_findings(conn, finding_ids, actor_label="System pipeline"):
    for fid in sorted(finding_ids):
        for org_id in orgs_for_finding(conn, fid):
            assess_for_org(conn, fid, org_id, actor_label)


def assess_for_org(conn, finding_id, org_id, actor_label="System pipeline"):
    finding = dict(conn.execute("SELECT * FROM findings WHERE id=?", (finding_id,)).fetchone())
    for key in ("affected_products", "technique_tags", "industries"):
        finding[key] = json.loads(finding[key])
    org = conn.execute("SELECT * FROM organizations WHERE id=?", (org_id,)).fetchone()
    items = [dict(r) for r in conn.execute("SELECT * FROM source_items WHERE finding_id=? ORDER BY id", (finding_id,))]
    inventory = inventory_for(conn, org_id)

    match = match_state(finding, inventory, org["industry"])
    analysis = build_demo_analysis(finding, items, match)
    matched_ids = {e["item_id"] for e in match["evidence"]}
    result = score_priority(
        impact_class=analysis["impact_class"],
        exploitation_status=analysis["exploitation_status"],
        match_state=match["state"],
        criticalities=[i["criticality"] for i in inventory if i["id"] in matched_ids],
        sources=[{"tier": i["tier"], "published_at": i["published_at"]} for i in items],
        as_of=today(),
        questionnaire_answer=latest_answer(conn, org_id, finding["technique"]),
        duplicate_without_new_info=False,
    )
    ts = now_iso()
    conn.execute("INSERT INTO analyses (org_id, finding_id, finding_version, provider, payload, created_at)"
                 " VALUES (?,?,?,?,?,?)",
                 (org_id, finding_id, finding["version"], analysis["provider"], json.dumps(analysis), ts))
    prev = conn.execute("SELECT * FROM relevance WHERE org_id=? AND finding_id=?", (org_id, finding_id)).fetchone()
    values = (match["state"], json.dumps(match["evidence"]), result["score"], result["priority"],
              json.dumps(result["factors"]), result["p1_gate_reason"], ts)
    if prev:
        conn.execute("UPDATE relevance SET match_state=?, match_evidence=?, score=?, priority=?, factors=?,"
                     " p1_gate_reason=?, as_of=? WHERE id=?", values + (prev["id"],))
    else:
        conn.execute("INSERT INTO relevance (match_state, match_evidence, score, priority, factors, p1_gate_reason,"
                     " as_of, org_id, finding_id) VALUES (?,?,?,?,?,?,?,?,?)", values + (org_id, finding_id))

    alert = conn.execute("SELECT * FROM alerts WHERE org_id=? AND finding_id=?", (org_id, finding_id)).fetchone()
    if alert is None and match["state"] != "no_match":
        alert_id = conn.execute("INSERT INTO alerts (org_id, finding_id, created_at, updated_at) VALUES (?,?,?,?)",
                                (org_id, finding_id, ts, ts)).lastrowid
        audit(conn, org_id=org_id, actor_id=None, actor_label=actor_label, action="alert.created",
              target_type="alert", target_id=alert_id,
              summary=f"{result['priority']} alert ({match['state'].replace('_', ' ')}, {result['score']}/100)")
    elif alert is not None and prev is not None:
        before = {"priority": prev["priority"], "score": prev["score"], "match_state": prev["match_state"]}
        after = {"priority": result["priority"], "score": result["score"], "match_state": match["state"]}
        if before != after or finding["version"] > _analysed_version(conn, org_id, finding_id):
            conn.execute("UPDATE alerts SET has_update=1, updated_at=? WHERE id=?", (ts, alert["id"]))
            audit(conn, org_id=org_id, actor_id=None, actor_label=actor_label, action="alert.evidence_updated",
                  target_type="alert", target_id=alert["id"], summary="New evidence or reassessment", before=before,
                  after=after)


def _analysed_version(conn, org_id, finding_id):
    row = conn.execute("SELECT finding_version FROM analyses WHERE org_id=? AND finding_id=? ORDER BY id DESC"
                       " LIMIT 1 OFFSET 1", (org_id, finding_id)).fetchone()
    return row["finding_version"] if row else 0
