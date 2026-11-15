"""CAN-REQ-009 (+007 override): allowlisted test email, routing, cadence, failures, dedup, updates."""
import pytest

from canary import create_app
from canary.db import get_db
from tests.conftest import login, org_id, refresh
from tests.smtp_capture import CaptureServer

KOEWEN_ADDR = "koewen-test@team.example"  # Fernwood routes cybersecurity alerts to Koewen
WYATT_ADDR = "wyatt-test@team.example"
PASSWORD = "s3cret-smtp-pw-DO-NOT-LEAK"


@pytest.fixture
def smtp():
    server = CaptureServer()
    yield server
    server.close()


def make_app(tmp_path, smtp, **overrides):
    cfg = {
        "TESTING": True, "SECRET_KEY": "test-only", "DATABASE": str(tmp_path / "n.sqlite"),
        "FIXED_NOW": "2026-11-14T15:00:00+00:00", "RETRY_SLEEP_SECONDS": 0, "START_SCHEDULER": False,
        "SMTP_HOST": "127.0.0.1", "SMTP_PORT": smtp.port, "SMTP_STARTTLS": False, "SMTP_SSL": False,
        "SMTP_USERNAME": "canary", "SMTP_PASSWORD": PASSWORD, "MAIL_FROM": "canary-demo@team.example",
        "EMAIL_ALLOWLIST": {KOEWEN_ADDR, WYATT_ADDR}, "LIVE_SOURCES": False, "TEST_RECIPIENTS": {},
        "ALLOWLIST_DOMAINS": None, "PRESENTATION_MODE": False,
    }
    cfg.update(overrides)
    return create_app(cfg)


@pytest.fixture
def napp(tmp_path, smtp):
    return make_app(tmp_path, smtp)


@pytest.fixture
def nclient(napp):
    return napp.test_client()


@pytest.fixture
def ndb(napp):
    with napp.app_context():
        yield get_db()


def setup_fernwood(client, db, koewen_addr=KOEWEN_ADDR):
    fern = org_id(db, "Fernwood Labs")
    login(client, "wyatt", org=fern)
    for user, addr in (("koewen", koewen_addr), ("wyatt", WYATT_ADDR)):
        uid = db.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()["id"]
        client.post("/notifications/recipients", data={"user_id": uid, "email": addr})
    return fern


def rows(db, **where):
    sql = "SELECT * FROM notifications" + (" WHERE " + " AND ".join(f"{k}=?" for k in where) if where else "")
    return db.execute(sql + " ORDER BY id", tuple(where.values())).fetchall()


def alert_id(db, fern):
    return db.execute("SELECT id FROM alerts WHERE org_id=?", (fern,)).fetchone()["id"]


def test_p2_is_queued_then_sent_in_next_processing_cycle(nclient, ndb, smtp):
    setup_fernwood(nclient, ndb)
    refresh(nclient)
    (n,) = rows(ndb)
    assert (n["status"], n["cadence"], n["kind"]) == ("pending", "prompt", "new")
    assert smtp.messages == []
    nclient.post("/notifications/process")
    (n,) = rows(ndb)
    assert n["status"] == "sent" and n["recipient_email"] == KOEWEN_ADDR
    (m,) = smtp.messages
    assert m["rcpts"] == [KOEWEN_ADDR]
    assert m["msg"]["Subject"].startswith("[CANARY DEMO - TEST] P2")
    body = m["msg"].get_content()
    assert "TEST MODE" in body and "not evidence of an actual incident" in body
    assert "https://www.php.net/archive/2026.php#2026-10-21-5" in body


def test_only_routed_recipient_is_notified(nclient, ndb, smtp):
    setup_fernwood(nclient, ndb)
    refresh(nclient)
    users = {r["user_id"] for r in rows(ndb)}
    koewen = ndb.execute("SELECT id FROM users WHERE username='koewen'").fetchone()["id"]
    assert users == {koewen}


def test_non_allowlisted_recipient_is_rejected_before_any_smtp_connection(nclient, ndb, smtp):
    setup_fernwood(nclient, ndb, koewen_addr="outsider@elsewhere.example")
    refresh(nclient)
    nclient.post("/notifications/process")
    (n,) = rows(ndb)
    assert n["status"] == "rejected" and "allowlist" in n["error"]
    assert smtp.connections == 0 and smtp.messages == []


