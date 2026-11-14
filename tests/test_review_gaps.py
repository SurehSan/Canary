"""Coverage for gaps listed in documents/codex-review-report.md (focus items 2, 4, 6, 9, 10)."""
import http.server
import sqlite3
import threading
import time

import pytest

from canary import create_app
from canary.db import get_db
from canary.live import http_get, parse_rss
from tests.conftest import login, org_id, refresh
from tests.smtp_capture import CaptureServer
from tests.test_live import SAMPLE
from tests.test_notifications import make_app

FERNWOOD, PRAIRIE = "Fernwood Labs", "Prairie Valley Medical Center"


# ------------------------------------------------------------------ focus 2: cross-org route matrix
@pytest.fixture
def fern_records(client, db):
    fern = org_id(db, FERNWOOD)
    login(client, "wyatt", org=fern)
    refresh(client)
    alert = db.execute("SELECT id FROM alerts WHERE org_id=?", (fern,)).fetchone()["id"]
    client.post(f"/alerts/{alert}/guide")
    guide = db.execute("SELECT id FROM guides WHERE alert_id=?", (alert,)).fetchone()["id"]
    client.post(f"/guides/{guide}/plan")
    plan = db.execute("SELECT id FROM plans WHERE guide_id=?", (guide,)).fetchone()["id"]
    client.post("/notifications/test", data={"email": "nobody@else.example"})
    notif = db.execute("SELECT id FROM notifications WHERE org_id=?", (fern,)).fetchone()["id"]
    item = db.execute("SELECT id FROM source_items WHERE group_status='proposed'").fetchone()["id"]
    koewen = db.execute("SELECT id FROM users WHERE username='koewen'").fetchone()["id"]
    client.post("/logout")
    login(client, "priya", org=org_id(db, PRAIRIE))
    return dict(alert=alert, guide=guide, plan=plan, notif=notif, item=item, koewen=koewen)


ROUTES = [
    ("get", "/alerts/{alert}"), ("get", "/guides/{guide}"), ("get", "/plans/{plan}"),
    ("post", "/alerts/{alert}/assign"), ("post", "/alerts/{alert}/status"), ("post", "/alerts/{alert}/override"),
    ("post", "/alerts/{alert}/guide"), ("post", "/alerts/{alert}/grouping/{item}/confirm"),
    ("post", "/alerts/{alert}/grouping/{item}/undo"), ("post", "/guides/{guide}/answer"),
    ("post", "/guides/{guide}/steps/1/status"), ("post", "/guides/{guide}/steps/1/edit"),
    ("post", "/guides/{guide}/plan"), ("post", "/plans/{plan}/submit"), ("post", "/plans/{plan}/return"),
    ("post", "/plans/{plan}/approve"), ("post", "/plans/{plan}/archive"), ("post", "/plans/{plan}/edit"),
    ("post", "/notifications/{notif}/retry"), ("post", "/members/{koewen}/revoke"),
]


@pytest.mark.parametrize("method,template", ROUTES)
def test_other_org_admin_gets_404_on_every_id_route(client, db, fern_records, method, template):
    data = {"status": "under_investigation", "priority": "P4", "reason": "x", "answer": "Yes", "confirm": "yes",
            "assignee_id": 1, "title": "hijack", "action": "hijack"}
    url = template.format(**fern_records)
    resp = client.get(url) if method == "get" else client.post(url, data=data)
    assert resp.status_code == 404, url


def test_route_matrix_left_fernwood_records_unchanged(client, db, fern_records):
    for method, template in ROUTES:
        url = template.format(**fern_records)
        client.get(url) if method == "get" else client.post(url, data={"reason": "x", "confirm": "yes", "title": "hijack"})
    assert db.execute("SELECT status FROM alerts WHERE id=?", (fern_records["alert"],)).fetchone()[0] == "new"
    plan = db.execute("SELECT title, status FROM plans WHERE id=?", (fern_records["plan"],)).fetchone()
    assert (plan["title"], plan["status"]) == ("Malicious dependency via AI agent", "draft")
    assert db.execute("SELECT status FROM memberships WHERE user_id=?", (fern_records["koewen"],)).fetchone()[0] == "active"
    assert db.execute("SELECT COUNT(*) FROM findings").fetchone()[0] == 1


