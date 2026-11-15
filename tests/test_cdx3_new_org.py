"""CDX-3: an organization created after collection must be assessed against already-collected findings
(CAN-REQ-016: a new demo organization can complete the workflow through an approved plan)."""
from tests.conftest import login, org_id, refresh

FERNWOOD = "Fernwood Labs"
AGENT = {"name": "Storefront (PHP)", "category": "Web application", "product_key": "php", "version": "8.4.10",
         "version_status": "known", "criticality": "High", "capabilities": "php"}


def collect_as_fernwood(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    client.post("/logout")


def new_org(client, db, name="Juniper Robotics"):
    client.post("/register", data={"username": "dana", "display_name": "Dana", "password": "pass1234"})
    client.post("/orgs/create", data={"name": name, "industry": "Manufacturing"})
    return org_id(db, name)


def alerts(db, oid):
    return db.execute("SELECT * FROM alerts WHERE org_id=?", (oid,)).fetchall()


def test_codex_repro_new_org_with_matching_inventory_gets_alert(client, db):
    collect_as_fernwood(client, db)
    jun = new_org(client, db)
    client.post("/organization/inventory", data=AGENT)
    refresh(client)
    (alert,) = alerts(db, jun)
    rel = db.execute("SELECT match_state, priority FROM relevance WHERE org_id=?", (jun,)).fetchone()
    assert rel["match_state"] == "confirmed"
    assert client.get(f"/alerts/{alert['id']}").status_code == 200


def test_adding_inventory_alone_assesses_available_findings(client, db):
    collect_as_fernwood(client, db)
    jun = new_org(client, db)
    assert alerts(db, jun) == []  # no inventory yet -> no supported relationship
    client.post("/organization/inventory", data=AGENT)
    assert len(alerts(db, jun)) == 1


def test_enabling_a_source_assesses_findings_it_already_collected(client, db):
    collect_as_fernwood(client, db)
    jun = new_org(client, db)
    srcs = {r["key"]: r["id"] for r in db.execute("SELECT id, key FROM source_catalog")}
    for key in ("thehackernews", "csa"):
        client.post(f"/sources/{srcs[key]}/toggle")  # disable
    # Simulate an org that was never assessed for the finding (creation already assessed it once, and
    # disabling a source only stops future collection, so known findings stay known by design).
    db.execute("DELETE FROM relevance WHERE org_id=?", (jun,))
    db.execute("INSERT INTO inventory_items (org_id, name, product_key, version, version_status, criticality,"
               " capabilities, updated_at) VALUES (?, 'Storefront', 'php', '8.4.10', 'known', 'High', '[\"php\"]', 'now')",
               (jun,))
    db.commit()
    assert alerts(db, jun) == []
    client.post(f"/sources/{srcs['csa']}/toggle")  # re-enable
    assert len(alerts(db, jun)) == 1


def test_refresh_assesses_backlog_for_orgs_without_prior_relevance(client, db, app):
    collect_as_fernwood(client, db)
    jun = new_org(client, db)
    # Inventory inserted outside the app's routes: only the refresh can pick it up.
    db.execute("INSERT INTO inventory_items (org_id, name, product_key, version, version_status, criticality,"
               " capabilities, updated_at) VALUES (?, 'Storefront', 'php', '8.4.10', 'known', 'High', '[\"php\"]', 'now')",
               (jun,))
    db.execute("DELETE FROM relevance WHERE org_id=?", (jun,))
    db.commit()
    refresh(client)
    assert len(alerts(db, jun)) == 1


def test_new_org_completes_workflow_through_approved_plan(client, db):
    collect_as_fernwood(client, db)
    jun = new_org(client, db)
    client.post("/organization/inventory", data=AGENT)
    (alert,) = alerts(db, jun)
    client.post(f"/alerts/{alert['id']}/guide")
    guide = db.execute("SELECT id FROM guides WHERE alert_id=?", (alert["id"],)).fetchone()["id"]
    client.post(f"/guides/{guide}/plan")
    plan = db.execute("SELECT id FROM plans WHERE guide_id=?", (guide,)).fetchone()["id"]
    client.post(f"/plans/{plan}/submit")
    client.post(f"/plans/{plan}/approve", data={"confirm": "yes"})
    assert db.execute("SELECT status FROM plans WHERE id=?", (plan,)).fetchone()[0] == "approved"


def test_backlog_assessment_does_not_leak_fernwood_alerts(client, db):
    collect_as_fernwood(client, db)
    jun = new_org(client, db)
    client.post("/organization/inventory", data=AGENT)
    fern = org_id(db, FERNWOOD)
    fern_alert = alerts(db, fern)[0]["id"]
    assert client.get(f"/alerts/{fern_alert}").status_code == 404
    assert len(alerts(db, fern)) == 1