def test_member_without_test_address_is_blocked_not_rejected(nclient, ndb, smtp):
    fern = org_id(ndb, "Fernwood Labs")
    login(nclient, "wyatt", org=fern)
    refresh(nclient)
    nclient.post("/notifications/process")
    (n,) = rows(ndb)
    assert n["status"] == "blocked" and "No test address" in n["error"] and smtp.connections == 0


def test_missing_smtp_configuration_blocks_and_never_claims_sent(tmp_path, smtp):
    app = make_app(tmp_path, smtp, SMTP_HOST=None)
    client = app.test_client()
    with app.app_context():
        db = get_db()
        setup_fernwood(client, db)
        refresh(client)
        client.post("/notifications/process")
        (n,) = rows(db)
        assert n["status"] == "blocked" and "SMTP is not configured" in n["error"]
        assert n["sent_at"] is None
        page = client.get("/notifications").data.decode()
        assert "Blocked" in page and "not configured" in page


def test_empty_allowlist_rejects_everyone(tmp_path, smtp):
    app = make_app(tmp_path, smtp, EMAIL_ALLOWLIST=set())
    client = app.test_client()
    with app.app_context():
        db = get_db()
        setup_fernwood(client, db)
        refresh(client)
        client.post("/notifications/process")
        assert rows(db)[0]["status"] == "rejected" and smtp.connections == 0


def test_smtp_refusal_is_recorded_as_failed(nclient, ndb, smtp):
    smtp.fail_rcpt = True
    setup_fernwood(nclient, ndb)
    refresh(nclient)
    nclient.post("/notifications/process")
    (n,) = rows(ndb)
    assert n["status"] == "failed" and n["sent_at"] is None and n["simulated"] == 0
    assert "Failed" in nclient.get("/notifications").data.decode()


def test_simulated_failure_then_retry_succeeds(nclient, ndb, smtp):
    setup_fernwood(nclient, ndb)
    nclient.post("/notifications/simulate-failure")
    refresh(nclient)
    nclient.post("/notifications/process")
    (n,) = rows(ndb)
    assert n["status"] == "failed" and n["simulated"] == 1 and "Simulated" in n["error"]
    assert smtp.connections == 0
    nclient.post("/notifications/simulate-failure")
    nclient.post(f"/notifications/{n['id']}/retry")
    (n,) = rows(ndb)
    assert n["status"] == "sent" and n["attempts"] == 2
    assert len(smtp.messages) == 1


def test_unchanged_reassessment_is_suppressed(nclient, ndb, smtp):
    fern = setup_fernwood(nclient, ndb)
    refresh(nclient)
    nclient.post("/notifications/process")
    csa = ndb.execute("SELECT id FROM source_items WHERE group_status='proposed'").fetchone()["id"]
    nclient.post(f"/alerts/{alert_id(ndb, fern)}/grouping/{csa}/confirm")
    nclient.post("/notifications/process")
    assert [r["status"] for r in rows(ndb)] == ["sent", "suppressed"]
    assert len(smtp.messages) == 1


def test_followup_evidence_escalates_to_p1_and_sends_update_immediately(nclient, ndb, smtp):
    fern = setup_fernwood(nclient, ndb)
    refresh(nclient)
    nclient.post("/notifications/process")
    assert smtp.messages[-1]["msg"]["Subject"].startswith("[CANARY DEMO - TEST] P2")
    nclient.post("/sources/followup")  # Check Point confirms exploitation -> P1; no processing cycle needed
    assert ndb.execute("SELECT COUNT(*) FROM source_items WHERE finding_id="
                       "(SELECT finding_id FROM alerts WHERE id=?)", (alert_id(ndb, fern),)).fetchone()[0] == 5
    assert ndb.execute("SELECT has_update FROM alerts WHERE id=?", (alert_id(ndb, fern),)).fetchone()[0] == 1
    last = rows(ndb)[-1]
    assert (last["kind"], last["priority"], last["cadence"], last["status"]) == ("update", "P1", "immediate", "sent")
    assert smtp.messages[-1]["msg"]["Subject"].startswith("[CANARY DEMO - TEST] Update: P1")
    assert "priority P2->P1" in smtp.messages[-1]["msg"].get_content()


