"""Presentation mode (CANARY_PRESENTATION_MODE=1): the web app looks like a real product, emails keep a clean
test tag, and truthfulness text (AI-generated draft, triage is not proof) stays. Off by default."""
import pytest

from canary import create_app
from canary.db import get_db
from canary.notify import build_digest, build_message
from tests.conftest import login, org_id, refresh
from tests.smtp_capture import CaptureServer
from tests.test_notifications import KOEWEN_ADDR, make_app
from tests.test_notify_unit import CTX

DEMO_WORDS = ("Demo data", "(fictional)", "Fictional", "Demo analysis", "demo template", "Demo step",
              "demo follow-up", "Offline fixture adapter", "demo cadence", "Demo accounts", "Test mode only",
              "CANARY DEMO")


@pytest.fixture
def papp(tmp_path):
    return create_app({"TESTING": True, "SECRET_KEY": "t", "DATABASE": str(tmp_path / "p.sqlite"),
                       "FIXED_NOW": "2026-11-14T15:00:00+00:00", "RETRY_SLEEP_SECONDS": 0, "START_SCHEDULER": False,
                       "SMTP_HOST": None, "EMAIL_ALLOWLIST": set(), "TEST_RECIPIENTS": {}, "LIVE_SOURCES": False,
                       "ALLOWLIST_DOMAINS": None, "PRESENTATION_MODE": True})


def walk(app):
    """Visit every main page as Wyatt and Sureh after a full flow; return {path: html}."""
    c = app.test_client()
    pages = {}
    with app.app_context():
        db = get_db()
        fern = org_id(db, "Fernwood Labs")
        pages["/login"] = c.get("/login").data.decode()
        login(c, "wyatt", org=fern)
        refresh(c)
        c.post("/sources/followup")
        alert = db.execute("SELECT id FROM alerts WHERE org_id=?", (fern,)).fetchone()["id"]
        c.post(f"/alerts/{alert}/guide")
        guide = db.execute("SELECT id FROM guides").fetchone()["id"]
        c.post(f"/guides/{guide}/plan")
        for path in ("/", "/organization", "/sources", "/notifications", "/questionnaire", "/audit", "/plans",
                     f"/alerts/{alert}", f"/guides/{guide}", "/plans/1", "/orgs"):
            pages[path] = c.get(path).data.decode()
        c.post("/logout")
        login(c, "sureh", org=fern)
        pages["lead:/sources"] = c.get("/sources").data.decode()
        pages["lead:/notifications"] = c.get("/notifications").data.decode()
    return pages


def test_presentation_pages_have_no_demo_wording(papp):
    for path, html in walk(papp).items():
        for word in DEMO_WORDS:
            assert word not in html, f"{path} still shows {word!r}"


def test_presentation_keeps_truthfulness_and_a_subtle_sample_marker(papp):
    pages = walk(papp)
    alert = next(v for k, v in pages.items() if k.startswith("/alerts/"))
    assert "AI-generated draft for human review" in alert and "not evidence of exposure" in alert
    assert "Sample workspace" in pages["/"]
    assert "does not execute" in pages["/plans/1"]


def test_presenter_tools_are_admin_only_and_still_work(papp):
    pages = walk(papp)
    assert "Presenter tools" in pages["/sources"] and "Presenter tools" in pages["/notifications"]
    assert "Presenter tools" not in pages["lead:/sources"] and "Presenter tools" not in pages["lead:/notifications"]
    assert "Simulate outage" in pages["/sources"] and "Simulate delivery failure" in pages["/notifications"]


def test_sign_in_page_hides_demo_credentials(papp):
    page = papp.test_client().get("/login").data.decode()
    assert "wyatt" not in page and "password <code>demo</code>" not in page
    assert "Sign in" in page


def test_default_mode_is_unchanged(client):
    page = client.get("/login").data.decode()
    assert "Demo data" in page and "Demo accounts (fictional)" in page


# ------------------------------------------------------------------ email
def test_presentation_email_has_clean_test_tag_and_footer():
    subject, body = build_message(CTX, presentation=True)
    assert subject.startswith("[Canary · Test] P2 · Possible match · ")
    assert "CANARY DEMO" not in subject + body and "TEST MODE" not in body
    assert "Test notification" in body and "not evidence of an actual incident" in body
    assert "Why this may matter to Fernwood Labs" in body


def test_presentation_digest_keeps_test_tag():
    subject, body = build_digest("Fernwood Labs", [], presentation=True)
    assert subject.startswith("[Canary · Test] Daily digest") and "Test notification" in body


def test_default_email_keeps_required_demo_label():
    subject, body = build_message(CTX)
    assert subject.startswith("[CANARY DEMO - TEST] ") and "TEST MODE" in body


def test_presentation_mode_emails_end_to_end(tmp_path):
    smtp = CaptureServer()
    try:
        app = make_app(tmp_path, smtp, PRESENTATION_MODE=True)
        c = app.test_client()
        with app.app_context():
            db = get_db()
            login(c, "wyatt", org=org_id(db, "Fernwood Labs"))
            koewen = db.execute("SELECT id FROM users WHERE username='koewen'").fetchone()["id"]
            c.post("/notifications/recipients", data={"user_id": koewen, "email": KOEWEN_ADDR})
            refresh(c)
            c.post("/notifications/process")
            c.post("/notifications/test", data={"email": KOEWEN_ADDR})
        subjects = [m["msg"]["Subject"] for m in smtp.messages]
        assert subjects[0].startswith("[Canary · Test] P2") and subjects[1].startswith("[Canary · Test] Delivery check")
    finally:
        smtp.close()
