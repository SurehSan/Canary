"""Vertical slice: sources -> finding w/ citations -> analysis -> priority -> alert -> dashboard.

CAN-REQ-003, 004, 005, 006, 007, 008, 013, 014.
"""
import json

from tests.conftest import login, org_id, refresh

FERNWOOD = "Fernwood Labs"
PRAIRIE = "Prairie Valley Medical Center"
THN = "https://thehackernews.com/2026/07/new-hallusquatting-attack-could-trick.html"


def fern_alert(db):
    return db.execute("SELECT * FROM alerts WHERE org_id=?", (org_id(db, FERNWOOD),)).fetchall()


def test_dashboard_starts_with_no_alerts(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    assert fern_alert(db) == []
    assert 'data-count="new-alerts">0<' in client.get("/").data.decode()


def test_refresh_collects_sources_with_url_dates_and_outcome(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    item = db.execute("SELECT * FROM source_items WHERE url=?", (THN,)).fetchone()
    assert item["published_at"] == "2026-07-08"
    assert item["retrieved_at"].startswith("2026-11-14")
    runs = {r["key"]: r for r in db.execute(
        "SELECT c.key, r.outcome, r.new_items FROM collection_runs r JOIN source_catalog c ON c.id=r.source_id")}
    assert runs["thehackernews"]["outcome"] == "success" and runs["thehackernews"]["new_items"] == 1
    assert runs["ghsa"]["outcome"] == "success_no_new"


def test_thn_and_csa_group_under_one_canonical_finding_with_both_citations(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    findings = db.execute("SELECT * FROM findings").fetchall()
    assert len(findings) == 1
    assert findings[0]["title"] == "HalluSquatting: hallucinated package names used to hijack AI coding agents"
    items = db.execute("SELECT group_status, published_at FROM source_items WHERE finding_id=? ORDER BY id",
                       (findings[0]["id"],)).fetchall()
    assert [(i["group_status"], i["published_at"]) for i in items] == [("primary", "2026-07-08"), ("proposed", "2026-04-19")]


def test_recollection_is_idempotent(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    refresh(client)
    assert db.execute("SELECT COUNT(*) FROM source_items").fetchone()[0] == 2
    assert db.execute("SELECT COUNT(*) FROM findings").fetchone()[0] == 1
    assert len(fern_alert(db)) == 1
    last = db.execute("SELECT r.outcome FROM collection_runs r JOIN source_catalog c ON c.id=r.source_id "
                      "WHERE c.key='thehackernews' ORDER BY r.id DESC").fetchone()
    assert last["outcome"] == "success_no_new"


def test_fernwood_alert_is_possible_65_p2_with_factors(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    (alert,) = fern_alert(db)
    rel = db.execute("SELECT * FROM relevance WHERE org_id=? AND finding_id=?",
                     (alert["org_id"], alert["finding_id"])).fetchone()
    assert (rel["match_state"], rel["score"], rel["priority"]) == ("possible", 65, "P2")
    pts = {f["key"]: f["points"] for f in json.loads(rel["factors"])}
    assert pts["severity"] == 16 and pts["questionnaire_gap"] == 5 and pts["asset_criticality"] == 15


def test_alert_detail_separates_facts_unknowns_and_shows_why_not_p1(client, db):
    login(client, "sureh", org=org_id(db, FERNWOOD))
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    (alert,) = fern_alert(db)
    page = client.get(f"/alerts/{alert['id']}").data.decode()
    for text in ("Possible match", "65/100", "P2 High", "Source-supported", "Unknown", "Canary interpretation",
                 THN, "2026-07-08", "2026-04-19", "Demo analysis", "P1 requires", "not evidence of exposure",
                 "Conflicting"):
        assert text in page, text
    assert "Possible match · Score 65/100" in page
    assert "Confirmed match ·" not in page and "<strong>Confirmed match.</strong>" not in page


def test_prairie_valley_gets_no_alert_for_unrelated_inventory(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    assert db.execute("SELECT COUNT(*) FROM alerts WHERE org_id=?", (org_id(db, PRAIRIE),)).fetchone()[0] == 0


def test_dashboard_counts_derive_from_records(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    page = client.get("/").data.decode()
    assert 'data-count="new-alerts">1<' in page
    assert 'data-count="high-priority">1<' in page


def test_simulated_outage_is_failure_not_empty_success(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    ghsa = db.execute("SELECT id FROM source_catalog WHERE key='ghsa'").fetchone()["id"]
    client.post(f"/sources/{ghsa}/simulate-failure")
    refresh(client)
    run = db.execute("SELECT * FROM collection_runs WHERE source_id=? ORDER BY id DESC", (ghsa,)).fetchone()
    assert run["outcome"] == "failed" and run["attempts"] == 3 and "Simulated" in run["error"]
    page = client.get("/").data.decode()
    assert "GitHub Security Advisories" in page and "Failed" in page


def test_disabled_source_is_not_collected(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    thn = db.execute("SELECT id FROM source_catalog WHERE key='thehackernews'").fetchone()["id"]
    client.post(f"/sources/{thn}/toggle")
    refresh(client)
    assert db.execute("SELECT COUNT(*) FROM collection_runs WHERE source_id=?", (thn,)).fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM source_items WHERE url=?", (THN,)).fetchone()[0] == 0


def test_lead_assigns_and_starts_investigation_with_audit(client, db):
    fern = org_id(db, FERNWOOD)
    login(client, "wyatt", org=fern)
    refresh(client)
    client.post("/logout")
    login(client, "sureh", org=fern)
    (alert,) = fern_alert(db)
    sureh = db.execute("SELECT id FROM users WHERE username='sureh'").fetchone()["id"]
    client.post(f"/alerts/{alert['id']}/assign", data={"assignee_id": sureh})
    client.post(f"/alerts/{alert['id']}/status", data={"status": "under_investigation"})
    (alert,) = fern_alert(db)
    assert alert["assignee_id"] == sureh and alert["status"] == "under_investigation"
    events = [(r["action"], r["actor_id"], r["created_at"]) for r in db.execute(
        "SELECT * FROM audit_events WHERE org_id=? AND target_type='alert' AND actor_id IS NOT NULL ORDER BY id",
        (fern,))]
    assert [e[0] for e in events] == ["alert.assigned", "alert.status_changed"]
    assert all(e[1] == sureh and e[2] for e in events)


def test_invalid_transition_is_rejected(client, db):
    fern = org_id(db, FERNWOOD)
    login(client, "wyatt", org=fern)
    refresh(client)
    (alert,) = fern_alert(db)
    resp = client.post(f"/alerts/{alert['id']}/status", data={"status": "resolved_verified"})
    assert resp.status_code == 400
    assert fern_alert(db)[0]["status"] == "new"


def test_proposed_grouping_can_be_confirmed_or_undone(client, db):
    fern = org_id(db, FERNWOOD)
    login(client, "sureh", org=fern)
    login(client, "wyatt", org=fern)
    refresh(client)
    (alert,) = fern_alert(db)
    csa = db.execute("SELECT id FROM source_items WHERE group_status='proposed'").fetchone()["id"]
    client.post(f"/alerts/{alert['id']}/grouping/{csa}/undo")
    assert db.execute("SELECT COUNT(*) FROM findings").fetchone()[0] == 2
    assert db.execute("SELECT action FROM audit_events WHERE action='grouping.undone'").fetchone()