def test_override_requires_reason(nclient, ndb, smtp):
    fern = setup_fernwood(nclient, ndb)
    refresh(nclient)
    resp = nclient.post(f"/alerts/{alert_id(ndb, fern)}/override", data={"priority": "P3", "reason": " "})
    assert resp.status_code == 400


def test_override_to_p3_goes_to_digest_not_prompt_queue(nclient, ndb, smtp):
    fern = setup_fernwood(nclient, ndb)
    refresh(nclient)
    nclient.post("/notifications/process")
    nclient.post(f"/alerts/{alert_id(ndb, fern)}/override",
                 data={"priority": "P3", "reason": "Runtime agent cannot install packages (demo)"})
    rel = ndb.execute("SELECT * FROM relevance WHERE org_id=?", (fern,)).fetchone()
    assert (rel["priority"], rel["override_priority"]) == ("P2", "P3")
    nclient.post("/notifications/process")
    assert rows(ndb)[-1]["status"] == "pending" and rows(ndb)[-1]["cadence"] == "digest"
    nclient.post("/notifications/digest")
    assert rows(ndb)[-1]["status"] == "sent"
    assert "Daily digest" in smtp.messages[-1]["msg"]["Subject"]
    assert ndb.execute("SELECT 1 FROM audit_events WHERE action='relevance.overridden'").fetchone()


def test_override_to_p1_sends_immediately(nclient, ndb, smtp):
    fern = setup_fernwood(nclient, ndb)
    refresh(nclient)
    nclient.post(f"/alerts/{alert_id(ndb, fern)}/override", data={"priority": "P1", "reason": "Reviewer escalation"})
    p1 = [r for r in rows(ndb) if r["priority"] == "P1"]
    assert p1 and p1[0]["status"] == "sent" and p1[0]["cadence"] == "immediate"


def test_manual_test_message_to_unlisted_address_is_rejected(nclient, ndb, smtp):
    setup_fernwood(nclient, ndb)
    nclient.post("/notifications/test", data={"email": "random@person.example"})
    (n,) = rows(ndb)
    assert (n["kind"], n["status"]) == ("test", "rejected") and smtp.connections == 0
    nclient.post("/notifications/test", data={"email": KOEWEN_ADDR})
    assert rows(ndb)[-1]["status"] == "sent"


def test_lead_cannot_change_recipients_or_rules(nclient, ndb, smtp):
    fern = org_id(ndb, "Fernwood Labs")
    login(nclient, "sureh", org=fern)
    sureh = ndb.execute("SELECT id FROM users WHERE username='sureh'").fetchone()["id"]
    assert nclient.post("/notifications/recipients", data={"user_id": sureh, "email": KOEWEN_ADDR}).status_code == 403
    assert nclient.post("/notifications/rules", data={"user_id": sureh, "category": "cybersecurity"}).status_code == 403
    assert nclient.get("/notifications").status_code == 200


def test_smtp_password_never_appears_in_pages_or_database(nclient, ndb, smtp):
    fern = setup_fernwood(nclient, ndb)
    refresh(nclient)
    nclient.post("/notifications/process")
    for path in ("/notifications", "/audit", "/", f"/alerts/{alert_id(ndb, fern)}"):
        assert PASSWORD not in nclient.get(path).data.decode()
    dump = "\n".join(ndb.iterdump())
    assert PASSWORD not in dump


def test_queued_p2_is_superseded_when_p1_escalation_is_sent(nclient, ndb, smtp):
    """Found in the PHP2Shell walkthrough: a still-queued P2 email must not go out after the P1 update."""
    setup_fernwood(nclient, ndb)
    refresh(nclient)                      # P2 queued, not yet processed
    nclient.post("/sources/followup")     # escalates to P1 -> update sent immediately
    nclient.post("/notifications/process")
    statuses = [(r["priority"], r["kind"], r["status"]) for r in rows(ndb)]
    assert statuses == [("P2", "new", "suppressed"), ("P1", "update", "sent")]
    assert "Superseded" in rows(ndb)[0]["error"]
    assert [m["msg"]["Subject"][:34] for m in smtp.messages] == ["[CANARY DEMO - TEST] Update: P1 · "]