# ------------------------------------------------------------------ focus 4: retry/digest never bypass the allowlist
@pytest.fixture
def smtp():
    s = CaptureServer()
    yield s
    s.close()


def _fernwood_with_sureh(app, client, db, addr):
    fern = org_id(db, FERNWOOD)
    login(client, "wyatt", org=fern)
    sureh = db.execute("SELECT id FROM users WHERE username='sureh'").fetchone()["id"]
    client.post("/notifications/recipients", data={"user_id": sureh, "email": addr})
    refresh(client)
    return fern, db.execute("SELECT id FROM alerts WHERE org_id=?", (fern,)).fetchone()["id"]


def test_retry_of_rejected_message_still_never_connects(tmp_path, smtp):
    app = make_app(tmp_path, smtp)
    c = app.test_client()
    with app.app_context():
        db = get_db()
        _fernwood_with_sureh(app, c, db, "outsider@else.example")
        c.post("/notifications/process")
        n = db.execute("SELECT id FROM notifications").fetchone()["id"]
        c.post(f"/notifications/{n}/retry")
        row = db.execute("SELECT status, attempts FROM notifications WHERE id=?", (n,)).fetchone()
        assert tuple(row) == ("rejected", 2) and smtp.connections == 0


def test_digest_to_unlisted_address_never_connects(tmp_path, smtp):
    app = make_app(tmp_path, smtp)
    c = app.test_client()
    with app.app_context():
        db = get_db()
        _, alert = _fernwood_with_sureh(app, c, db, "outsider@else.example")
        c.post(f"/alerts/{alert}/override", data={"priority": "P3", "reason": "digest check"})
        c.post("/notifications/digest")
        statuses = [r[0] for r in db.execute("SELECT status FROM notifications WHERE cadence='digest'")]
        assert statuses and set(statuses) == {"rejected"} and smtp.connections == 0


def test_digest_batch_retry_updates_every_message_in_the_batch(tmp_path, smtp):
    app = make_app(tmp_path, smtp)
    c = app.test_client()
    with app.app_context():
        db = get_db()
        _, alert = _fernwood_with_sureh(app, c, db, "sureh-test@team.example")
        c.post("/notifications/process")
        c.post(f"/alerts/{alert}/override", data={"priority": "P3", "reason": "first"})
        c.post(f"/alerts/{alert}/override", data={"priority": "P3", "match_state": "industry_only", "reason": "second"})
        c.post("/notifications/simulate-failure")
        c.post("/notifications/digest")
        batch = db.execute("SELECT id, status, digest_batch FROM notifications WHERE cadence='digest'").fetchall()
        assert len(batch) == 2 and {r["status"] for r in batch} == {"failed"}
        assert len({r["digest_batch"] for r in batch}) == 1
        c.post("/notifications/simulate-failure")
        c.post(f"/notifications/{batch[0]['id']}/retry")
        after = db.execute("SELECT status, attempts FROM notifications WHERE cadence='digest'").fetchall()
        assert {tuple(r) for r in after} == {("sent", 2)}
        assert sum("Daily digest" in m["msg"]["Subject"] for m in smtp.messages) == 1


# ------------------------------------------------------------------ focus 9: plan lifecycle edges
def _plan_as_wyatt(client, db):
    fern = org_id(db, FERNWOOD)
    login(client, "wyatt", org=fern)
    refresh(client)
    alert = db.execute("SELECT id FROM alerts WHERE org_id=?", (fern,)).fetchone()["id"]
    client.post(f"/alerts/{alert}/guide")
    guide = db.execute("SELECT id FROM guides").fetchone()["id"]
    client.post(f"/guides/{guide}/plan")
    return db.execute("SELECT id FROM plans").fetchone()["id"]


def test_no_op_plan_edit_creates_no_version(client, db):
    plan = _plan_as_wyatt(client, db)
    client.post(f"/plans/{plan}/edit", data={})
    assert db.execute("SELECT version FROM plans WHERE id=?", (plan,)).fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM plan_versions WHERE plan_id=?", (plan,)).fetchone()[0] == 1


def test_archived_plan_cannot_be_edited(client, db):
    plan = _plan_as_wyatt(client, db)
    client.post(f"/plans/{plan}/submit")
    client.post(f"/plans/{plan}/approve", data={"confirm": "yes"})
    client.post(f"/plans/{plan}/archive")
    assert client.post(f"/plans/{plan}/edit", data={"title": "changed"}).status_code == 400
    assert db.execute("SELECT status FROM plans WHERE id=?", (plan,)).fetchone()[0] == "archived"


