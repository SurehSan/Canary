"""Option B: Administrator-managed, per-organization email allowlist (CAN-REQ-009, 014, 015).

The .env allowlist stays authoritative and cannot be removed in the app; Administrators can add team-owned
addresses on permitted domains, with an explicit confirmation, and every change is audited."""
import pytest

from canary.db import get_db
from tests.conftest import login, org_id
from tests.smtp_capture import CaptureServer
from tests.test_notifications import SUREH_ADDR, make_app

FERNWOOD, PRAIRIE = "Fernwood Labs", "Prairie Valley Medical Center"
NEW_ADDR = "teammate@team.example"


@pytest.fixture
def smtp():
    s = CaptureServer()
    yield s
    s.close()


@pytest.fixture
def ctx(tmp_path, smtp):
    app = make_app(tmp_path, smtp, ALLOWLIST_DOMAINS={"team.example"})
    with app.app_context():
        yield app.test_client(), get_db(), smtp


def add(client, email=NEW_ADDR, confirm="yes"):
    data = {"email": email}
    if confirm:
        data["confirm"] = confirm
    return client.post("/notifications/allowlist", data=data)


def statuses(db, kind="test"):
    return [r[0] for r in db.execute("SELECT status FROM notifications WHERE kind=? ORDER BY id", (kind,))]


def test_admin_adds_team_address_and_it_can_receive(ctx):
    client, db, smtp = ctx
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    client.post("/notifications/test", data={"email": NEW_ADDR})
    assert statuses(db) == ["rejected"] and smtp.connections == 0
    add(client)
    page = client.get("/notifications").data.decode()
    assert NEW_ADDR in page and "Added in app by Wyatt" in page
    client.post("/notifications/test", data={"email": NEW_ADDR})
    assert statuses(db)[-1] == "sent" and smtp.messages[-1]["rcpts"] == [NEW_ADDR]
    ev = db.execute("SELECT * FROM audit_events WHERE action='notification.allowlist_added'").fetchone()
    assert NEW_ADDR in ev["summary"] and ev["actor_id"] is not None


def test_saved_test_address_shows_allowed_after_allowlisting(ctx):
    client, db, _ = ctx
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    koewen = db.execute("SELECT id FROM users WHERE username='koewen'").fetchone()["id"]
    client.post("/notifications/recipients", data={"user_id": koewen, "email": NEW_ADDR})
    assert "Not allowed" in client.get("/notifications").data.decode()
    add(client)
    assert "Not allowed" not in client.get("/notifications").data.decode()


def test_confirmation_is_required(ctx):
    client, db, _ = ctx
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    assert add(client, confirm=None).status_code == 400
    assert db.execute("SELECT COUNT(*) FROM email_allowlist").fetchone()[0] == 0


@pytest.mark.parametrize("email", ["someone@outside.example", "not-an-email", ""])
def test_addresses_off_permitted_domains_or_malformed_are_refused(ctx, email):
    client, db, smtp = ctx
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    assert add(client, email).status_code == 400
    assert db.execute("SELECT COUNT(*) FROM email_allowlist").fetchone()[0] == 0


def test_duplicate_or_env_address_is_refused(ctx):
    client, db, _ = ctx
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    add(client)
    assert add(client).status_code == 400
    assert add(client, SUREH_ADDR).status_code == 400  # already allowed by .env


def test_lead_cannot_change_the_allowlist(ctx):
    client, db, _ = ctx
    login(client, "sureh", org=org_id(db, FERNWOOD))
    assert add(client).status_code == 403


def test_allowlist_is_per_organization(ctx):
    client, db, smtp = ctx
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    add(client)
    client.post("/logout")
    login(client, "priya", org=org_id(db, PRAIRIE))
    assert NEW_ADDR not in client.get("/notifications").data.decode()
    before = smtp.connections
    client.post("/notifications/test", data={"email": NEW_ADDR})
    assert statuses(db)[-1] == "rejected" and smtp.connections == before
    entry = db.execute("SELECT id FROM email_allowlist").fetchone()["id"]
    assert client.post(f"/notifications/allowlist/{entry}/delete").status_code == 404


def test_removing_an_address_blocks_future_sends_and_is_audited(ctx):
    client, db, smtp = ctx
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    add(client)
    entry = db.execute("SELECT id FROM email_allowlist").fetchone()["id"]
    client.post(f"/notifications/allowlist/{entry}/delete")
    before = smtp.connections
    client.post("/notifications/test", data={"email": NEW_ADDR})
    assert statuses(db)[-1] == "rejected" and smtp.connections == before
    assert db.execute("SELECT 1 FROM audit_events WHERE action='notification.allowlist_removed'").fetchone()


def test_env_addresses_are_listed_but_not_removable(ctx):
    client, db, _ = ctx
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    page = client.get("/notifications").data.decode()
    assert SUREH_ADDR in page and "From local configuration (.env)" in page


def test_permitted_domains_default_to_the_env_allowlist_domains(tmp_path, smtp):
    app = make_app(tmp_path, smtp)  # no ALLOWLIST_DOMAINS: derived from team.example in EMAIL_ALLOWLIST
    with app.app_context():
        client, db = app.test_client(), get_db()
        login(client, "wyatt", org=org_id(db, FERNWOOD))
        assert add(client).status_code == 302
        assert add(client, "x@gmail.com").status_code == 400


def test_in_app_additions_are_disabled_without_any_configured_allowlist(tmp_path, smtp):
    app = make_app(tmp_path, smtp, EMAIL_ALLOWLIST=set())
    with app.app_context():
        client, db = app.test_client(), get_db()
        login(client, "wyatt", org=org_id(db, FERNWOOD))
        assert add(client).status_code == 400
        assert "in-app additions are off" in client.get("/notifications").data.decode().lower()
