"""CAN-REQ-001, 002, 015, 016: demo auth, roles, org isolation, revocation, labels."""
from tests.conftest import login, org_id, refresh

FERNWOOD = "Fernwood Labs"
PRAIRIE = "Prairie Valley Medical Center"


def test_wrong_password_is_rejected_generically(client):
    resp = login(client, "wyatt", "nope")
    assert b"Invalid username or password" in resp.data
    assert client.get("/").status_code == 302


def test_admin_sees_fernwood_workspace_with_demo_label(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    page = client.get("/").data.decode()
    assert "Demo data" in page and FERNWOOD in page


def test_inventory_shows_unknown_version_explicitly(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    page = client.get("/organization").data.decode()
    assert "Python runtime agent framework" in page
    assert "Unknown" in page
    assert "Sureh" in page and "Koewen" in page


def test_lead_cannot_change_source_settings(client, db):
    login(client, "sureh", org=org_id(db, FERNWOOD))
    src = db.execute("SELECT id FROM source_catalog WHERE key='thehackernews'").fetchone()["id"]
    assert client.post(f"/sources/{src}/toggle").status_code == 403
    assert client.post("/sources/refresh").status_code == 403


def test_lead_cannot_revoke_members(client, db):
    login(client, "sureh", org=org_id(db, FERNWOOD))
    koewen = db.execute("SELECT id FROM users WHERE username='koewen'").fetchone()["id"]
    assert client.post(f"/members/{koewen}/revoke").status_code == 403


def test_user_cannot_select_an_organization_they_do_not_belong_to(client, db):
    login(client, "sureh")
    resp = client.post("/orgs/select", data={"org_id": org_id(db, PRAIRIE)})
    assert resp.status_code == 404


def test_cross_org_alert_read_and_write_are_not_found(client, db, app):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    alert = db.execute("SELECT id FROM alerts WHERE org_id = ?", (org_id(db, FERNWOOD),)).fetchone()["id"]
    client.post("/logout")
    login(client, "priya", org=org_id(db, PRAIRIE))
    assert client.get(f"/alerts/{alert}").status_code == 404
    assert client.post(f"/alerts/{alert}/status", data={"status": "under_investigation"}).status_code == 404
    assert db.execute("SELECT status FROM alerts WHERE id=?", (alert,)).fetchone()["status"] == "new"


def test_revoked_member_loses_access(client, db, app):
    fern = org_id(db, FERNWOOD)
    koewen = db.execute("SELECT id FROM users WHERE username='koewen'").fetchone()["id"]
    other = app.test_client()
    login(other, "koewen", org=fern)
    assert other.get("/").status_code == 200
    login(client, "wyatt", org=fern)
    client.post(f"/members/{koewen}/revoke")
    assert other.get("/").status_code in (302, 404)
    assert other.get("/organization").status_code in (302, 404)
    audit = db.execute("SELECT action FROM audit_events WHERE org_id=? AND action='membership.revoked'", (fern,)).fetchone()
    assert audit is not None
