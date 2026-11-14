"""Central source collection — CAN-REQ-003/004/005.

The prototype collects from an offline fixture adapter (labeled in the UI) so
the demo never depends on network access. Each enabled catalog source is
collected once per run; resulting findings are associated with organizations
whose settings enable a contributing source (pipeline.py).
"""
import json
import time

from flask import current_app

from .analysis import CURATED
from .db import audit, now_iso
from .fixtures import SOURCE_ITEMS
from .normalize import canonical_url, classify_duplicate, detect_technique, extract_identifiers

MAX_ATTEMPTS = 3
FIXTURE_ADAPTER = "Offline fixture adapter (demo)"


class SourceError(Exception):
    pass


def fetch_fixture(source):
    if source["simulate_failure"]:
        raise SourceError("Simulated outage (demo): HTTP 503 from source")
    return [i for i in SOURCE_ITEMS if i["source_key"] == source["key"]]


def run_collection(conn, trigger="manual", actor_label="System scheduler"):
    """Collect every source enabled by at least one organization. Returns touched finding ids."""
    sources = conn.execute(
        "SELECT * FROM source_catalog WHERE id IN (SELECT source_id FROM org_sources WHERE enabled = 1) ORDER BY id"
    ).fetchall()
    touched = set()
    sleep = current_app.config.get("RETRY_SLEEP_SECONDS", 0.2)
    for src in sources:
        run_id = conn.execute(
            "INSERT INTO collection_runs (source_id, trigger, adapter, started_at) VALUES (?,?,?,?)",
            (src["id"], trigger, FIXTURE_ADAPTER, now_iso())).lastrowid
        attempts, items, error = 0, None, None
        while attempts < MAX_ATTEMPTS and items is None:
            attempts += 1
            try:
                items = fetch_fixture(src)
            except SourceError as exc:
                error = str(exc)
                if attempts < MAX_ATTEMPTS and sleep:
                    time.sleep(sleep * attempts)  # bounded backoff
        if items is None:
            conn.execute("UPDATE collection_runs SET finished_at=?, outcome='failed', attempts=?, error=? WHERE id=?",
                         (now_iso(), attempts, error, run_id))
            audit(conn, org_id=None, actor_id=None, actor_label=actor_label, action="collection.failed",
                  target_type="source", target_id=src["id"],
                  summary=f"{src['name']}: failed after {attempts} attempts")
            continue
        new = 0
        for raw in items:
            finding_id = ingest_item(conn, raw, src, run_id)
            if finding_id:
                new += 1
                touched.add(finding_id)
        conn.execute("UPDATE collection_runs SET finished_at=?, outcome=?, attempts=?, new_items=? WHERE id=?",
                     (now_iso(), "success" if new else "success_no_new", attempts, new, run_id))
    return touched


def existing_findings(conn):
    out = []
    for f in conn.execute("SELECT id, technique, identifiers FROM findings"):
        urls = [r["canonical_url"] for r in conn.execute(
            "SELECT canonical_url FROM source_items WHERE finding_id=?", (f["id"],))]
        out.append({"finding_id": f["id"], "identifiers": json.loads(f["identifiers"]),
                    "canonical_urls": urls, "technique": f["technique"]})
    return out


def ingest_item(conn, raw, src, run_id, source_label=None, tier=None):
    """Store a source item and attach it to a finding. Returns finding id, or None if already collected."""
    curl = canonical_url(raw["url"])
    if conn.execute("SELECT 1 FROM source_items WHERE canonical_url=?", (curl,)).fetchone():
        return None  # idempotent re-collection: no uncontrolled copies
    ids = extract_identifiers(f"{raw['title']} {raw.get('excerpt', '')}")
    technique = detect_technique(raw["title"], raw.get("excerpt", ""))
    match = classify_duplicate({"identifiers": ids, "canonical_url": curl, "technique": technique},
                               existing_findings(conn))
    ts = now_iso()
    if match:
        finding_id, status, basis = match["finding_id"], match["status"], match["basis"]
    else:
        spec = CURATED.get(technique, {})
        finding_id = conn.execute(
            "INSERT INTO findings (title, technique, event_type, technique_tags, industries, identifiers,"
            " first_seen_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (spec.get("title", raw["title"]), technique, spec.get("event_type"),
             json.dumps(spec.get("technique_tags", [])), json.dumps(spec.get("industries", [])),
             json.dumps(ids), ts, ts)).lastrowid
        status, basis = "primary", "First report of this finding"
    conn.execute(
        "INSERT INTO source_items (source_id, source_label, tier, url, canonical_url, title, published_at, retrieved_at,"
        " excerpt, source_note, identifiers, technique, finding_id, group_status, group_basis, collection_run_id)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (src["id"] if src else None, source_label or src["name"], tier or src["tier"], raw["url"], curl, raw["title"],
         raw.get("published_at"), ts, raw.get("excerpt"), raw.get("source_note"), json.dumps(ids), technique,
         finding_id, status, basis, run_id))
    if match:
        bump_revision(conn, finding_id, f"Source added: {source_label or src['name']} ({status} grouping)",
                      "System collector")
    else:
        snapshot_revision(conn, finding_id, 1, "Finding created", "System collector")
    return finding_id


def finding_snapshot(conn, finding_id):
    f = dict(conn.execute("SELECT * FROM findings WHERE id=?", (finding_id,)).fetchone())
    f["sources"] = [dict(r) for r in conn.execute(
        "SELECT id, source_label, url, published_at, group_status FROM source_items WHERE finding_id=? ORDER BY id",
        (finding_id,))]
    return f


def snapshot_revision(conn, finding_id, version, summary, actor_label):
    conn.execute("INSERT INTO finding_revisions (finding_id, version, change_summary, snapshot, actor_label, created_at)"
                 " VALUES (?,?,?,?,?,?)",
                 (finding_id, version, summary, json.dumps(finding_snapshot(conn, finding_id)), actor_label, now_iso()))


def bump_revision(conn, finding_id, summary, actor_label):
    conn.execute("UPDATE findings SET version = version + 1, updated_at=? WHERE id=?", (now_iso(), finding_id))
    version = conn.execute("SELECT version FROM findings WHERE id=?", (finding_id,)).fetchone()["version"]
    snapshot_revision(conn, finding_id, version, summary, actor_label)
