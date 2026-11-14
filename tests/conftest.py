import pytest

from canary import create_app
from canary.db import get_db


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-only",
        "DATABASE": str(tmp_path / "canary-test.sqlite"),
        "FIXED_NOW": "2026-11-14T15:00:00+00:00",
        "RETRY_SLEEP_SECONDS": 0,
        "START_SCHEDULER": False,
        # Hermetic: never pick up a developer's real SMTP / live-source settings.
        "SMTP_HOST": None, "SMTP_PASSWORD": None, "EMAIL_ALLOWLIST": set(), "TEST_RECIPIENTS": {},
        "ALLOWLIST_DOMAINS": None, "PRESENTATION_MODE": False,
        "LIVE_SOURCES": False,
    })
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    with app.app_context():
        yield get_db()


def login(client, username, password="demo", org=None):
    resp = client.post("/login", data={"username": username, "password": password})
    if org is not None:
        client.post("/orgs/select", data={"org_id": org})
    return resp


def org_id(db, name):
    return db.execute("SELECT id FROM organizations WHERE name = ?", (name,)).fetchone()["id"]


def refresh(client):
    return client.post("/sources/refresh", follow_redirects=True)
