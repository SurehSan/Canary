"""Fixes for Codex review findings CDX-1 and CDX-2, plus the review's coverage gaps."""
import smtplib

import pytest

from canary.db import get_db
from tests.conftest import login, org_id, refresh

FERNWOOD, PRAIRIE = "Fernwood Labs", "Prairie Valley Medical Center"


def source(db, key):
    return db.execute("SELECT id FROM source_catalog WHERE key=?", (key,)).fetchone()["id"]


# ------------------------------------------------------------------ CDX-1
def test_cdx1_outage_simulation_in_one_org_does_not_affect_another(client, db):
    ghsa = source(db, "ghsa")
    login(client, "priya", org=org_id(db, PRAIRIE))
    client.post(f"/sources/{ghsa}/simulate-failure")
    prairie_page = None
    client.post("/logout")
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    fern_dash = client.get("/").data.decode()
    assert "Simulated outage" not in client.get("/sources").data.decode()
    assert "Failed" not in fern_dash, "Fernwood must not see Prairie Valley's simulated outage"
    client.post("/logout")
    login(client, "priya", org=org_id(db, PRAIRIE))
    prairie_page = client.get("/").data.decode()
    assert "Failed" in prairie_page, "Prairie Valley still sees its own simulated outage"
    assert "Simulated outage on (this organization only)" in client.get("/sources").data.decode()


def test_cdx1_simulated_outage_blocks_items_only_for_the_simulating_org(client, db):
    thn = source(db, "thehackernews")
    fern = org_id(db, FERNWOOD)
    login(client, "wyatt", org=fern)
    client.post(f"/sources/{thn}/simulate-failure")
    refresh(client)
    # THN is Fernwood-only, so nothing real is fetched for it; CSA still arrives.
    assert db.execute("SELECT COUNT(*) FROM source_items si JOIN source_catalog c ON c.id=si.source_id"
                      " WHERE c.key='thehackernews'").fetchone()[0] == 0
    run = db.execute("SELECT * FROM collection_runs WHERE source_id=? ORDER BY id DESC", (thn,)).fetchone()
    assert run["org_id"] == fern and run["outcome"] == "failed" and run["attempts"] == 3


def test_cdx1_shared_evidence_actions_disclose_cross_org_scope(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    refresh(client)
    alert = db.execute("SELECT id FROM alerts").fetchone()["id"]
    assert "affects every organization" in client.get(f"/alerts/{alert}").data.decode()
    assert "affects every organization" in client.get("/sources").data.decode()


# ------------------------------------------------------------------ CDX-2
SECRET = "SENTINEL-SECRET-123"


def test_cdx2_smtp_error_text_is_not_persisted_or_shown(tmp_path, monkeypatch):
    from tests.smtp_capture import CaptureServer
    from tests.test_notifications import make_app
    smtp = CaptureServer()
    try:
        app = make_app(tmp_path, smtp, SMTP_PASSWORD=SECRET)
        import canary.delivery as delivery

        def refuse(*_a, **_k):
            raise smtplib.SMTPAuthenticationError(535, f"5.7.8 bad credentials for {SECRET}".encode())
        monkeypatch.setattr(delivery, "_send_smtp", refuse)
        client = app.test_client()
        with app.app_context():
            db = get_db()
            login(client, "wyatt", org=org_id(db, FERNWOOD))
            sureh = db.execute("SELECT id FROM users WHERE username='sureh'").fetchone()["id"]
            client.post("/notifications/recipients", data={"user_id": sureh, "email": "sureh-test@team.example"})
            refresh(client)
            client.post("/notifications/process")
            n = db.execute("SELECT * FROM notifications").fetchone()
            assert n["status"] == "failed"
            assert "SMTPAuthenticationError" in n["error"] and "535" in n["error"]
            assert SECRET not in "\n".join(db.iterdump())
            for path in ("/notifications", "/audit"):
                assert SECRET not in client.get(path).data.decode()
    finally:
        smtp.close()


# ------------------------------------------------------------------ demo-step ordering (found in first local run)
def test_followup_step_is_refused_before_the_finding_is_collected(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    resp = client.post("/sources/followup")
    assert resp.status_code == 400
    assert "Refresh sources first" in resp.data.decode()
    assert db.execute("SELECT COUNT(*) FROM source_items").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM findings").fetchone()[0] == 0


def test_followup_button_is_disabled_until_refresh(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    page = client.get("/sources").data.decode()
    assert "Refresh sources first" in page
    refresh(client)
    client.post("/sources/followup")
    alert = db.execute("SELECT id FROM alerts WHERE org_id=?", (org_id(db, FERNWOOD),)).fetchone()["id"]
    items = db.execute("SELECT source_label, group_status FROM source_items WHERE finding_id="
                       "(SELECT finding_id FROM alerts WHERE id=?) ORDER BY id", (alert,)).fetchall()
    assert [i["group_status"] for i in items][0] == "primary" and items[0]["source_label"] == "PHP security announcements"
    assert items[-1]["source_label"] == "Additional evidence (follow-up report)"
