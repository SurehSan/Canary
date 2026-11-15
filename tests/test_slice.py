"""Vertical slice: sources -> finding w/ citations -> analysis -> priority -> alert -> dashboard.

CAN-REQ-003, 004, 005, 006, 007, 008, 013, 014. Demo scenario: PHP2Shell (CVE-2026-109618, CVE-2026-109619).
"""
import json

from tests.conftest import login, org_id, refresh

FERNWOOD = "Fernwood Labs"
PRAIRIE = "Prairie Valley Medical Center"
PHP_NET = "https://www.php.net/archive/2026.php#2026-10-21-5"
THN = "https://thehackernews.com/2026/10/php-issues-emergency-patches-for-two.html"
GHSA_1 = "https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w"
GHSA_2 = "https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp"
CHECK_POINT = ("https://blog.checkpoint.com/security/"
               "security-advisory-active-exploitation-of-php2shell-and-local-privilege-escalation/")
TITLE = "PHP2Shell: unauthenticated remote code execution in PHP (CVE-2026-109618, CVE-2026-109619)"


def fern_alert(db):
    return db.execute("SELECT * FROM alerts WHERE org_id=?", (org_id(db, FERNWOOD),)).fetchall()


def relevance(db, alert):
    return db.execute("SELECT * FROM relevance WHERE org_id=? AND finding_id=?",
                      (alert["org_id"], alert["finding_id"])).fetchone()


def test_dashboard_starts_with_no_alerts(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    assert fern_alert(db) == []
    assert 'data-count="new-alerts">0<' in client.get("/").data.decode()


def test_refresh_collects_sources_with_url_dates_and_outcome(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    item = db.execute("SELECT * FROM source_items WHERE url=?", (PHP_NET,)).fetchone()
    assert item["published_at"] == "2026-10-21"
    assert item["retrieved_at"].startswith("2026-11-14")
    runs = {r["key"]: r for r in db.execute(
        "SELECT c.key, r.outcome, r.new_items FROM collection_runs r JOIN source_catalog c ON c.id=r.source_id")}
    assert (runs["php-net"]["outcome"], runs["php-net"]["new_items"]) == ("success", 1)
    assert (runs["ghsa"]["outcome"], runs["ghsa"]["new_items"]) == ("success", 2)
    assert (runs["thehackernews"]["outcome"], runs["thehackernews"]["new_items"]) == ("success", 1)
    assert runs["owasp-genai"]["outcome"] == "success_no_new"


def test_advisories_group_by_cve_and_news_is_a_proposed_grouping(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    findings = db.execute("SELECT * FROM findings").fetchall()
    assert len(findings) == 1 and findings[0]["title"] == TITLE
    items = {i["url"]: i for i in db.execute("SELECT * FROM source_items WHERE finding_id=?", (findings[0]["id"],))}
    assert set(items) == {PHP_NET, THN, GHSA_1, GHSA_2}
    assert items[PHP_NET]["group_status"] == "primary"
    assert items[GHSA_1]["group_status"] == "exact" and "CVE-2026-109618" in items[GHSA_1]["group_basis"]
    assert items[GHSA_2]["group_status"] == "exact" and "CVE-2026-109619" in items[GHSA_2]["group_basis"]
    assert items[THN]["group_status"] == "proposed"  # news matched by name only: needs a person to confirm


def test_recollection_is_idempotent(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    refresh(client)
    assert db.execute("SELECT COUNT(*) FROM source_items").fetchone()[0] == 4
    assert db.execute("SELECT COUNT(*) FROM findings").fetchone()[0] == 1
    assert len(fern_alert(db)) == 1
    last = db.execute("SELECT r.outcome FROM collection_runs r JOIN source_catalog c ON c.id=r.source_id "
                      "WHERE c.key='php-net' ORDER BY r.id DESC").fetchone()
    assert last["outcome"] == "success_no_new"


def test_fernwood_alert_is_confirmed_87_but_capped_at_p2(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    (alert,) = fern_alert(db)
    rel = relevance(db, alert)
    assert (rel["match_state"], rel["score"], rel["priority"]) == ("confirmed", 87, "P2")
    pts = {f["key"]: f["points"] for f in json.loads(rel["factors"])}
    assert (pts["severity"], pts["exploitation"], pts["inventory_match"], pts["asset_criticality"],
            pts["source_reliability"], pts["questionnaire_gap"]) == (25, 12, 20, 15, 10, 5)
    assert "gate not met" in rel["p1_gate_reason"]


def test_confirmed_exploitation_report_escalates_to_p1(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    client.post("/sources/followup")
    (alert,) = fern_alert(db)
    rel = relevance(db, alert)
    assert (rel["score"], rel["priority"]) == (95, "P1") and "gate met" in rel["p1_gate_reason"]
    assert alert["has_update"] == 1
    assert db.execute("SELECT COUNT(*) FROM source_items WHERE url=?", (CHECK_POINT,)).fetchone()[0] == 1
    page = client.get(f"/alerts/{alert['id']}").data.decode()
    assert "P1 Critical" in page and "Confirmed match · Score 95/100" in page


def test_alert_detail_separates_facts_unknowns_and_shows_why_not_p1(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    (alert,) = fern_alert(db)
    page = client.get(f"/alerts/{alert['id']}").data.decode()
    for text in ("Confirmed match · Score 87/100", "P2 High", "Source-supported", "Unknown", "Canary interpretation",
                 PHP_NET, GHSA_1, "2026-10-21", "AI-generated draft", "P1 requires", "gate not met",
                 "not evidence of exposure", "Conflicting or unverified", "8.3.30", "8.3.36"):
        assert text in page, text


def test_analysis_never_claims_compromise(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    client.post("/sources/followup")
    payload = db.execute("SELECT payload FROM analyses ORDER BY id DESC LIMIT 1").fetchone()["payload"].lower()
    for phrase in ("was compromised", "has been compromised", "is compromised", "exposure confirmed"):
        assert phrase not in payload


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
    login(client, "wyatt", org=fern)
    refresh(client)
    (alert,) = fern_alert(db)
    news = db.execute("SELECT id FROM source_items WHERE group_status='proposed'").fetchone()["id"]
    client.post(f"/alerts/{alert['id']}/grouping/{news}/undo")
    assert db.execute("SELECT COUNT(*) FROM findings").fetchone()[0] == 2
    assert db.execute("SELECT action FROM audit_events WHERE action='grouping.undone'").fetchone()


def test_undone_grouping_keeps_affected_versions_on_the_split_finding(client, db):
    """Found while building the PHP2Shell demo: the split-off finding lost its affected-version data."""
    fern = org_id(db, FERNWOOD)
    login(client, "wyatt", org=fern)
    refresh(client)
    (alert,) = fern_alert(db)
    news = db.execute("SELECT id FROM source_items WHERE group_status='proposed'").fetchone()["id"]
    client.post(f"/alerts/{alert['id']}/grouping/{news}/undo")
    split = db.execute("SELECT affected_products FROM findings WHERE id=(SELECT finding_id FROM source_items WHERE id=?)",
                       (news,)).fetchone()["affected_products"]
    assert "8.3.36" in split
    assert len(fern_alert(db)) == 2