# ------------------------------------------------------------------ focus 6: hostile RSS
BILLION_LAUGHS = b"""<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol">
<!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
<!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
<!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
<!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">
<!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">
<!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">
<!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">
<!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">]>
<rss><channel><item><title>AI &lol9;</title><link>https://x.example/a</link></item></channel></rss>"""

EXTERNAL_ENTITY = b"""<?xml version="1.0"?><!DOCTYPE r [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<rss><channel><item><title>AI agent &xxe;</title><link>https://x.example/b</link></item></channel></rss>"""

UNSAFE_LINK = b"""<rss><channel>
<item><title>AI agent one</title><link>javascript:alert(1)</link></item>
<item><title>AI agent two</title><link>data:text/html,hi</link></item>
<item><title>AI agent three</title><link>https://ok.example/c</link></item></channel></rss>"""


def test_unsafe_link_schemes_are_dropped():
    assert [i["url"] for i in parse_rss(UNSAFE_LINK)] == ["https://ok.example/c"]


def _live_refresh(tmp_path, payload):
    app = create_app({"TESTING": True, "SECRET_KEY": "t", "DATABASE": str(tmp_path / "h.sqlite"),
                      "FIXED_NOW": "2026-11-14T15:00:00+00:00", "RETRY_SLEEP_SECONDS": 0, "START_SCHEDULER": False,
                      "SMTP_HOST": None, "EMAIL_ALLOWLIST": set(), "TEST_RECIPIENTS": {}, "LIVE_SOURCES": True,
                      "HTTP_GET": lambda url: payload})
    c = app.test_client()
    with app.app_context():
        db = get_db()
        login(c, "wyatt", org=org_id(db, FERNWOOD))
        started = time.monotonic()
        refresh(c)
        elapsed = time.monotonic() - started
        run = db.execute("SELECT outcome, error FROM collection_runs WHERE adapter='Live RSS'").fetchone()
        titles = [r[0] for r in db.execute("SELECT title FROM source_items")]
        return run, titles, elapsed, c.get("/sources").status_code


@pytest.mark.parametrize("payload", [BILLION_LAUGHS, EXTERNAL_ENTITY], ids=["entity-expansion", "external-entity"])
def test_hostile_feed_fails_safely(tmp_path, payload):
    run, titles, elapsed, status = _live_refresh(tmp_path, payload)
    assert run["outcome"] == "failed" and "ParseError" in run["error"]
    assert elapsed < 5 and status == 200
    assert not any("lollol" in t or "root:" in t for t in titles)


def test_http_get_caps_response_size():
    class Big(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"x" * 3_000_000)

        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Big)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        assert len(http_get(f"http://127.0.0.1:{srv.server_address[1]}/feed")) == 2_000_000
    finally:
        srv.shutdown()


# ------------------------------------------------------------------ focus 10: scheduler vs requests on one SQLite file
def test_slow_live_fetch_in_scheduler_does_not_lock_out_other_writers(tmp_path):
    def slow_get(url):
        time.sleep(1.5)
        return SAMPLE
    path = str(tmp_path / "c.sqlite")
    app = create_app({"TESTING": True, "SECRET_KEY": "t", "DATABASE": path, "RETRY_SLEEP_SECONDS": 0,
                      "START_SCHEDULER": False, "SMTP_HOST": None, "EMAIL_ALLOWLIST": set(), "TEST_RECIPIENTS": {},
                      "LIVE_SOURCES": True, "HTTP_GET": slow_get})

    def cycle():
        from canary.scheduler import run_cycle
        with app.app_context():
            run_cycle(get_db(), collect=True, digest=False)
    worker = threading.Thread(target=cycle)
    worker.start()
    time.sleep(0.6)  # the worker is now inside the slow live fetch
    other = sqlite3.connect(path, timeout=0.5)
    try:
        other.execute("INSERT INTO audit_events (actor_label, action, target_type, summary, created_at)"
                      " VALUES ('test', 'probe', 'none', 'concurrent write', 'now')")
        other.commit()
    finally:
        other.close()
        worker.join()
