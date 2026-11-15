"""Independent runtime checks required by documents/codex-verification-guide.md."""

from canary.db import get_db
from canary.scoring import match_state
from tests.conftest import login, org_id, refresh
from tests.smtp_capture import CaptureServer
from tests.test_notifications import make_app


FERNWOOD = "Fernwood Labs"
PRAIRIE = "Prairie Valley Medical Center"
SUREH_ADDR = "sureh-test@team.example"
# Updated by Claude for the PHP2Shell demo scenario (was the HalluSquatting "what happened" sentence).
ORIGINAL = ("The PHP project fixed two critical memory-safety flaws that let an unauthenticated attacker run code on "
            "servers running PHP 5.4 through 8.5.")
CORRECTED = "PHP fixed two critical RCE flaws; nothing yet shows this organization was attacked."


def test_fernwood_outage_does_not_fail_prairie_valley_or_ingest_ghsa(client, db):
    source_id = db.execute("SELECT id FROM source_catalog WHERE key='ghsa'").fetchone()["id"]
    fern = org_id(db, FERNWOOD)
    prairie = org_id(db, PRAIRIE)

    login(client, "wyatt", org=fern)
    assert client.post(f"/sources/{source_id}/simulate-failure").status_code == 302
    refresh(client)
    fern_run = db.execute(
        "SELECT * FROM collection_runs WHERE org_id=? AND source_id=? ORDER BY id DESC LIMIT 1",
        (fern, source_id),
    ).fetchone()
    assert (fern_run["outcome"], fern_run["attempts"], fern_run["new_items"]) == ("failed", 3, 0)
    # Updated by Claude for the PHP2Shell scenario: GHSA now has items, and Prairie Valley (not simulating) still
    # gets the shared fetch. Fernwood's own run failed; the items came only from the shared run (org_id NULL).
    shared = db.execute(
        "SELECT outcome, new_items FROM collection_runs WHERE org_id IS NULL AND source_id=? ORDER BY id DESC LIMIT 1",
        (source_id,)).fetchone()
    assert (shared["outcome"], shared["new_items"]) == ("success", 2)
    assert db.execute(
        "SELECT COUNT(*) FROM source_items si JOIN collection_runs r ON r.id=si.collection_run_id"
        " WHERE si.source_id=? AND r.org_id IS NOT NULL", (source_id,)).fetchone()[0] == 0

    client.post("/logout")
    login(client, "priya", org=prairie)
    prairie_page = client.get("/sources").data.decode()
    assert "GHSA" not in prairie_page or "Failed" not in prairie_page
    prairie_run = db.execute(
        "SELECT outcome FROM collection_runs WHERE org_id=? AND source_id=? ORDER BY id DESC LIMIT 1",
        (prairie, source_id),
    ).fetchone()
    assert prairie_run is None or prairie_run["outcome"] != "failed"


def test_unknown_version_exact_product_match_stays_possible():
    finding = {
        "affected_products": [{"product_key": "agentkit", "versions": ["1.0", "1.1"]}],
        "technique_tags": [],
        "industries": [],
    }
    inventory = [{"id": 42, "name": "AgentKit", "product_key": "agentkit", "version": None,
                  "capabilities": [], "criticality": "Critical"}]
    result = match_state(finding, inventory, "Software")
    assert result["state"] == "possible"
    assert result["state"] != "confirmed"


def test_corrected_analysis_statement_is_in_followup_update_email(tmp_path):
    smtp = CaptureServer()
    try:
        app = make_app(tmp_path, smtp)
        client = app.test_client()
        with app.app_context():
            db = get_db()
            fern = org_id(db, FERNWOOD)
            login(client, "wyatt", org=fern)
            sureh = db.execute("SELECT id FROM users WHERE username='sureh'").fetchone()["id"]
            client.post("/notifications/recipients", data={"user_id": sureh, "email": SUREH_ADDR})
            refresh(client)
            alert = db.execute("SELECT id FROM alerts WHERE org_id=?", (fern,)).fetchone()["id"]
            client.post("/notifications/process")
            assert len(smtp.messages) == 1

            correction = client.post(
                f"/alerts/{alert}/analysis/correct",
                data={"section": "what_happened", "original": ORIGINAL,
                      "corrected": CORRECTED, "reason": "Use the careful wording from the demo evidence review."},
            )
            assert correction.status_code == 302
            assert len(smtp.messages) == 1, "a correction alone should not send email"

            assert client.post("/sources/followup").status_code == 302
            client.post("/notifications/process")
            assert len(smtp.messages) == 2
            update = smtp.messages[-1]
            assert update["msg"]["Subject"].startswith("[CANARY DEMO - TEST] Update:")
            assert CORRECTED in update["msg"].get_content()
    finally:
        smtp.close()


def test_create_org_invite_revoke_reinvite_and_role_audit(client, db):
    client.post("/register", data={"username": "runtime_dana", "display_name": "Dana", "password": "pass1234"})
    assert client.post("/orgs/create", data={"name": "Runtime Check Co", "industry": "Software"}).status_code == 302
    org = org_id(db, "Runtime Check Co")
    koewen = db.execute("SELECT id FROM users WHERE username='koewen'").fetchone()["id"]

    assert client.post("/members/invite", data={"username": "koewen", "role": "lead"}).status_code == 302
    row = db.execute("SELECT role, status FROM memberships WHERE org_id=? AND user_id=?", (org, koewen)).fetchone()
    assert tuple(row) == ("lead", "active")

    assert client.post(f"/members/{koewen}/revoke").status_code == 302
    row = db.execute("SELECT role, status FROM memberships WHERE org_id=? AND user_id=?", (org, koewen)).fetchone()
    assert tuple(row) == ("lead", "revoked")

    assert client.post("/members/invite", data={"username": "koewen", "role": "admin"}).status_code == 302
    row = db.execute("SELECT role, status FROM memberships WHERE org_id=? AND user_id=?", (org, koewen)).fetchone()
    assert tuple(row) == ("admin", "active")
    audit = [r[0] for r in db.execute(
        "SELECT action FROM audit_events WHERE org_id=? ORDER BY id", (org,)
    )]
    assert "membership.invited" in audit
    assert "membership.revoked" in audit
    assert audit.count("membership.invited") == 2
