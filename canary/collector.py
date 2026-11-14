"""Central source collection — CAN-REQ-003/004/005.

The prototype collects from an offline fixture adapter (labeled in the UI) so
the demo never depends on network access. Each enabled catalog source is
collected once per run; resulting findings are associated with organizations
whose settings enable a contributing source (pipeline.py).
"""
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime

from flask import current_app

from . import live
from .analysis import CURATED
from .db import audit, now_iso
from .fixtures import SOURCE_ITEMS
from .normalize import canonical_url, classify_duplicate, detect_technique, extract_identifiers

MAX_ATTEMPTS = 3
FIXTURE_ADAPTER = "Offline fixture adapter (demo)"


class SourceError(Exception):
    pass


SIMULATED_OUTAGE = "Simulated outage (demo): HTTP 503 from source"


def fetch_fixture(source):
    return [i for i in SOURCE_ITEMS if i["source_key"] == source["key"]]


def fetch_live(source):
    getter = current_app.config.get("HTTP_GET") or live.http_get
    items = live.parse_rss(getter(live.LIVE_FEEDS[source["key"]]))
    return [dict(i, source_key=source["key"]) for i in items if live.is_ai_relevant(i["title"], i["excerpt"])]


def run_collection(conn, trigger="manual", actor_label="System scheduler"):
    """Collect every source enabled by at least one organization. Returns touched finding ids.

    A demo outage simulation is scoped to the organization that turned it on (CDX-1): that org gets a
    failed run of its own, while the shared fetch still runs for every other org that enabled the source.
    """
    sources = conn.execute(
        "SELECT * FROM source_catalog WHERE id IN (SELECT source_id FROM org_sources WHERE enabled = 1) ORDER BY id"
    ).fetchall()
    touched = set()
    for src in sources:
        orgs = conn.execute("SELECT org_id, simulate_failure FROM org_sources WHERE source_id=? AND enabled=1",
                            (src["id"],)).fetchall()
        if any(not o["simulate_failure"] for o in orgs):
            touched |= _run_adapter(conn, src, trigger, FIXTURE_ADAPTER, fetch_fixture, actor_label)
            if current_app.config.get("LIVE_SOURCES") and src["key"] in live.LIVE_FEEDS:
                touched |= _run_adapter(conn, src, trigger, live.LIVE_ADAPTER, fetch_live, actor_label)
        for o in orgs:
            if o["simulate_failure"]:
                _record_simulated_outage(conn, src, o["org_id"], trigger, actor_label)
    return touched


def _record_simulated_outage(conn, src, org_id, trigger, actor_label):
    ts = now_iso()
    conn.execute("INSERT INTO collection_runs (source_id, org_id, trigger, adapter, started_at, finished_at, outcome,"
                 " attempts, error) VALUES (?,?,?,?,?,?,'failed',?,?)",
                 (src["id"], org_id, trigger, FIXTURE_ADAPTER, ts, ts, MAX_ATTEMPTS, SIMULATED_OUTAGE))
    audit(conn, org_id=org_id, actor_id=None, actor_label=actor_label, action="collection.failed",
          target_type="source", target_id=src["id"],
          summary=f"{src['name']}: simulated outage (demo), failed after {MAX_ATTEMPTS} attempts")


def _live_too_soon(conn, src):
    last = conn.execute("SELECT started_at FROM collection_runs WHERE source_id=? AND adapter=? AND outcome!='skipped'"
                        " ORDER BY id DESC LIMIT 1", (src["id"], live.LIVE_ADAPTER)).fetchone()
    if last is None:
        return False
    elapsed = (datetime.fromisoformat(now_iso()) - datetime.fromisoformat(last["started_at"])).total_seconds()
    return elapsed < current_app.config.get("LIVE_MIN_INTERVAL_SECONDS", 900)


def _run_adapter(conn, src, trigger, adapter, fetch, actor_label):
    run_id = conn.execute("INSERT INTO collection_runs (source_id, trigger, adapter, started_at) VALUES (?,?,?,?)",
                          (src["id"], trigger, adapter, now_iso())).lastrowid
    if adapter == live.LIVE_ADAPTER and _live_too_soon(conn, src):
        conn.execute("UPDATE collection_runs SET finished_at=?, outcome='skipped', error=? WHERE id=?",
                     (now_iso(), "Skipped: minimum interval between live fetches not reached (rate-limit respect)",
                      run_id))
        return set()
    # Never hold the SQLite write lock across network I/O: other requests must stay writable (review focus 10).
    conn.commit()
    sleep = current_app.config.get("RETRY_SLEEP_SECONDS", 0.2)
    attempts, items, error = 0, None, None
    while attempts < MAX_ATTEMPTS and items is None:
        attempts += 1
        try:
            items = fetch(src)
        except (SourceError, OSError, ET.ParseError) as exc:
            error = f"{type(exc).__name__}: {str(exc)[:200]}" if not isinstance(exc, SourceError) else str(exc)
            if attempts < MAX_ATTEMPTS and sleep:
                time.sleep(sleep * attempts)  # bounded backoff
    if items is None:
        conn.execute("UPDATE collection_runs SET finished_at=?, outcome='failed', attempts=?, error=? WHERE id=?",
                     (now_iso(), attempts, error, run_id))
        audit(conn, org_id=None, actor_id=None, actor_label=actor_label, action="collection.failed",
              target_type="source", target_id=src["id"],
              summary=f"{src['name']} ({adapter}): failed after {attempts} attempts")
        return set()
    touched = set()
    for raw in items:
        finding_id = ingest_item(conn, raw, src, run_id)
        if finding_id:
            touched.add(finding_id)
    new = conn.execute("SELECT COUNT(*) FROM source_items WHERE collection_run_id=?", (run_id,)).fetchone()[0]
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
